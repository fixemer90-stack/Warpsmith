---
title: "CR-03 — Auth and session review"
status: request-changes
review_task: CR-03
date: 2026-05-09
source: ../../requirements/code-review/cr-03-auth-and-session-review.md
---

# CR-03 — Auth and session review

## Verdict

**REQUEST CHANGES / AUTH SESSION FIXES REQUIRED**

Registration/login basics work and passwords are bcrypt-hashed, but the auth/session layer is not production-ready. OAuth is currently non-functional in the app route registration path, OAuth CSRF/session handling is incomplete, JWT production secret handling is still a blocker from CR-02, and there are no dedicated auth tests.

## Scope reviewed

- `backend/auth/__init__.py`
- `web/routes/auth.py`
- `backend/auth/providers/base.py`
- `backend/auth/providers/routes.py`
- `backend/auth/providers/google.py`
- `backend/auth/providers/vk.py`
- `backend/db/database.py`
- `main.py`
- test suite inventory for auth-specific tests

## Tests / verification

Targeted tests run:

```text
uv run python -m pytest tests/test_rosters.py tests/test_replay.py -q
33 passed, 33 warnings in 6.18s
```

Broader related test run:

```text
uv run python -m pytest tests/test_rosters.py tests/test_generate_roster.py tests/test_replay.py -q
41 passed, 33 warnings in 6.09s
```

Auth smoke verification with `TestClient`:

```text
HASH_BCRYPT True True False
JWT_DECODE_USER 123
OAUTH_LOGIN_STATUS 400
OAUTH_LOGIN_BODY_PREFIX {"detail":"[google] Unknown OAuth provider: google"}
REGISTER 302 True set-cookie present
LOGIN 302 True set-cookie present
LOGOUT 302 token=""; Max-Age=0; Path=/; SameSite=lax; Secure
```

No dedicated `tests/test_auth*.py` files exist.

## Critical findings

### Critical 1 — OAuth providers are not registered, so `/auth/google/login` is non-functional

Evidence:

```text
backend/auth/providers/base.py
PROVIDER_REGISTRY = {}
providers self-register only when their modules are imported
```

`backend/auth/providers/__init__.py` is empty and `main.py` only imports `backend.auth.providers.routes`, not `google.py` or `vk.py`.

Runtime evidence:

```text
GET /auth/google/login -> 400
{"detail":"[google] Unknown OAuth provider: google"}
```

Impact:

- OAuth login advertised by docs/UI cannot work.
- Account-linking flow is unreachable.
- Any production plan relying on Google/VK auth will fail.

Required fix:

- Import provider modules during provider package initialization or inside route startup:
  - `from backend.auth.providers import google, vk` in `backend/auth/providers/__init__.py`, or
  - explicit import in `routes.py` before `get_provider` is called.
- Add tests for `/auth/providers`, `/auth/google/login`, and callback state failure paths.

## Important findings

### Important 1 — OAuth CSRF state validation is incomplete and depends on missing session setup

Evidence:

```text
backend/auth/providers/routes.py:36-38
request.session["oauth_state"] = state

backend/auth/providers/routes.py:56-58
saved_state = request.session.get("oauth_state", "")
if saved_state and state != saved_state:
    raise HTTPException(400, "State mismatch — possible CSRF")
```

`main.py` does not register Starlette `SessionMiddleware`.

Impact:

- Once providers are registered, login/callback will likely fail because `request.session` requires session middleware.
- The callback check permits missing/empty `saved_state` because it only rejects mismatch when `saved_state` is truthy.

Required fix:

- Register `SessionMiddleware` with production-safe secret.
- Reject missing state and compare with `secrets.compare_digest`:
  ```python
  if not saved_state or not secrets.compare_digest(saved_state, state):
      raise HTTPException(400, "State mismatch — possible CSRF")
  ```

### Important 2 — JWT production secret fallback remains a release blocker

Evidence:

```text
backend/auth/__init__.py:26
SECRET_KEY = os.getenv("JWT_SECRET", "change-me-in-production-2026")
```

