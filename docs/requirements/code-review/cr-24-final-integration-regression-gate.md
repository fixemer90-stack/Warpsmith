---
title: "CR-24 — Final integration regression gate"
parent: code-review
status: request-changes
source: ../code-review-plan.md#cr-24
tags: [requirements, code-review, atomic-review]
---

# CR-24 — Final integration regression gate

**Objective:** финально подтвердить, что review/fix cycle не сломал продукт.

**Files:**
- Scope: whole repo
- Output: `docs/reviews/YYYY-MM-DD/CR-24-final-regression-gate.md`

**Steps:**
1. Выполнить `uv run ruff check .`.
2. Выполнить `uv run ruff format --check .`.
3. Выполнить `node -c web/static/team_builder.js`.
4. Выполнить `node -c web/static/scenario_setup.js`.
5. Выполнить `node -c web/static/battlefield_map.js`.
6. Выполнить `uv run python -m pytest tests/ -q`.
7. Запустить server без reload и проверить `/api/health`.
8. Browser smoke key pages: `/`, `/team-builder`, `/scenario-setup`, `/my-rosters`, `/result/<known_or_generated_game_id>` if available.
9. Записать final verdict and remaining accepted debt.

**Acceptance:** final gate report создан; release readiness verdict explicit.

---

---

## Execution Status

**Status:** Request Changes

**Review report target:** `docs/reviews/2026-05-10/CR-24-final-integration-regression-gate.md`

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

- **Verdict:** Request Changes — executable gates pass, but release readiness is blocked by unresolved/untriaged CR debt (37 prior Critical + 111 prior Important) and a reproduced result VP consistency issue.
- **Critical:** 1
- **Important:** 1
- **Suggestions:** 1
- **Blocked by:** unresolved Critical/Important CR debt, result final VP snapshot mismatch
- **Completed at:** 2026-05-10

## Triage summary

- [CR-24 triage entry](../../reviews/2026-05-10/triage-summary.md#cr-24)
- Current release triage verdict: not-release-ready until open Critical/Important findings are fixed/re-reviewed or explicitly accepted where allowed.

## Regression evidence — Task 4.1 (5-phase 10e loop invariants)

**2026-05-17.** Locked the runtime phase loop to the canonical Warhammer 40k 10e order: Command → Movement → Shooting → Charge → Fight.

Changes:
- Added `GAME_PHASE_ORDER` as the shared canonical phase order in `backend/state/game_state.py`.
- Updated `GameState.next_phase()` and `Scenario.run_round()` to consume that shared order instead of duplicated hardcoded phase-count logic.
- Added regression coverage for enum size/order, shared phase-order export, scenario full-round phase logs, replay/autoplay snapshot phase names, and autoplay full-turn five-phase execution.
- Confirmed no runtime Morale/Psychic/End phase enum members are present and battle-shock remains a Command phase step.

```bash
$ rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_game_state.py tests/test_scenario.py tests/test_autoplay.py tests/test_replay.py -q
80 passed, 12 warnings in 8.20s

$ uv run python -m pytest tests/ -q
593 passed, 3 skipped, 60 warnings in 53.49s

$ uv run ruff check backend/state/game_state.py backend/engine/scenario.py tests/test_game_state.py tests/test_scenario.py tests/test_autoplay.py tests/test_replay.py
All checks passed!

$ uv run ruff format --check backend/state/game_state.py backend/engine/scenario.py tests/test_game_state.py tests/test_scenario.py tests/test_autoplay.py tests/test_replay.py
6 files already formatted

$ git diff --check -- backend/state/game_state.py backend/engine/scenario.py tests/test_game_state.py tests/test_scenario.py tests/test_autoplay.py tests/test_replay.py
(clean)
```
