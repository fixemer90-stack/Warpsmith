# Review — Task 2.2: Enforce exactly one Warlord when required

Date: 2026-05-17
Verdict: REQUEST CHANGES → FIXED 2026-05-17

## Resolution

All original findings are resolved.

### Important 1 — Auto mode accepted 2+ eligible Characters without Warlord (Fixed)

- `validate_roster(..., is_warlord=None)` now rejects two or more eligible Characters with `no_warlord`.
- Deterministic probe confirms one eligible Character auto mode is valid, but two eligible Characters without a selected Warlord are invalid.

### Important 2 — Generator used narrower eligibility than validator (Fixed)

- Added shared `is_unit_eligible_warlord(unit)` helper in `backend/state/roster.py`.
- Validator, API Warlord checks, and generated roster selection use the same helper.
- Generated Orks/T'au rosters validate through `validate_roster()` with exactly one eligible Warlord.

### Important 3 — Closure documentation was stale (Fixed)

- Task 2.2 frontmatter is `status: completed`.
- Verification commands use existing files: `tests/test_roster*.py tests/test_rosters.py`.
- Source plan, index, CR evidence, and Phase 2 triage summary are synchronized.

## Re-check results

```text
- `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_roster*.py tests/test_rosters.py -q` → 68 passed, 48 warnings.
- `uv run python -m pytest tests/ -q` → 562 passed, 3 skipped, 60 warnings.
- `uv run ruff check backend/state/roster.py web/routes/api_rosters.py backend/billing/plans.py backend/engine/ai/autoplay.py tests/test_roster.py tests/test_rosters.py tests/test_autoplay.py` → clean.
- `uv run ruff format --check backend/state/roster.py web/routes/api_rosters.py backend/billing/plans.py backend/engine/ai/autoplay.py tests/test_roster.py tests/test_rosters.py tests/test_autoplay.py` → 7 files already formatted.
- Deterministic Warlord probe → zero eligible, two eligible/no Warlord, two Warlords, and non-Character Warlord rejected; one eligible auto and exactly one explicit Warlord accepted.
- Generated roster probe → Orks/T'au generated rosters validate through `validate_roster()` with exactly one eligible Warlord; Mechanicus skipped because current wiki has no valid Mechanicus units.
```