This is already CR-02 Critical 2. It remains directly relevant to CR-03 because every auth cookie/JWT depends on this key.

Required fix:

- Fail startup in production if `JWT_SECRET` is missing/default.
- Add tests for production config failure.

### Important 3 — No dedicated auth tests exist

Evidence:

```text
search tests/*auth* -> 0 files
```

Existing roster tests indirectly cover registration cookies, but there is no direct coverage for:

- register success/failure
- duplicate email
- login success/failure
- logout cookie deletion
- `/auth/me` and `/api/me`
- JWT expiry/invalid token
- Secure/HttpOnly/SameSite cookie flags
- OAuth provider registry and callback state checks

Required fix:

- Add `tests/test_auth.py` with direct auth/session coverage.

### Important 4 — Login/register forms are POST endpoints without explicit route-level rate limits

Evidence:

- `main.py` sets a SlowAPI default limiter.
- Auth routes themselves have no explicit `@limiter.limit(...)` decorators.

Impact:

- Depending on SlowAPI behavior/config, auth brute-force protection may be weaker than intended.
- Commercial deployment needs explicit login/register throttling and lockout/abuse strategy.

Required fix:

- Add explicit conservative limits to `/auth/login` and `/auth/register`.
- Add tests for rate-limit headers/status if feasible.

### Important 5 — OAuth access token plaintext storage remains unresolved

Evidence:

```text
backend/auth/providers/routes.py:112-115
INSERT OR IGNORE INTO oauth_accounts (..., access_token) VALUES (?, ?, ?, ?)
```

This is already CR-02 Important 1. In CR-03 it blocks a clean auth/session approval because OAuth account linking stores bearer credentials without encryption or clear need.

Required fix:

- Store only provider identity linkage unless token reuse is required.
- If storage is required, encrypt at rest and store expiry/scope metadata.

## Suggestions

### Suggestion 1 — Password policy is minimal

Evidence:

```text
backend/auth/__init__.py:59-63
minimum length = 6
```

This matches current SRS, so it is not a spec violation. For commercialization, consider 8+ characters, breach-list checks, and stronger login throttling.

### Suggestion 2 — Use timezone-aware UTC datetimes for JWT claims

Test warnings:

```text
DeprecationWarning: datetime.datetime.utcnow() is deprecated
backend/auth/__init__.py:76-77
```

Use `datetime.now(datetime.UTC)` for `exp`/`iat`.

### Suggestion 3 — Duplicate email message leaks account existence

Evidence:

```text
This email is already registered — please log in instead
```

This may be acceptable UX, but for public production it enables account enumeration. Consider generic messaging or throttling.

## Five-axis review notes

### Correctness

- bcrypt hash/verify works.
- register/login create JWT cookie and redirect.
- logout emits a deletion cookie.
- OAuth route is currently broken because provider registry is empty.

### Readability / simplicity

- Auth helpers are compact and readable.
- The OAuth self-registration pattern is fragile because provider imports are implicit and currently missing.

### Architecture

- Auth core, auth routes, and provider routes are separated reasonably.
- Session state is used without app-level session middleware; this is a boundary/config architecture bug.

### Security

- JWT default secret, missing OAuth state hardening, and plaintext token storage prevent approval.
- Passwords are bcrypt-hashed and not stored plaintext.

### Performance

- bcrypt cost is default and acceptable for now.
- No obvious performance blocker in auth flow, but brute-force throttling must be explicit.

## What is done well

- Password hashing uses bcrypt with generated salts.
- JWT cookie is HttpOnly and SameSite=Lax.
- Production mode sets Secure cookies via `HOSTING` flag for login/register.
- Invalid login uses generic `Invalid email or password`.
- SQL in reviewed auth paths is parameterized.

## Completion

- Completed at: `2026-05-09`
- Verdict: `REQUEST CHANGES / AUTH SESSION FIXES REQUIRED`
- Critical: `1`
- Important: `5`
- Suggestions: `3`
