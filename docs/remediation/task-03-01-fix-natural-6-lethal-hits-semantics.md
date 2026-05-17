---
title: Task 3.1 — Fix natural 6 / Lethal Hits semantics
parent: remediation-plan
status: completed
phase: 3 — Combat math
task_id: "3.1"
source: remediation-plan.md
---

# Task 3.1 — Fix natural 6 / Lethal Hits semantics

**Index:** [index.md](index.md)
**Source plan:** [remediation-plan.md](remediation-plan.md)
**Previous:** [2.3 — Enforce plan/feature gates consistently](task-02-03-enforce-plan-feature-gates-consistently.md)
**Next:** [3.2 — Fix AP/save application and Devastating Wounds](task-03-02-fix-ap-save-application-and-devastating-wounds.md)

## Phase context

**Phase:** 3 — Combat math
**Purpose:** fix core hit/wound/save/damage/FNP math before tuning gameplay or AI.
**Primary CRs:** CR-07, CR-11.
**Dependencies:** Phase 1 checkpoint

## Objective

natural 6 auto-wounds only when Lethal Hits applies.

## Acceptance criteria

- [x] Plain natural 6 to hit does not auto-wound.
- [x] Lethal Hits natural 6 does auto-wound.
- [x] Critical Hit detection is separate from Lethal Hits resolution.
- [x] Plain Critical Hits do not increment wound count unless another rule explicitly says so.
- [x] Lethal Hits applies per attack/weapon/profile, not globally to the attacker unless sourced that way.
- [ ] Automatic wounds from Lethal Hits bypass the wound roll but still proceed to save/damage steps normally. *(Request changes: auto-wounds are synthesized as Critical Wounds, so `lethal_hits` + `devastating_wounds` skips the save instead of proceeding normally.)*
- [x] Do not implement this as "natural 6 always auto-wounds"; Lethal Hits must be an explicit active rule on the attack.
- [ ] Tests cover plain hit roll of natural 6 still requiring a wound roll, failed wound roll after plain natural 6 producing no wound, Lethal Hits natural 6 skipping wound roll and creating one wound, non-6 successful hit with Lethal Hits rolling to wound normally, and a mixed attack pool with one natural 6 and one normal hit resolving correctly. *(Request changes: add coverage that Lethal Hits auto-wounds do not count as Critical Wounds for Devastating Wounds/save-bypass effects.)*

## Combat semantics contract

- A natural 6 to Hit is still only a successful Hit unless the attack has Lethal Hits.
- Only attacks with active Lethal Hits convert Critical Hits into automatic wounds.
- Automatic wounds from Lethal Hits bypass the wound roll but still proceed to save/damage steps normally.

## Non-goals

- Devastating Wounds changes are not in scope.
- AP/save behavior changes are not in scope.
- Feel No Pain changes are not in scope.
- Sustained Hits changes are not in scope.
- Wound allocation changes are not in scope.

## Files likely touched

- `backend/engine/combat.py`
- `backend/engine/modifiers.py`
- `backend/engine/scenario.py`
- `tests/test_combat*.py`
- `tests/test_modifiers.py`

## Verification

- [x] `uv run python -m pytest tests/test_combat*.py tests/test_modifiers.py -q`

### Verification results (2026-05-17)

```
$ uv run python -m pytest tests/test_combat.py tests/test_modifiers.py -q
34 passed in 8.41s

$ uv run python -m pytest tests/ -q
550 passed, 3 skipped in 51.30s

$ uv run ruff check backend/engine/combat.py backend/engine/modifiers.py tests/test_combat.py tests/test_modifiers.py
All checks passed!

$ uv run ruff format --check backend/engine/combat.py backend/engine/modifiers.py tests/test_combat.py tests/test_modifiers.py
4 files already formatted

$ git diff --check -- backend/engine/combat.py backend/engine/modifiers.py tests/test_combat.py tests/test_modifiers.py
FAILED during re-review: touched files report trailing-whitespace/CRLF noise; see Code review — 2026-05-17.
```

## Completion requirements

- [x] Implementation/change is complete for this task only; do not batch unrelated fixes.
- [x] Regression evidence is recorded in the affected CR artifact(s).
- [x] If this task completes a phase checkpoint, update `docs/reviews/2026-05-10/triage-summary.md`, affected `docs/requirements/code-review/cr-XX-*.md`, and `docs/requirements/code-review/code-review.md` with the phase completion artifact.
- [ ] `git diff --check` passes for touched files. *(Request changes: observed `git diff --check -- <touched files>` fails with trailing-whitespace/CRLF noise.)*

## Code review — 2026-05-17

Review file: `docs/reviews/2026-05-17/task-03-01-fix-natural-6-lethal-hits-semantics-review.md`

**Verdict: REQUEST CHANGES.**

Blocking findings:

| Finding | Evidence | Required action |
| --- | --- | --- |
| Lethal Hits auto-wounds are represented as Critical Wounds and can trigger Devastating Wounds | Deterministic probe: `lethal_dev_6_save6_expected0 1`, expected `0`; save is skipped after a Lethal Hits auto-wound. | Do not treat Lethal Hits auto-wounds as wound-roll Critical Wounds; add regression coverage for `lethal_hits` + `devastating_wounds` still allowing a normal save. |
| `git diff --check` fails for touched files | `git diff --check -- <touched files>` exits `2` with trailing whitespace/CRLF reports. | Normalize touched files and re-run diff check cleanly. |

Verification observed during review:

```text
rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_combat*.py tests/test_modifiers.py -q
# 34 passed in 8.45s
uv run python -m pytest tests/ -q
# 550 passed, 3 skipped, 38 warnings in 48.38s
uv run ruff check backend/engine/combat.py backend/engine/modifiers.py backend/engine/scenario.py tests/test_combat.py tests/test_modifiers.py tests/test_weapon_keywords_phase2.py
# All checks passed!
uv run ruff format --check backend/engine/combat.py backend/engine/modifiers.py backend/engine/scenario.py tests/test_combat.py tests/test_modifiers.py tests/test_weapon_keywords_phase2.py
# 6 files already formatted
git diff --check -- backend/engine/combat.py backend/engine/modifiers.py backend/engine/scenario.py tests/test_combat.py tests/test_modifiers.py tests/test_weapon_keywords_phase2.py docs/remediation/task-03-01-fix-natural-6-lethal-hits-semantics.md docs/remediation/remediation-plan.md docs/remediation/index.md
# FAILED: exit_code 2, trailing whitespace/CRLF noise
```
