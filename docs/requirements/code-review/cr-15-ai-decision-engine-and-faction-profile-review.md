---
title: "CR-15 — AI decision engine and faction profile review"
parent: code-review
status: request-changes
source: ../code-review-plan.md#cr-15
tags: [requirements, code-review, atomic-review]
---

# CR-15 — AI decision engine and faction profile review

**Objective:** проверить greedy decisions, faction AI profiles, behavior activation, deployment integration.

**Files:**
- Review: `backend/engine/ai/`
- Review: `wiki/factions/*.md`
- Review: AI tests
- Output: `docs/reviews/YYYY-MM-DD/CR-15-ai-decision-faction-profiles.md`

**Steps:**
1. Проверить decision tests first.
2. Проверить `load_profile`, cache isolation, fuzzy faction matching.
3. Проверить phase weights and behavior activation.
4. Проверить target multipliers for shooting/charge.
5. Проверить deployment profiles are loaded before deploy_game.
6. Проверить melee/ranged faction-specific movement behavior.
7. Запустить AI tests.

**Acceptance:** Orks/Tau/AdMech behavior profiles реально используются в autoplay decisions.

---

---

## Execution Status

**Status:** Request Changes

**Review report target:** `docs/reviews/2026-05-09/CR-15-ai-decision-engine-and-faction-profile-review.md`

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
- **Suggestions:** 0
- **Blocked by:** —
- **Completed at:** 2026-05-09T23:22:36+03:00

### Finding summary

- F3.1 greedy decision engine is not used by live Scenario/autoplay phases.
- Faction behavior `action_override` is retrieved but never applied.
- `choose_action_with_faction_ai()` does not set `ctx.faction_profile`, so target-priority scoring remains disabled in the wrapper.
- Target-priority multipliers below 1.0 are ignored.
- `get_weights()` mutates behavior cooldown/one-shot state while acting like a getter.
- Live autoplay deployment passes `objectives=[]`.
- Tests pass but do not prove live faction-specific decisions.

## Triage summary

- [CR-15 triage entry](../../reviews/2026-05-10/triage-summary.md#cr-15)
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
