---
title: "CR-20 — Deployment, config and production readiness review"
status: request-changes
date: 2026-05-10
review: CR-20
scope:
  - Dockerfile
  - .dockerignore
  - docker-compose.yml
  - railway.json
  - Procfile
  - .env.example
  - .github/workflows/
  - main.py
  - backend/security/
  - backend/logging_setup.py
  - backend/auth/__init__.py
  - backend/db/database.py
  - deployment/security/rate-limit/logging tests
verdict: request-changes
critical: 2
important: 7
suggestions: 1
---

# CR-20 — Deployment, config and production readiness review

## Verdict

Request Changes.

The Railway/Docker happy path is partly aligned with the current Warpsmith deployment notes, and focused deployment/security tests pass. However, production readiness is blocked by a data-loss migration, an unsafe JWT fallback secret, stale CI/deploy branch wiring, disabled CSP, a public crash endpoint, incomplete error correlation, and production defaults that are not safe for rate limiting/privacy.

## Summary

- Critical: 2
- Important: 7
- Suggestions: 1
- Source-code changes made by this review: none
- Review/tracker docs updated: yes

## Scope reviewed

- `Dockerfile`
- `.dockerignore`
- `docker-compose.yml`
- `railway.json`
- `Procfile`
- `.env.example`
- `.github/workflows/ci.yml`
- `.github/workflows/deploy.yml`
- `main.py`
- `backend/security/headers.py`
- `backend/logging_setup.py`
- `backend/auth/__init__.py`
- `backend/db/database.py`
- `tests/test_docker.py`
- `tests/test_security_headers.py`
- `tests/test_rate_limit.py`
- `tests/test_logging.py`

## Findings

### CR-20-C1 — Critical — App startup migration deletes all replay data

Evidence:
- `backend/db/database.py:118-130` runs `DROP TABLE IF EXISTS replays;` inside `Database.migrate()`.
- `main.py:119-120` calls `db.migrate()` during app creation/startup.
- Probe with an isolated temp DB: after inserting one replay, a second `migrate()` changed replay count from `1` to `0`.

Problem:
Every production restart/deploy calls migration and drops the `replays` table. This destroys historical simulations and makes production persistence unreliable.

Impact:
Data loss on deploy/restart. This violates the commercial product expectation that users can return to saved simulation/replay history.

Recommendation:
Remove destructive DDL from startup migration. Replace with non-destructive `CREATE TABLE IF NOT EXISTS` plus explicit schema migrations. If replay schema must change, migrate/transform rows or run a one-time operator-approved migration with backup.

### CR-20-C2 — Critical — JWT has a hardcoded production fallback secret

Evidence:
- `backend/auth/__init__.py:26` defaults `JWT_SECRET` to a fixed placeholder value.
- `.env.example:8-10` documents the same placeholder pattern for copy/paste setup.

Problem:
If production starts without a real `JWT_SECRET`, or if `.env.example` is copied unchanged, all JWTs are signed with a known value.

Impact:
Authentication can be forged in any deployment using the fallback. This is a production security blocker.

Recommendation:
Fail fast in production when `JWT_SECRET` is missing or equals the placeholder. Generate a strong secret for local examples but do not keep a valid fallback in application code. Add a startup/config test for `HOSTING=true` + missing/placeholder secret.

### CR-20-I1 — Important — CI/deploy branch wiring is inconsistent and can skip production deployment

Evidence:
- `.github/workflows/ci.yml:4-7` triggers pushes/PRs for `master`, `feat/*`, `fix/*`, `0.*`, and PRs to `master`.
- `.github/workflows/ci.yml:69-73` Docker build runs only on `refs/heads/main`.
- `.github/workflows/deploy.yml:4-8` waits for CI on branch `main`.
- Git branch probe: current branch is `feat/0.7.7`; `origin/HEAD -> origin/master`; no `main` branch is listed.

Problem:
The test/lint workflow is configured around `master`, but Docker build and deploy are configured around `main`.

Impact:
Merges to the actual default branch can pass CI without Docker build/deploy, or deploy workflow may never run.

Recommendation:
Pick one canonical protected branch (`master` or `main`) and align all workflow triggers, Docker build conditions, deploy workflow filters, and repository branch settings.

### CR-20-I2 — Important — Content-Security-Policy is implemented but disabled

Evidence:
- `backend/security/headers.py:12-23` defines `CSP_POLICY`.
- `backend/security/headers.py:46-52` defines `CSPMiddleware`.
- `main.py:99-101` installs only `SecurityHeadersMiddleware`; `CSPMiddleware` is commented out.
- Runtime/browser probes: `/`, `/health`, and `/api/health` all returned no `Content-Security-Policy` header.

Problem:
The app advertises a CSP implementation but does not apply it.

Impact:
Production loses a key browser-side defense against XSS/script injection. This matters because the app uses rich templates and third-party CDN scripts.

Recommendation:
Enable CSP at least in `HOSTING=true`, tune allowed script/style sources for Alpine/Tailwind/HTMX as needed, and add tests that production responses include a CSP header.

### CR-20-I3 — Important — Public `/sentry-debug` endpoint is a production crash trigger

Evidence:
- `main.py:142-145` registers `GET /sentry-debug` and unconditionally executes `1 / 0`.
- Browser/runtime probe: `/sentry-debug` returned `500 Internal Server Error`.

Problem:
A public endpoint intentionally raises an exception in all environments.

Impact:
Anyone can generate 500s, spam Sentry/error logs, and create false production incidents. It also makes health/monitoring noise easier to trigger.

Recommendation:
Remove the endpoint from production, or guard it behind `HOSTING=false`/admin auth plus an explicit debug flag.

### CR-20-I4 — Important — Error responses can miss `X-Request-ID`

