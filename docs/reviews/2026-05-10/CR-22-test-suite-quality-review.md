---
title: "CR-22 — Test suite quality review"
status: request-changes
date: 2026-05-10
review: CR-22
scope:
  - tests/
  - pyproject.toml pytest/coverage config
  - backend/db/database.py test isolation boundaries
  - backend/billing/ and subscription-related routes
  - web/routes/auth.py and backend/auth/providers/
  - web/routes/api_replays.py autoplay/replay integration
  - frontend/static behavior coverage
verdict: "Request Changes"
critical_findings: 2
important_findings: 9
suggestions: 2
---

# CR-22 — Test suite quality review

## Verdict

**Request Changes.**

The suite is large enough to be useful (`457 tests collected`, `454 passed`, `3 skipped`), but it is not yet a reliable regression gate. Several major product/commercialization bugs from earlier reviews would still pass because coverage is concentrated in lower-level engine behavior and many route/frontend/production tests are status-only, placeholder, or not isolated.

## Review scope

Checked:

- `tests/` structure, assertions, fixtures, skips, random/time usage.
- `pyproject.toml` pytest/coverage configuration.
- Route/test coverage around auth, billing, subscriptions, replay, deployment/security, frontend static behavior.
- DB isolation and persistent side effects.
- Full-suite behavior, coverage gate behavior, lint.

## Verification commands

```bash
uv run python -m pytest tests/ -q
uv run python -m pytest --collect-only -q
uv run python -m pytest tests/ --cov=backend --cov=web --cov=main --cov-report=term-missing:skip-covered -q
uv run ruff check tests
curl -sS -o /tmp/health22.txt -w '%{http_code}\n' http://127.0.0.1:8000/api/health && cat /tmp/health22.txt || true
```

Results:

- Full suite: `454 passed, 3 skipped, 33 warnings in 30.82s`.
- Collection: `457 tests collected`.
- Coverage run: all tests passed, but command exited `1` because total coverage is `78.58%`, below `--cov-fail-under=80`.
- Ruff on tests: `All checks passed!`.
- Local health: `200 {"status":"ok","version":"0.7.7"}`.
- Codex independent review: attempted, but CLI unavailable: `/usr/bin/bash: line 3: codex: command not found`.
- Independent `delegate_task` review completed and confirmed the main findings.

## Coverage snapshot

Lowest-impact gaps from explicit coverage run:

| File | Coverage | Notes |
|---|---:|---|
| `backend/auth/providers/google.py` | 0% | OAuth provider path untested. |
| `backend/auth/providers/vk.py` | 0% | OAuth provider path untested. |
| `backend/billing/stripe_stub.py` | 0% | Checkout/session stub untested. |
| `backend/auth/providers/routes.py` | 30% | OAuth state/callback/linking mostly untested. |
| `web/routes/api_detachments.py` | 32% | API route behavior weakly covered. |
| `web/routes/api_replays.py` | 43% | Autoplay/replay/result happy paths weakly covered. |
| `backend/loader/parser.py` | 47% | Parser edge cases weakly covered. |
| `web/routes/auth.py` | 60% | Login/register/current-user pages/API gaps. |
| `web/routes/api.py` | 63% | Large API surface not covered by route-level tests. |

## Findings

### Critical 1 — Tests mutate the real project SQLite database

Evidence:

- `tests/conftest.py:5-12` only sets rate-limit env variables and imports `main.app`; it does not set `DB_PATH` to a temporary DB before app/database initialization.
- `backend/db/database.py` defaults `DB_PATH` to `Path.cwd() / "simulator.db"`.
- `tests/test_rosters.py:35-47` registers users through `/auth/register`.
- `tests/test_rosters.py:64`, `114`, `123`, `141`, `168`, `196` create persistent rosters through the real app.
- Live DB after review runs contained persistent test data:
  - `users 622`
  - `rosters 404`
  - `scenarios 0`
  - `replays 0`

Impact:

- Test order and previous local runs can affect results.
- Developer data is polluted.
- Bugs can hide behind pre-existing rows.
- A failed/partial run leaves state for the next run.

Expected gate:

- Each test or test session should use a disposable DB via `tmp_path`/`:memory:`/transaction rollback, configured before importing `main`/`backend.db.database`.

### Critical 2 — Coverage threshold is configured but not enforced by the normal test command

Evidence:

- `pyproject.toml:136` sets `addopts = "-v --tb=short --cov-fail-under=80"`.
- Normal full suite command passes without coverage output:
  - `uv run python -m pytest tests/ -q` → `454 passed, 3 skipped`.
- Explicit coverage command fails:
  - `uv run python -m pytest tests/ --cov=backend --cov=web --cov=main --cov-report=term-missing:skip-covered -q`
  - Total coverage: `78.58%`.
  - Exit: `1`, `Coverage failure: total of 79 is less than fail-under=80`.

Impact:

- CI/local can report green while the intended minimum coverage gate is below threshold.
- Review/fix cycle may incorrectly treat the suite as fully passing.

Expected gate:

- Either include `--cov=backend --cov=web --cov=main` in default pytest/CI config, or remove the misleading fail-under and add a dedicated required coverage job.

### Important 1 — Billing/subscription/free-premium gates are effectively untested

Evidence:

- `backend/billing/webhooks.py` defines webhook/subscribe/portal routes.
- `backend/billing/plans.py` defines `FREE`, `PREMIUM`, `UserFeatures`, `for_user()`, and `require_tier()`.
- `backend/billing/stripe_stub.py` is 0% covered.
- Search over tests found no references to:
  - `billing`
  - `subscribe`
  - `stripe`
  - `webhook`
  - `portal`
  - `premium`
  - `max_rosters`
  - `features`
  - `trial`

Impact:

- CR-19 monetization defects would pass the suite: unsigned webhook acceptance, stubbed subscribe/portal, free roster-limit bypass through duplicate, public roster creation for Free, and missing `/api/me.features`.

Expected tests:

- Authenticated/unauthenticated `/api/subscribe` behavior.
- Webhook signature validation and subscription state transition.
- Free vs Premium feature gate matrix.
- `/api/me` subscription/features contract.
- Roster create/duplicate/public/free-limit boundaries.

### Important 2 — Auth, `/api/me`, and OAuth provider flows are under-tested

Evidence:

- `web/routes/auth.py` coverage is 60%.
- `backend/auth/providers/routes.py` coverage is 30%.
- `backend/auth/providers/google.py` and `vk.py` are 0% covered.
- Test search found no references to:
  - `/api/me`
  - `/auth/me`
  - `/auth/login`
  - OAuth provider callback/state flows.

Impact:

- Session-cookie regressions, current-user response regressions, OAuth CSRF state handling, provider token exchange failures, and account-linking bugs can ship undetected.

Expected tests:

- Register/login/logout/current-user cookie lifecycle.
- Invalid credentials and duplicate email.
- `/api/me` anonymous vs authenticated user contract.
- OAuth callback missing/invalid state, provider errors, and successful user creation/linking with mocked provider.

### Important 3 — Deployment/security regressions from CR-20 are not covered

Evidence:

- `tests/test_security_headers.py` checks basic headers and CORS but does not assert CSP.
- Search found no test references to `CSP` or `Content-Security-Policy`.
- `tests/test_logging.py` covers `/sentry-debug`, but earlier runtime review showed that a 500 response can lose `X-Request-ID`; no test guards that boundary.
- No migration test asserts that re-running `db.migrate()` preserves existing `replays`.
- Docker integration tests in `tests/test_docker.py:153-183` are skipped if Docker is unavailable and currently contain placeholder file-existence checks instead of real build/start checks.

Impact:

- CR-20 issues would pass: CSP disabled, destructive replay migration, public debug 500 endpoint, and non-real Docker deploy validation.

Expected tests:

- Production-mode CSP header present.
- Request ID present on handled and unhandled error responses.
- Migration idempotency/preservation for every table.
- Real Docker build/start health check in CI environment where Docker is available.

### Important 4 — Autoplay/replay/result integration coverage is shallow

Evidence:

- `web/routes/api_replays.py` coverage is 43%.
- The critical `/api/auto-play` route contains DB roster loading, deployment validation, simulation, replay saving, and response summary logic.
- Search found no tests referencing `/api/auto-play`.
- `tests/test_round_viewer.py:18-34` only verifies 404 JSON shape for nonexistent replay IDs.
- `tests/test_round_viewer.py:37-42` only checks that `/api/replays` returns a list.
- `tests/test_round_viewer.py:45-54` is a JS string-presence placeholder for VP logic.

Impact:

- Regressions in full route-level simulation, replay persistence, result winner computation, and replay retrieval can pass.

Expected tests:

- Seed two valid rosters in an isolated DB.
- POST `/api/auto-play` and assert replay ID, round snapshots, winner/VP contract, saved replay row.
- GET `/api/replays/{game_id}` and `/api/results/{game_id}` happy path.
- Auth/feature gate expectations after monetization is fixed.

### Important 5 — Frontend tests mostly check static strings, not behavior

Evidence:

- `tests/test_team_builder.py:6-17` checks only page `200` and a script marker.
- `tests/test_progressive_disclosure.py:13-34` checks for strings/classes but not toggle behavior, body class mutation, or `localStorage` failure handling.
- `tests/test_tooltips.py:14-62` checks static `data-stat` strings.
- `tests/test_canvas_map.py:103-119` reads `battlefield_map.js` and asserts literal function/string names.
- Search found no tests for `localStorage`, `loadMode`, `@apply`, `pricing`, or Tailwind helper class behavior.

Impact:

- CR-18 frontend defects would pass: broken pricing CTA method/contract, Tailwind `@apply` helper classes not compiled by CDN, progressive-disclosure `localStorage.getItem()` failure, and many JS runtime regressions.

Expected tests:

- At least syntax-check every maintained JS file with `node -c`.
- Browser/DOM smoke for progressive disclosure toggle and blocked-storage fallback.
- Pricing CTA contract test.
- Team Builder modal save/edit/warlord/points UI behavior tests.

