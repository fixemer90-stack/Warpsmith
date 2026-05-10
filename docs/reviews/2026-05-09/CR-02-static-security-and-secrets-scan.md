---
title: "CR-02 — Static security and secrets scan"
status: request-changes
review_task: CR-02
date: 2026-05-09
source: ../../requirements/code-review/cr-02-static-security-and-secrets-scan.md
---

# CR-02 — Static security and secrets scan

## Verdict

**REQUEST CHANGES / SECURITY FIXES REQUIRED**

Static security scan found two critical issues that must be fixed before production/release: a credential-like file is tracked in git, and JWT signing has a hardcoded default fallback. Additional important issues were found around OAuth token storage/CSRF state, unsafe pickle cache loading, CSP disabled, Stripe webhook stub behavior, and PII/logging exposure.

No secret values were read or printed in this review. Credential-like files were detected by filename/tracking metadata only.

## Executive summary

Scope:

- Repository text scan excluding `.git`, `.venv`, caches, build artifacts.
- Backend/web AST scan for dangerous Python calls.
- Targeted review of auth, OAuth, billing webhook, security headers, logging, loader cache.

Static scan inventory:

```text
SCANNED_TEXT_FILES 725
SECRET_KEYWORD_HITS 339
DANGER_PATTERN_HITS 4
DANGER_BY_KIND {'pickle_load': 2, 'shell_true': 2}
DANGER_BY_AREA {'production': 1, 'doc_or_test': 3}
SECRET_BY_AREA {'credential_file': 1, 'doc_or_test': 184, 'production': 154}
AST_FINDINGS 1
```

AST-confirmed dangerous production call:

```text
backend/loader/registry.py:199 pickle.load
```

Tracked credential-like file metadata:

```text
.test-credentials exists True
size_bytes 482
git ls-files: tracked
working tree status: modified
```

The file content was not read.

## Critical findings

### Critical 1 — `.test-credentials` is tracked by git

Evidence:

```text
git ls-files --stage -- .test-credentials
100644 <hash> 0 .test-credentials

git status --short -- .test-credentials
 M .test-credentials
```

Additional metadata:

```text
exists True
size_bytes 482
```

The file is listed in `.gitignore`, but it is already tracked, so ignore rules do not protect it.

Why this is critical:

- Filename indicates local credentials.
- File is tracked in git and modified in working tree.
- Even if current contents are test-only, history may already contain sensitive values.

Required fix:

1. Do not print or inspect the values in chat/logs.
2. Rotate any credentials that may have been stored there.
3. Remove from index while keeping local file if needed:
   ```bash
   git rm --cached .test-credentials
   ```
4. Keep `.test-credentials` in `.gitignore`.
5. If real secrets were ever committed, rewrite repository history or treat them as compromised.
6. Add `.test-credentials.example` with placeholder values if tests need a template.

### Critical 2 — JWT signing secret has a hardcoded production fallback

Evidence:

```text
backend/auth/__init__.py:26
SECRET_KEY = os.getenv("JWT_SECRET", "change-me-in-production-2026")
```

Why this is critical:

- If production starts without `JWT_SECRET`, all JWTs use a known repository value.
- Anyone with source access can forge auth tokens.
- The file docstring says auth is production-ready, so the fallback is especially risky.

Required fix:

- In production/hosting mode, fail startup when `JWT_SECRET` is missing or equal to the default.
- Use a generated high-entropy secret in local development only.
- Add test coverage for production startup refusing default/missing JWT secret.

Suggested implementation pattern:

```python
_DEFAULT_DEV_JWT_SECRET = "change-me-in-production-2026"
SECRET_KEY = os.getenv("JWT_SECRET", _DEFAULT_DEV_JWT_SECRET)
if os.getenv("HOSTING", "").lower() in {"true", "1", "yes"} and SECRET_KEY == _DEFAULT_DEV_JWT_SECRET:
    raise RuntimeError("JWT_SECRET must be set in production")
```

## Important findings

### Important 1 — OAuth access tokens are stored plaintext in SQLite

Evidence:

```text
backend/auth/providers/routes.py:112-115
INSERT OR IGNORE INTO oauth_accounts (..., access_token) VALUES (?, ?, ?, ?)
(user.id, provider, user_info.sub, access_token)
```

Why this matters:

- OAuth access tokens are bearer credentials.
- DB compromise gives direct provider access for token lifetime.
- Current code does not appear to use stored access tokens after linking.

Required fix:

- Do not store access tokens unless refresh/use is required.
- If storage is required, encrypt at rest and store expiry/scope metadata.
- Prefer storing only provider identity linkage: `provider`, `provider_user_id`, `user_id`.

### Important 2 — OAuth CSRF state check is conditional and SessionMiddleware is not visible in `main.py`

Evidence:

```text
backend/auth/providers/routes.py:36-38
state = secrets.token_urlsafe(32)
request.session["oauth_state"] = state

backend/auth/providers/routes.py:56-58
saved_state = request.session.get("oauth_state", "")
if saved_state and state != saved_state:
    raise HTTPException(400, "State mismatch — possible CSRF")
```

`main.py` does not show `SessionMiddleware` registration.

Why this matters:

- If session support is absent, OAuth flow can fail at runtime.
- If saved state is missing/empty, the check is bypassed because it only rejects when `saved_state` is truthy.
- Correct CSRF behavior should require state presence and equality.

Required fix:

- Add Starlette `SessionMiddleware` with a production-safe secret or store OAuth state elsewhere.
- Change logic to reject missing state and mismatch:
  ```python
  if not saved_state or not secrets.compare_digest(saved_state, state):
      raise HTTPException(400, "State mismatch — possible CSRF")
  ```

### Important 3 — Wiki registry uses unsafe `pickle.load` on cache file

Evidence:

```text
backend/loader/registry.py:59
self.cache_path = Path.home() / ".cache" / "wiki_registry.pkl"

backend/loader/registry.py:199
data = pickle.load(cache_file)
```

Why this matters:

- Loading pickle is code execution if an attacker can write the cache file.
- The cache is under the user home, not inside a strictly controlled repo path.
- Production container/user permissions may reduce risk, but this remains unsafe deserialization.

Required fix:

- Replace pickle cache with JSON/msgpack or another safe format.
- If pickle remains temporarily, include explicit risk comment and restrict file permissions/location.
- Consider disabling cache in hosted mode until safe serialization exists.

### Important 4 — CSP middleware is disabled

Evidence:

```text
main.py:99-101
app.add_middleware(SecurityHeadersMiddleware)
# app.add_middleware(CSPMiddleware)  # отключено для локальной разработки
```

Why this matters:

- `SecurityHeadersMiddleware` does not add `Content-Security-Policy`.
- Frontend uses CDN scripts and inline Alpine/Tailwind patterns, so CSP needs careful tuning, but having it fully disabled weakens XSS defense.

Required fix:

- Enable CSP in production at minimum.
- Keep local/dev override if needed.
- Add a test that production responses include `Content-Security-Policy`.

### Important 5 — Stripe webhook route is a public stub that accepts requests without signature verification

Evidence:

```text
backend/billing/webhooks.py:9-20
@router.post("/webhooks/stripe")
async def stripe_webhook(request: Request):
    # TODO: stripe.Webhook.construct_event(payload, sig_header, WEBHOOK_SECRET)
    return JSONResponse({"status": "ok", "mode": "stub"})
```

Why this matters:

- Current route does not update state, so direct financial impact is limited today.
- But it returns success for unauthenticated webhook calls and may mask missing implementation in production.
- When subscription updates are added, this becomes critical if left unchanged.

Required fix:

- In production, reject webhook calls unless signature verification is configured.
- Return non-2xx for unimplemented production webhook mode.
- Add tests for invalid/missing Stripe signature.

### Important 6 — Sentry is configured to send default PII and logs partial DSN

Evidence:

```text
backend/logging_setup.py:94-96
send_default_pii=True
logger.info("Sentry initialized", dsn_short=dsn[:30] + "...")
```

Why this matters:

- `send_default_pii=True` can send IPs/headers and potentially user metadata to Sentry.
- Logging partial DSN is not usually as severe as logging API secrets, but it is avoidable.

Required fix:

- Decide explicitly whether PII capture is required; default should usually be `False` unless policy says otherwise.
- Do not log DSN fragments; log only `sentry_enabled=True` and environment.

### Important 7 — Public `/sentry-debug` endpoint is always registered

Evidence:

```text
main.py:142-145
@app.get("/sentry-debug")
async def trigger_error():
    division_by_zero = 1 / 0
```

Why this matters:

- Public endpoint intentionally raises an exception.
- It can be used to spam error monitoring and logs.
- It should not be exposed in production without an admin gate or feature flag.

Required fix:

- Register this route only in non-production or behind an explicit debug env flag.
- Add test that production app does not expose `/sentry-debug`.

## Suggestions

### Suggestion 1 — OAuth provider errors may expose upstream response bodies

Evidence:

