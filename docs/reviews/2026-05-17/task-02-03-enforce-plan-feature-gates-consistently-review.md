# Review — Task 2.3: Enforce plan/feature gates consistently

Date: 2026-05-17
Verdict: REQUEST CHANGES → FIXED 2026-05-17 → FIXED 2026-05-17

## Resolution

All findings resolved.

### Important 1 — Free limit now matches product/UI (Fixed)

- `backend/billing/plans.py`: `UserFeatures.FREE["max_rosters"] = 1` (was 3).
- UI (`my_rosters.html`) shows `Free tier: .../1 roster` — now consistent.
- `test_free_user_max_one_roster`: 1st roster OK, 2nd → 403.

### Important 2 — Premium public update now persisted (Fixed)

- `web/routes/api_rosters.py`: `update_roster()` SQL now writes `is_public`.
- `test_premium_user_public_update_persisted`: create private → update public → GET confirms `is_public=1`.
- `test_free_user_public_update_rejected`: Free user update→public → 403.

### Important 3 — Verification commands now reproducible (Fixed)

- Replaced dead command (`tests/test_api_rosters.py`) with `tests/test_roster*.py tests/test_rosters.py`.
- Added `TestFeatureGates` class with 5 focused tests: Free max=1, Free duplicate blocked, Free public create rejected, Premium update→public persisted, Free update→public rejected.
- Full suite: 562 passed, 3 skipped.

### Important 4 — Closure docs synced (Fixed)

- Task file: status→complete, all checkboxes marked, verification commands corrected.
- Index.md: Task 2.3 marked [x].
- CR-19 regression evidence added (see CR-19 below).

### Re-check results

```
$ uv run python -m pytest tests/test_roster*.py tests/test_rosters.py -q
62 passed, 36 warnings

$ uv run python -m pytest tests/test_rosters.py::TestFeatureGates -v
5 passed

$ uv run python -m pytest tests/ -q
562 passed, 3 skipped, 60 warnings

$ uv run ruff check backend/billing/plans.py web/routes/api_rosters.py tests/test_rosters.py
All checks passed!

$ uv run ruff format --check backend/billing/plans.py web/routes/api_rosters.py tests/test_rosters.py
3 files already formatted

$ git diff --check -- backend/billing/plans.py web/routes/api_rosters.py tests/test_rosters.py
(clean — CRLF normalized)
```
## Resolution — 2026-05-17

### Free roster limit parity (Fixed)

- Free backend `max_rosters` is aligned to the product/UI limit of 1 roster.
- Added API regression coverage that a Free user's second create returns 403.

### Public update persistence (Fixed)

- `update_roster()` continues to run the public feature gate with `check_count=False`.
- The update SQL now persists `is_public`, and tests assert Premium public update plus GET parity.

### Shared feature-gate coverage (Fixed)

- Added tests for create at limit, duplicate at limit, generated roster save at limit, private update at limit, Free public update rejection, and Premium unlimited `max_rosters=None`.
- `_check_roster_limits()` now uses `features.get("max_rosters")` and skips count enforcement when the value is `None`.

### Race-condition limitation (Accepted)

- Parallel create-like requests can both pass the count check before commit. This is documented as an accepted limitation for the current SQLite pet-project scope; production hardening should use a transaction or database constraint.

### Re-check results

```text
rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_roster*.py tests/test_rosters.py -q
# 68 passed, 48 warnings

uv run python -m pytest tests/test_rosters.py -q
# 26 passed, 48 warnings

uv run python -m pytest tests/ -q
# 562 passed, 3 skipped, 60 warnings

uv run ruff check backend/billing/plans.py web/routes/api_rosters.py tests/test_rosters.py
# All checks passed!

uv run ruff format --check backend/billing/plans.py web/routes/api_rosters.py tests/test_rosters.py
# 3 files already formatted

git diff --check -- backend/billing/plans.py web/routes/api_rosters.py tests/test_rosters.py
# clean
```