Evidence:
- `backend/logging_setup.py:57-75` adds `X-Request-ID` only after `await call_next(request)` returns successfully.
- Runtime/browser probe: `/sentry-debug` 500 response had no `X-Request-ID` header.

Problem:
Unhandled exceptions skip the response-header injection path.

Impact:
The exact requests that most need incident correlation are missing the trace ID in the client response.

Recommendation:
Use a middleware pattern that guarantees request ID injection for error responses, or add a global exception handler that preserves the request ID. Also log exception paths with request ID.

### CR-20-I5 — Important — Production rate limiting defaults to in-memory storage

Evidence:
- `main.py:38-43` defaults `RATE_LIMIT_STORAGE` to `memory://`.
- `.env.example:29-32` documents `RATE_LIMIT_STORAGE=memory://`.

Problem:
The default limiter storage is process-local and resets on restart.

Impact:
In multi-process/multi-replica production, rate limits are inconsistent and easily bypassed by process/instance distribution. On restart, all counters reset.

Recommendation:
Use Redis or another shared backend in production. Fail fast or warn loudly when `HOSTING=true` and `RATE_LIMIT_STORAGE=memory://`.

### CR-20-I6 — Important — Sentry config sends default PII and logs a DSN prefix

Evidence:
- `backend/logging_setup.py:85-95` calls `sentry_sdk.init(..., send_default_pii=True)`.
- `backend/logging_setup.py:96` logs a shortened DSN value.

Problem:
Production observability currently opts into default PII collection and logs part of the DSN.

Impact:
This can leak more user/request data into Sentry than intended and leaves credential-like configuration material in logs.

Recommendation:
Default `send_default_pii` to false unless explicitly enabled by env/config and documented. Do not log DSN material; log only whether Sentry is enabled and the environment.

### CR-20-I7 — Important — Deployment tests skip the real Docker build/start path

Evidence:
- `tests/test_docker.py:150-183` has integration tests marked skipped when Docker is unavailable.
- `tests/test_docker.py:157-174` comments out the actual Docker build command and only checks file existence.
- Review environment probe: `docker` command was unavailable, so no container build/start verification ran.

Problem:
Current tests validate Dockerfile text shape, not that the production container builds, starts, contains wiki assets, runs migrations safely, and serves health endpoints.

Impact:
Docker/Railway regressions can pass the focused test suite.

Recommendation:
Add CI-only Docker build/start smoke: build image, run with `HOSTING=true`, `JWT_SECRET` set, `DB_PATH` pointed at a temp volume, then curl `/`, `/health`, `/api/health`, and a wiki-backed endpoint.

### CR-20-S1 — Suggestion — `Procfile` is stale relative to Railway Dockerfile deployment

Evidence:
- `railway.json:2-4` uses Dockerfile builder.
- `Dockerfile:14` defines the actual runtime command.
- `Procfile:1` uses a different `${PORT:-8000}` command.

Problem:
The Procfile is not the Railway runtime path but remains in the repo with a separate command style.

Impact:
This can confuse future deployment debugging or a non-Docker platform migration.

Recommendation:
Either remove it, document it as non-Railway fallback, or keep it synchronized with the supported deployment path.

## Verification performed

Focused tests:

```bash
uv run python -m pytest tests/test_docker.py tests/test_security_headers.py tests/test_rate_limit.py tests/test_logging.py -q
```

Result: `25 passed, 2 skipped`.

Scoped lint:

```bash
uv run ruff check main.py backend/security/headers.py backend/logging_setup.py backend/auth/__init__.py backend/db/database.py tests/test_docker.py tests/test_security_headers.py tests/test_rate_limit.py tests/test_logging.py
```

Result: `All checks passed!`.

Local server smoke:

```bash
curl -sS -o /tmp/health20.txt -w '%{http_code}\n' http://127.0.0.1:8000/api/health && cat /tmp/health20.txt
curl -sS -o /tmp/root20.html -w '%{http_code} %{size_download}\n' http://127.0.0.1:8000/
```

Result:
- `/api/health` → `200 {"status":"ok","version":"0.7.7"}`
- `/` → `200`, 8058 bytes

Production-like header probes with `TestClient`:

- `HOSTING=true`, evil Origin was not reflected in CORS.
- `/`, `/health`, `/api/health` had no CSP header.
- HTTPS `/health` had `Strict-Transport-Security: max-age=31536000; includeSubDomains; preload`.
- `/sentry-debug` returned 500 and no `X-Request-ID`.

Database migration probe:

- Isolated temp DB replay count before second `migrate()`: `1`.
- Replay count after second `migrate()`: `0`.

Browser smoke:

- `/` loaded successfully.
- Fetch probes for `/`, `/health`, `/api/health`, `/sentry-debug` matched the header/status observations above.
- Browser console had no app JS errors; Tailwind CDN production warning was present.

Docker availability:

- `docker` command was not available in this environment, so no real Docker build/start could be executed.

Independent review:

- `delegate_task` performed a second-pass deployment/config review and independently identified the replay-drop migration, branch mismatch, JWT fallback, disabled CSP, public debug crash endpoint, missing error request IDs, and in-memory limiter defaults.

Codex:

- Attempted, but unavailable: `/usr/bin/bash: line 3: codex: command not found`.

## Non-findings / notes

- `.dockerignore` does not exclude `wiki/`; Docker context should include wiki assets.
- `railway.json` has no `startCommand`, uses Dockerfile builder, root healthcheck `/`, and timeout `100`, which matches the current Warpsmith Railway notes.
- `Dockerfile` uses single-stage `python:3.12-slim`, installs `requirements.txt`, and does not use editable install.
- No secrets were exposed in this report.