```text
backend/auth/providers/google.py:64
msg = f"Token exchange failed: {resp.text}"

backend/auth/providers/vk.py:63-68
msg = f"Token exchange failed: {resp.text}"
msg = f"VK API error: {data['error']}"
```

These are raised as `OAuthError` and may surface to request handlers/logs. Sanitize upstream response bodies before returning/logging.

### Suggestion 2 — Password minimum length is low

Evidence:

```text
backend/auth/__init__.py:59-63
if len(password) < 6:
```

Current SRS also says 6 characters, so this is not a spec violation. For commercialization, consider 8+ minimum, breach-password checks, and rate limiting on login attempts.

### Suggestion 3 — `.test-credentials` working tree mode appears broad under WSL

Metadata scan showed working tree permissions as broad on WSL. Git records mode `100644`, but local permission hygiene should still be tightened for credential files where possible.

### Suggestion 4 — Add a dedicated security scan script

Current scan was ad-hoc. Add a repo-local script or CI job that checks:

- tracked credential filenames
- default secrets in production config
- `pickle.load`, `eval`, `exec`, `os.system`, `shell=True`
- SQL f-string/format execution
- webhook signature enforcement

## False positives / non-issues from static scan

### False Positive 1 — GitHub Actions `secrets.*` references

Examples:

```text
.github/workflows/ci.yml: token/password fields reference GitHub Actions secrets context
.github/workflows/deploy.yml: RAILWAY_TOKEN / DOKKU secrets context
```

These are not hardcoded secrets in the repository.

### False Positive 2 — Documentation mentions of JWT/Stripe/password/token

Many hits are documentation, roadmap, or requirements text. They are not secret values.

### False Positive 3 — Dependency names containing `PyJWT[crypto]`

`pyproject.toml`, `requirements.txt`, and `uv.lock` include package names and hashes. These are not application secrets.

### False Positive 4 — `shell=True` hits in CR plan text

The only `shell=True` hits were review-plan instructions describing what to scan for, not executable code.

### False Positive 5 — SQL scan found no AST-confirmed string interpolation in production execute calls

The AST scan found no f-string, `%`, or `.format()` SQL execution patterns in backend/web Python code.

## Five-axis review notes

### Correctness

- Static scan completed across 725 text files.
- AST scan confirmed no `eval`, `exec`, `os.system`, `shell=True`, or SQL interpolation calls in backend/web Python code.
- One production unsafe deserialization call exists: `pickle.load`.

### Readability / simplicity

- Security-sensitive defaults are easy to find, but current code comments overstate readiness in auth and billing areas.
- Stub/prod boundaries should be explicit in code, not only in comments.

### Architecture

- Auth, OAuth, and billing are spread across reasonable modules, but production safety should be enforced at startup/config boundary.
- Loader cache serialization is an architectural risk because a speed optimization creates an RCE class.

### Security

- Two critical issues require action before production/release.
- Important issues should be fixed or explicitly accepted as debt before CR-24.

### Performance

- Pickle cache exists for performance, but safe serialization should replace it.
- Security fixes for JWT/CSP/webhook should not materially affect performance.

## What is done well

- SQL usage inspected so far is parameterized in reviewed auth/OAuth/database code paths.
- Request logging records method/path/status/duration and does not log full cookies, Authorization headers, or request bodies.
- `.gitignore` already includes `.test-credentials`; the remaining issue is that it was tracked before/while ignored.
- Security headers include `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy`, and HTTPS-only HSTS.

## Verification story

Commands/tools used:

- Read CR-02 artifact and code-review index.
- Read `backend/auth/__init__.py`.
- Read `backend/auth/providers/routes.py`.
- Read `backend/auth/providers/google.py`.
- Read `backend/auth/providers/vk.py`.
- Read `backend/billing/webhooks.py`.
- Read `backend/loader/registry.py`.
- Read `backend/logging_setup.py`.
- Read `backend/security/headers.py`.
- Read `main.py`.
- Read `.gitignore`.
- Ran redacted repository text scan.
- Ran Python AST scan for dangerous calls.
- Checked `.test-credentials` git tracking metadata without reading file contents.
- Attempted `uv run bandit -q -r backend web main.py`; tool is not installed in current environment.

Bandit availability check:

```text
error: Failed to spawn: `bandit`
Caused by: No such file or directory
```

## Completion

- Completed at: `2026-05-09`
- Verdict: `REQUEST CHANGES / SECURITY FIXES REQUIRED`
- Critical: `2`
- Important: `7`
- Suggestions: `4`
- False positives: `5`
