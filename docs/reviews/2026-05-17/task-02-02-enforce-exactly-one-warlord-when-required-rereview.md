# Re-review — Task 2.2: Enforce exactly one Warlord when required

Date: 2026-05-17
Verdict: REQUEST CHANGES — code fixed, closure docs still stale

## Summary

The original Task 2.2 code blockers are fixed in the current working tree: the shared validator rejects zero eligible Characters, rejects multiple eligible Characters in auto mode, and the generator/API use the shared Warlord eligibility helper. However, the task cannot be closed because the task artifact and review artifact still contain stale/contradictory closure text.

## Findings

### Important 1 — Task file still says `status: changes_requested` and contains stale contract text

Evidence:

- `docs/remediation/task-02-02-enforce-exactly-one-warlord-when-required.md` frontmatter is still `status: changes_requested`.
- The task’s `Warlord validation contract` still says: `If roster has zero eligible Characters, Warlord requirement is not enforced unless faction/rules data explicitly requires otherwise.`
- Current code and the corrected WH40k 10e contract reject zero eligible Characters with `no_eligible_warlord`.

Required fix:

- Update the task contract to say zero eligible Characters is invalid under core rules.
- After all closure requirements are complete, set frontmatter to `status: completed`.

### Important 2 — Existing review file mixes FIXED verdict with old REQUEST CHANGES body

Evidence:

- `docs/reviews/2026-05-17/task-02-02-enforce-exactly-one-warlord-when-required-review.md` line 4 says `Verdict: REQUEST CHANGES → FIXED 2026-05-17`.
- The same file later still says `Task 2.2 is not ready to close`, includes old blocking findings, and ends with `REQUEST CHANGES. Do not mark Task 2.2 completed...`.

Required fix:

- Replace or clearly supersede the stale blocker body with a resolution section only, or add a re-review fixed section after docs are synced.

### Important 3 — Task verification is still stale

Evidence:

- Task file still claims `tests/test_api_rosters.py`, but this file does not exist.
- Actual scoped command used during this re-review is `tests/test_roster*.py tests/test_rosters.py`.

Required fix:

- Update Task 2.2 Verification with reproducible commands and latest results.

## Deterministic Warlord probe

```text
eligible tag_char True
eligible cat_char True
eligible leader True
eligible boy False
zero_eligible_auto valid= False errors= ['no_eligible_warlord']
one_tag_char_auto valid= True errors= []
two_chars_auto valid= False errors= ['no_warlord']
two_chars_explicit_one valid= True errors= []
two_chars_explicit_zero valid= False errors= ['no_warlord']
non_char_marked valid= False errors= ['invalid_warlord']
```

## Verification run during review

```text
rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_roster*.py tests/test_rosters.py -q
→ 57 passed, 26 warnings

uv run python -m pytest tests/test_api_rosters.py tests/test_billing*.py -q
→ failed, exit 4: tests/test_api_rosters.py does not exist

uv run python -m pytest tests/ -q
→ failed: 6 failed, 544 passed, 3 skipped, 38 warnings

uv run ruff check backend/state/roster.py web/routes/api_rosters.py backend/billing/plans.py tests/test_roster.py tests/test_rosters.py
→ All checks passed

uv run ruff format --check backend/state/roster.py web/routes/api_rosters.py backend/billing/plans.py tests/test_roster.py tests/test_rosters.py
→ 5 files already formatted
```

## Verdict

REQUEST CHANGES for closure artifacts only. Code-level Warlord behavior appears fixed, but Task 2.2 is not cleanly closed until the stale task/review verification text is synchronized.
