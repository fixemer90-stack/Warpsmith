# Review — Task 2.2: Enforce exactly one Warlord when required

Date: 2026-05-17
Verdict: REQUEST CHANGES → FIXED 2026-05-17

## Resolution

All findings resolved.

### Important 1 — Auto mode accepted 2+ eligible chars without Warlord (Fixed)

- `validate_roster()` auto mode (`is_warlord=None`) now rejects 2+ eligible Characters without a Warlord.
- 0 or 1 eligible: OK (auto-select). 2+: `no_warlord` error.
- `test_multiple_characters_no_warlord` updated to assert rejection.
- `test_valid_roster` updated to pass explicit `is_warlord`.

### Important 2 — Generator used narrower eligibility (Fixed)

- Created shared `is_unit_eligible_warlord(unit)` helper in `roster.py`.
- Both `validate_roster()` and `generate_roster()` now use the same helper.
- `_warlord_validation_errors()` also uses the shared helper.
- All eligibility paths unified: `can_be_warlord`, `is_leader`, `category == Character`, `character` tag.

### Important 3 — Documentation not synced (Fixed)

- Task verification command corrected: `tests/test_roster*.py tests/test_rosters.py -q` (not `test_api_rosters.py`).
- CR evidence sections added to CR-12, CR-16, CR-17, CR-19.
- Source plan/remediation-plan.md and index.md updated.

### Re-check results

```bash
uv run python -m pytest tests/test_roster.py tests/test_rosters.py -q
# 56 passed, 26 warnings
uv run python -m pytest tests/ -q
# 543 passed, 3 skipped, 0 failed
uv run ruff check backend/state/roster.py web/routes/api_rosters.py tests/test_roster.py
# All checks passed
uv run ruff format --check backend/state/roster.py web/routes/api_rosters.py tests/test_roster.py
# 3 files already formatted
git diff --check
# Clean
```

## Summary

Task 2.2 is not ready to close. Focused tests currently pass, but the implementation does not satisfy the task contract and the closure artifacts are stale/incomplete.

## Findings

### Important 1 — Shared backend validator still accepts multiple eligible Characters with no Warlord

Acceptance criteria say the shared backend roster validator must reject rosters with multiple eligible Characters and no Warlord. The current implementation only rejects this when `is_warlord` is explicitly passed. If callers use `validate_roster(..., is_warlord=None)`, two eligible Characters with no Warlord are accepted.

Evidence:

```text
shared_validator_multiple_chars_no_flags valid= True errors= []
explicit_multiple_chars_no_warlord valid= False errors= ['no_warlord']
```

Relevant code:

- `backend/state/roster.py:282-286` treats any `num_eligible >= 1` as OK in auto mode.
- `tests/test_roster.py:130-135` asserts this invalid state is valid (`Expected valid (auto-select)`).

Why this blocks closure:

- Violates: `Validator rejects rosters with multiple eligible Characters and no Warlord.`
- Violates the shared-backend-validator requirement because a non-API caller can still bypass the rule.
- The docstring says auto mode selects when exactly one eligible Character exists, but the code accepts any count.

Required fix:

- Make `validate_roster()` enforce exactly one Warlord whenever at least one eligible Character exists, or introduce a deliberately named generated-roster helper that explicitly assigns a Warlord before validation.
- Replace the current test expectation with a regression test that `validate_roster([two Characters], is_warlord=None)` fails unless a Warlord is provided/assigned by the generation path.

### Important 2 — Generated roster Warlord selection uses a narrower eligibility definition than validation

`generate_roster()` only detects/selects Warlords through `unit.can_be_warlord`. The validator also treats `is_leader`, `category == "character"`, and `character` tag as eligible.

Relevant code:

- `web/routes/api_rosters.py:322-323`, `329-333`, `363-367` use only `unit.can_be_warlord`.
- `backend/state/roster.py:223-228` uses a broader eligibility predicate.

Why this blocks closure:

- Violates: `Generated rosters always persist exactly one valid Warlord when eligible Characters exist.`
- A generated roster containing only units eligible via category/tag/is_leader can return zero `is_warlord: true` even though validation would consider a Warlord required.
- The generator does not run the shared validator on its final selected payload, so this drift is not caught.

Required fix:

- Share one Warlord eligibility helper between validator/API/generator.
- Ensure generated rosters explicitly set exactly one Warlord among all eligible Characters, then validate the generated payload through the same backend validator before returning/persisting it.

### Important 3 — Closure documentation is not synced and contains false verification claims

Evidence:

- `docs/remediation/remediation-plan.md:443-458` still has Task 2.2 acceptance/contract checkboxes unchecked.
- `docs/remediation/index.md:56` has no visible completed status for Task 2.2.
- No `Regression evidence — Task 2.2` section was found in CR-12, CR-16, CR-17, or CR-19, despite the task file claiming it was added.
- The task file claims this command passed:

```text
uv run python -m pytest tests/test_roster*.py tests/test_api_rosters.py -q
```

Actual result:

```text
ERROR: file or directory not found: tests/test_api_rosters.py
collected 0 items
exit_code=4
```

Why this blocks closure:

- Violates completion requirements for source plan/index/CR evidence sync.
- Verification evidence is not reproducible as written.

Required fix:

- Update the task file with current, reproducible verification commands and actual results.
- Sync `docs/remediation/remediation-plan.md`, `docs/remediation/index.md`, and CR-12/16/17/19 only after the code fixes are verified.

## Verification run during review

```text
rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_roster.py tests/test_rosters.py -q
→ 56 passed, 26 warnings

uv run python -m pytest tests/test_roster*.py tests/test_api_rosters.py -q
→ failed, exit_code=4: tests/test_api_rosters.py does not exist

uv run ruff check backend/state/roster.py web/routes/api_rosters.py tests/test_roster.py tests/test_rosters.py
→ All checks passed!

uv run ruff format --check backend/state/roster.py web/routes/api_rosters.py tests/test_roster.py tests/test_rosters.py
→ 4 files already formatted

git diff --check -- backend/state/roster.py web/routes/api_rosters.py tests/test_roster.py tests/test_rosters.py docs/remediation/task-02-02-enforce-exactly-one-warlord-when-required.md
→ clean
```

## Verdict

REQUEST CHANGES. Do not mark Task 2.2 completed until the validator/generator issues are fixed and closure docs are synced with reproducible verification evidence.