### Important 6 — Placeholder/no-op tests inflate confidence

Evidence:

- `tests/test_unit_modal.py:86-90` ends with `assert True` for squad-size validation.
- `tests/test_unit_modal.py:96-99` ends with `assert True` for loadout selection.
- `tests/test_unit_modal.py:105-108` ends with `assert True` for cost calculation.
- `tests/test_generate_roster.py:29-38` says warlord assignment is verified, but does not assert anything about warlord assignment; a later test partially covers this, making this one redundant/misleading.
- Automated AST scan found `11` test functions without `assert`; some are valid `pytest.raises`, but several are placeholders or weak checks.

Impact:

- Test count looks healthier than actual regression protection.

Expected tests:

- Replace placeholders with behavior-level tests or mark them `xfail(strict=True)` with a tracked issue.
- Remove duplicate/no-value placeholder tests from the “green suite” count.

### Important 7 — Conditional assertions allow empty/no-op behavior to pass

Evidence:

- `tests/test_unit_modal.py:25-31` validates weapon fields only `if data.get("weapons")`.
- `tests/test_unit_modal.py:42-50` validates wargear fields only `if wargear_options`.
- `tests/test_synergy_hints.py:47-50` checks transport messages only `if transport_checks`.
- `tests/test_synergy_hints.py:62-65` checks empty transport warning only `if transport_checks`.
- `tests/test_synergy_hints.py:67-80` computes leader checks but asserts nothing.
- `tests/test_synergy_hints.py:115-129` computes synergy checks but asserts nothing.

Impact:

- Endpoints can silently return no data/no checks and still pass.

Expected tests:

- Use known fixtures where a weapon/wargear/transport/leader/synergy check must exist.
- Assert the presence, severity, and message contract for each expected check.

### Important 8 — Some auth/ownership assertions are overly broad

Evidence:

- `tests/test_rosters.py:152-157` says unauthenticated `GET /api/rosters` should return 401/403, but accepts `(200, 401, 403)`.
- `tests/test_rosters.py:159-163` accepts `(401, 403)` for unauthenticated POST without asserting the exact API contract.
- Automated scan found broad status-code tuple checks in:
  - `tests/test_rate_limit.py:42:test_rate_limit_health_exempt`
  - `tests/test_rosters.py:152:test_unauthorized_get`
  - `tests/test_rosters.py:159:test_unauthorized_post`

Impact:

- Auth contract changes from protected to optional, or from 401 to 403, can pass unnoticed.
- Tests document uncertainty instead of enforcing a decision.

Expected tests:

- Define exact expected status and response shape for anonymous list/create/update/delete/read-private-public behavior.

### Important 9 — Test suite has flakiness and worktree hygiene risks

Evidence:

- `tests/test_autoplay.py:123-133` uses `AutoPlayConfig(time_limit_seconds=0.001)` and expects a wall-clock timeout.
- Randomness appears in several files without deterministic seed control:
  - `tests/test_autoplay.py`
  - `tests/test_dice.py`
  - `tests/test_f2_7_battle_shock_cp_stratagems.py`
  - `tests/test_modifiers.py`
  - `tests/test_weapon.py`
  - `tests/test_weapon_keywords_phase2.py`
- `tests/test_parser.py:37-41` writes generated files under `tests/.tmp_parser/frontmatter`.
- `tests/test_parser.py:72-80` writes cache/files under `tests/.tmp_parser/cache`.

Impact:

- Timing and random behavior can produce machine/load-dependent failures.
- Tests can leave artifacts in the repo and influence later runs.

Expected tests:

- Use injectable clock/time budget or monkeypatch time for timeout behavior.
- Seed randomness or assert statistical properties robustly.
- Use `tmp_path` for parser temp files and cache.

## Suggestions

### Suggestion 1 — Deduplicate low-value structure checks

Examples:

- `tests/test_canvas_map.py:27-35` and `135-144` both verify tile integer ranges.
- `tests/test_tooltips.py:31-53` has six near-identical stat checks, then `59-62` repeats the same idea in a loop.

Reduce duplication and spend the saved test budget on behavior-level tests for UI interactions and route contracts.

### Suggestion 2 — Promote prior review repro probes into permanent regression tests

CR-18 through CR-21 already produced concrete repro probes. The strongest ones should become tests before fixes land:

- Pricing CTA method/contract.
- Progressive disclosure storage failure.
- Billing webhook signature/state transition.
- Free/Premium roster gate matrix including duplicate/public bypasses.
- Migration idempotency preserving replays.
- CSP/request-id/error response production checks.
- Docs facts/count consistency script.

## Positive notes

- Full suite currently completes quickly enough for local iteration: about 31 seconds without coverage.
- Engine/model/rules layers have meaningful coverage in many areas.
- `tests/test_rosters.py` contains useful CRUD/validation coverage and should be extended rather than replaced.
- `ruff check tests` is clean.

## Final decision

**Request Changes** until the suite is isolated, the coverage gate is actually enforced or corrected, and the missing high-risk route/product gates are covered by regression tests.
