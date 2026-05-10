---
title: "CR-08 — Game state and phase machine review"
parent: code-review
status: request-changes
source: ../code-review-plan.md#cr-08
tags: [requirements, code-review, atomic-review]
---

# CR-08 — Game state and phase machine review

**Objective:** проверить 10th Edition game loop, phase transitions, round counting, CP, battle-shock.

**Files:**
- Review: `backend/state/game_state.py`
- Review: `backend/engine/scenario.py`
- Review: phase/game-loop tests
- Output: `docs/reviews/YYYY-MM-DD/CR-08-game-state-phase-machine.md`

**Steps:**
1. Проверить enum фаз: Command, Movement, Shooting, Charge, Fight.
2. Проверить `max_phases_per_round` и off-by-one по `max_rounds`.
3. Проверить CP старт/генерацию/cap.
4. Проверить battle-shock timing and reset.
5. Проверить `is_engaged`, `has_advanced`, death state transitions.
6. Проверить game over logic.
7. Запустить phase/game-loop tests.

**Acceptance:** нет возврата к 6 фазам, VP-cap early game over, CP=6 или premature round ending.

---

---

## Execution Status

**Status:** Request Changes

**Review report target:** `docs/reviews/YYYY-MM-DD/CR-08-game-state-and-phase-machine-review.md`

### Status checklist

- [x] Scope confirmed
- [x] Requirements/specs reviewed
- [x] Tests reviewed first
- [x] Production code reviewed
- [x] Correctness checked
- [x] Readability checked
- [x] Architecture checked
- [x] Security checked
- [x] Performance checked
- [x] Verification commands executed
- [x] Findings report written
- [x] Triage status updated in `docs/requirements/code-review/code-review.md`

### Result

- **Verdict:** Request Changes
- **Critical:** 3
- **Important:** 4
- **Suggestions:** 1
- **Blocked by:** —
- **Report:** `docs/reviews/2026-05-09/CR-08-game-state-and-phase-machine-review.md`
- **Completed at:** 2026-05-09

## Triage summary

- [CR-08 triage entry](../../reviews/2026-05-10/triage-summary.md#cr-08)
- Current release triage verdict: not-release-ready until open Critical/Important findings are fixed/re-reviewed or explicitly accepted where allowed.
