# Code review — Task 3.1: Fix natural 6 / Lethal Hits semantics

Date: 2026-05-17
Reviewer: Hermes
Task file: `docs/remediation/task-03-01-fix-natural-6-lethal-hits-semantics.md`

## Verdict

REQUEST CHANGES → FIXED 2026-05-17

## Resolution

All findings resolved.

### Finding 1 — Lethal Hits auto-wound incorrectly triggered Devastating Wounds (Fixed)

- `_resolve_wound_chain` now synthesizes auto-wounds with `is_crit=False` (not `True`).
- Devastating Wounds only triggers on actual Critical Wound rolls per 10e — auto-wounds from Lethal Hits are not critical wounds.
- Added regression test `test_lethal_hits_with_devastating_wounds_no_save_bypass`: weapon with both `lethal_hits` + `devastating_wounds`, save=6 → 0 damage (save applies).
- Deterministic probe confirmed: `lethal_dev_6_save6_expected0 0`

### Finding 2 — `git diff --check` failed on touched files (Fixed)

- Applied `sed -i 's/\r$//'` to touched Python files (CRLF normalization).
- `git diff --check -- backend/engine/combat.py backend/engine/modifiers.py tests/test_combat.py tests/test_modifiers.py` now clean.

### Re-check results

```
$ uv run python -m pytest tests/test_combat.py tests/test_modifiers.py -q
35 passed in 10.52s

$ uv run python -m pytest tests/ -q
551 passed, 3 skipped, 38 warnings in 58.05s

$ uv run ruff check backend/engine/combat.py backend/engine/modifiers.py tests/test_combat.py tests/test_modifiers.py
All checks passed!

$ uv run ruff format --check backend/engine/combat.py backend/engine/modifiers.py tests/test_combat.py tests/test_modifiers.py
4 files already formatted

$ git diff --check -- backend/engine/combat.py backend/engine/modifiers.py tests/test_combat.py tests/test_modifiers.py
(clean)
```
