---
title: "CR-09 — Movement, charge and melee review"
parent: code-review
status: request-changes
source: ../code-review-plan.md#cr-09
tags: [requirements, code-review, atomic-review]
---

# CR-09 — Movement, charge and melee review

**Objective:** проверить, что melee units реально сближаются, charge возможен, melee damage логируется.

**Files:**
- Review: `backend/engine/scenario.py`
- Review: movement/charge/melee tests
- Output: `docs/reviews/YYYY-MM-DD/CR-09-movement-charge-melee.md`

**Steps:**
1. Прочитать tests вокруг movement/charge.
2. Проверить `_is_valid_move` и occupied-cell handling.
3. Проверить adjacent charge position, а не move onto target cell.
4. Проверить engagement distance.
5. Проверить melee target resolution по adjacency, не exact position only.
6. Проверить melee damage log format compatible with summary parser.
7. Запустить targeted tests/autoplay smoke.

**Acceptance:** melee-focused rosters не застревают без charge/fight damage.

---

---

## Execution Status

**Status:** Request Changes

**Review report target:** `docs/reviews/2026-05-09/CR-09-movement-charge-and-melee-review.md`

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
- **Important:** 3
- **Suggestions:** 0
- **Blocked by:** —
- **Report:** `docs/reviews/2026-05-09/CR-09-movement-charge-and-melee-review.md`
- **Completed at:** 2026-05-09

## Triage summary

- [CR-09 triage entry](../../reviews/2026-05-10/triage-summary.md#cr-09)
- Current release triage verdict: not-release-ready until open Critical/Important findings are fixed/re-reviewed or explicitly accepted where allowed.

## Regression evidence — Task 5.1 (charge destination + engagement identity)

Date: 2026-05-18

Fixed charge destination to enumerate all 8 adjacent cells (not just left/right X-axis). Same-X/different-Y scenarios now find valid adjacent cells. Melee combat scoped to opponent units only. Added 6 regression tests (charge cell avoidance, occupied alternate, same-X, opponent-only targeting, same-name mirrored units, runtime ID logging).

Verification: focused 10 passed, full 610 passed, 3 skipped. Ruff/format/diff-check clean.

## Regression evidence — Task 5.2 (melee target selection + damage logging)

Date: 2026-05-18

Melee combat now uses the combat engine via `simulate_unit_attack()` with melee weapons. Counter-attack also uses proper combat resolution. Damage logs use `hits ... for ... damage` pattern with runtime unit IDs. Added 3 regression tests (adjacent resolution, log format, same-name attribution).

Verification: scoped 19 passed, full 613 passed, 3 skipped. Ruff/format/diff-check clean.

## Regression evidence — Task 5.3 (terrain/LoS/cover blockers)

Date: 2026-05-18 (Phase 5 checkpoint)

set_terrain() now invalidates LoS cache. Cover argument order fixed in scenario shooting (target first). AP0 cover cap: SV3+ with cover vs AP0 stays at SV3+ (SV2+ unaffected). Added 9 regression tests.

Phase 5 closed: 22 scoped passed, 622 full passed. Ruff/format/diff-check clean.

## Superseding evidence — Task 5.2 CR — 2026-05-19

Verdict: REQUEST CHANGES. Task 5.2 is not ready to close.

Behavior observed:
- Adjacent melee resolves and opponent-only target scoping works in the deterministic probe; friendly adjacent unit remains undamaged.
- Blocking: `_resolve_melee_combat()` logs `hits ... for ... damage in melee`, but `_parse_log_events()` only parses `hits ... for ... damage`; the authoritative melee hit line becomes generic `info`.
- Blocking: same-name melee damage attribution is not proven non-name-based because parsed events lose the attacker runtime ID and only retain a target-side damage event.
- Blocking: `git diff --check` for the claimed touched set fails on `tests/test_result_screen.py` CRLF/trailing-whitespace lines.

Verification:
- `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_scenario.py tests/test_result_screen.py tests/test_movement.py -q` → 19 passed in 0.72s.
- `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/ -q` → 626 passed, 3 skipped, 60 warnings in 49.02s.
- `uv run ruff check backend/engine/scenario.py tests/test_movement.py tests/test_scenario.py tests/test_result_screen.py` → All checks passed.
- `uv run ruff format --check backend/engine/scenario.py tests/test_movement.py tests/test_scenario.py tests/test_result_screen.py` → 4 files already formatted.
- `git diff --check -- backend/engine/scenario.py tests/test_movement.py tests/test_scenario.py tests/test_result_screen.py docs/remediation/task-05-02-fix-melee-target-selection-and-damage-logging.md docs/remediation/remediation-plan.md docs/remediation/index.md` → failed on `tests/test_result_screen.py` CRLF/trailing whitespace.

## Superseding evidence — Task 5.3 CR — 2026-05-19

Verdict: REQUEST CHANGES for closure metadata only. Terrain/LoS/cover behavior passes, but Task 5.3 cannot claim Phase 5 checkpoint completion while Task 5.2 remains `changes_requested`.

Behavior observed:
- `set_terrain()` invalidates the LoS cache.
- Scenario shooting calls `_has_cover()` with defender/target position first and shooter position second.
- AP0 cover cap uses pre-cover save state in both runtime and expected-value save paths.

Verification:
- `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_terrain.py tests/test_scenario.py -q` → 13 passed in 0.49s.
- `uv run python -m pytest tests/ -q` → 626 passed, 3 skipped, 60 warnings in 50.82s.
- `uv run ruff check backend/state/map.py backend/engine/combat.py backend/engine/scenario.py tests/test_terrain.py` → All checks passed.
- `uv run ruff format --check backend/state/map.py backend/engine/combat.py backend/engine/scenario.py tests/test_terrain.py` → 4 files already formatted.
- `git diff --check -- backend/state/map.py backend/engine/combat.py backend/engine/scenario.py tests/test_terrain.py` → clean.


- Task 5.2 re-check FIXED (2026-05-19): `_parse_log_events` parses melee hit lines as structured `fight` events with runtime IDs; same-name attribution regressions added; scoped/full/ruff/format/diff gates green.
