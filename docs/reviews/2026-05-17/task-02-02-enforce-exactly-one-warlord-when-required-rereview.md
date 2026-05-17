# Re-review — Task 2.2: Enforce exactly one Warlord when required

Date: 2026-05-17
Verdict: REQUEST CHANGES — code fixed, closure docs still stale → FIXED 2026-05-17

## Resolution

The re-review blockers are resolved.

- Task contract now states the corrected core rule: rosters with zero eligible Characters are invalid because every army must include a Character Warlord.
- Task frontmatter is `status: completed`; acceptance criteria and completion requirements are checked.
- The original review file no longer mixes a fixed verdict with stale request-changes body.
- Verification uses reproducible commands and current results.
- Source plan, visible index status, CR evidence, and Phase 2 checkpoint are synchronized.

## Deterministic Warlord probe

```text
eligibility {'TagChar': True, 'CatChar': True, 'Leader': True, 'CanWar': True, 'Boyz': False}
zero_eligible_auto valid= False errors= ['no_eligible_warlord']
one_tag_char_auto valid= True errors= []
two_chars_auto valid= False errors= ['no_warlord']
two_chars_explicit_one valid= True errors= []
two_chars_explicit_zero valid= False errors= ['no_warlord']
two_chars_explicit_two valid= False errors= ['too_many_warlords']
non_char_marked valid= False errors= ['invalid_warlord']
```

## Re-check results

```text
- `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_roster*.py tests/test_rosters.py -q` → 68 passed, 48 warnings.
- `uv run python -m pytest tests/ -q` → 562 passed, 3 skipped, 60 warnings.
- `uv run ruff check backend/state/roster.py web/routes/api_rosters.py backend/billing/plans.py backend/engine/ai/autoplay.py tests/test_roster.py tests/test_rosters.py tests/test_autoplay.py` → clean.
- `uv run ruff format --check backend/state/roster.py web/routes/api_rosters.py backend/billing/plans.py backend/engine/ai/autoplay.py tests/test_roster.py tests/test_rosters.py tests/test_autoplay.py` → 7 files already formatted.
- Deterministic Warlord probe → zero eligible, two eligible/no Warlord, two Warlords, and non-Character Warlord rejected; one eligible auto and exactly one explicit Warlord accepted.
- Generated roster probe → Orks/T'au generated rosters validate through `validate_roster()` with exactly one eligible Warlord; Mechanicus skipped because current wiki has no valid Mechanicus units.
```
