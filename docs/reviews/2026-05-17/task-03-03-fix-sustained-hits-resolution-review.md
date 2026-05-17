# Task 3.3 — Fix Sustained Hits resolution — Review

Date: 2026-05-17
Task: `docs/remediation/task-03-03-fix-sustained-hits-resolution.md`
Verdict: REQUEST CHANGES → FIXED 2026-05-17

## Summary

The Sustained Hits implementation behavior passes focused tests and deterministic probes: extra hits are spawned as downstream wound/save/damage chains, extra hits are normal non-critical hits, and Sustained Hits coexists with Lethal Hits and Devastating Wounds correctly.

Task closure is now complete: required CR-11 regression evidence and Phase 3 completion artifacts were added and synced.

## Findings

### Important 1 — Missing CR-11 Task 3.3 regression evidence

Task 3.3 lists Primary CRs: CR-07 and CR-11.

Observed:
- `docs/requirements/code-review/cr-07-combat-engine-review.md` contains `Task-03-03 Resolution`.
- `docs/requirements/code-review/cr-11-terrain-cover-and-los-review.md` contains Task 3.2 evidence only; there is no Task 3.3 regression evidence section.

Required fix: add Task 3.3 regression evidence to CR-11 with latest test/probe results, or explicitly document why CR-11 has no Task 3.3 evidence despite being listed as a Primary CR.

### Important 2 — Missing Phase 3 completion artifact

Task 3.3 is the last Phase 3 task. Its completion requirement says the phase checkpoint artifacts must be updated:

- `docs/reviews/2026-05-10/triage-summary.md`
- affected CR artifacts
- `docs/requirements/code-review/code-review.md`

Observed:
- `docs/reviews/2026-05-10/triage-summary.md` has no Phase 3 completion entry.
- `docs/requirements/code-review/code-review.md` has no Phase 3 completion entry.
- Affected CR metadata is only partially updated.

Required fix: add/sync the Phase 3 completion artifact across the required metadata surfaces, including latest verification results and remaining blockers/debt.

## Positive behavior checks

Sustained Hits code path:
- `_resolve_attack_chain()` resolves the original hit, then loops over `critical_effect.extra_attacks` and calls `_resolve_wound_chain(..., auto_wound=False)` for each extra hit.
- `handle_critical_hit()` returns `extra_attacks` only for Critical Hits with `sustained_hits` modifiers.
- Extra hits are not Critical Hits and do not recursively trigger Sustained Hits.

Deterministic probe results:

```text
no_crit_sh1_damage=1
crit_sh1_two_hits_one_saved_or_failed_damage=1
crit_sh2_three_hits_two_damage=2
sh_lethal_original_auto_extra_normal_damage=2
sh_dev_extra_noncrit_save_applies_damage=1
```

## Re-check commands run

```bash
$ rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_modifiers.py tests/test_combat*.py -q
50 passed in 10.38s

$ uv run python -m pytest tests/ -q
583 passed, 3 skipped, 60 warnings in 56.40s

$ uv run ruff check backend/engine/combat.py backend/engine/modifiers.py tests/test_combat.py tests/test_modifiers.py
All checks passed!

$ uv run ruff format --check backend/engine/combat.py backend/engine/modifiers.py tests/test_combat.py tests/test_modifiers.py
4 files already formatted

$ git diff --check -- backend/engine/combat.py backend/engine/modifiers.py tests/test_combat.py tests/test_modifiers.py docs/remediation/task-03-03-fix-sustained-hits-resolution.md docs/remediation/remediation-plan.md docs/remediation/index.md docs/requirements/code-review/cr-07-combat-engine-review.md docs/requirements/code-review/cr-11-terrain-cover-and-los-review.md docs/reviews/2026-05-10/triage-summary.md docs/requirements/code-review/code-review.md
clean
```

## Required before approval — FIXED 2026-05-17

- [x] Task 3.3 regression evidence added to CR-11.
- [x] Phase 3 completion artifact synced in `triage-summary.md`, affected CR artifacts, and `code-review.md`.
- [x] `task-03-03-fix-sustained-hits-resolution.md` restored to `status: completed`.

## Resolution — 2026-05-17

- Added `Regression evidence — Task 3.3` to CR-11 with latest focused/full-suite results and deterministic probe output.
- Added Phase 3 completion artifact to `docs/reviews/2026-05-10/triage-summary.md`.
- Added Phase 3 checkpoint evidence to CR-07, CR-11, and `docs/requirements/code-review/code-review.md`.
- Restored Task 3.3 status to completed and re-checked visible index status.

### Re-check results

```bash
rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_modifiers.py tests/test_combat*.py -q
# 50 passed in 10.38s
uv run python -m pytest tests/ -q
# 583 passed, 3 skipped, 60 warnings in 56.40s
uv run ruff check backend/engine/combat.py backend/engine/modifiers.py tests/test_combat.py tests/test_modifiers.py
# All checks passed!
uv run ruff format --check backend/engine/combat.py backend/engine/modifiers.py tests/test_combat.py tests/test_modifiers.py
# 4 files already formatted
git diff --check -- <Task 3.3 touched docs/code files>
# clean
```
