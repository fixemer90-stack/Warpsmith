# Review — Task 2.1 Lock the canonical PTS formula

Date: 2026-05-17
Task: `docs/remediation/task-02-01-lock-the-canonical-pts-formula.md`
Scope: Verify the claimed completed implementation of Task 2.1.

## Verdict

REQUEST CHANGES after re-review 2026-05-17 → FIXED 2026-05-17.

## Resolution

All remaining issues are resolved.

### Closure docs stale (Fixed)

- Task frontmatter remains `status: completed`.
- Verification and completion requirements now reflect current green Phase 2 checks.
- Source plan, index, CR evidence, and review file are synchronized.

### Frontend formula contract parity (Fixed)

- `test_pts_formula_parity_fixture()` documents exact backend formula scenarios.
- `team_builder.js` retains the same arithmetic with a backend-contract comment; parity is covered by the shared fixture.

### Production loadout/Nob parity (Fixed)

- `validate_roster()` accepts `loadout_pts`/`nob_pts` and uses `calculate_squad_pts()` for production totals.
- API create/update resolve selected loadout/Nob options and read paths recalculate totals consistently.

## Re-check results

```text
rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_roster*.py tests/test_rosters.py -q
→ 68 passed, 48 warnings

uv run python -m pytest tests/ -q
→ 562 passed, 3 skipped, 60 warnings

uv run ruff check backend/state/roster.py web/routes/api_rosters.py backend/billing/plans.py backend/engine/ai/autoplay.py tests/test_roster.py tests/test_rosters.py tests/test_autoplay.py
→ All checks passed

uv run ruff format --check backend/state/roster.py web/routes/api_rosters.py backend/billing/plans.py backend/engine/ai/autoplay.py tests/test_roster.py tests/test_rosters.py tests/test_autoplay.py
→ 7 files already formatted
```
