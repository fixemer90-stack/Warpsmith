---
title: "CR-14 — Autoplay, replay and result review"
parent: code-review
status: request-changes
source: ../code-review-plan.md#cr-14
tags: [requirements, code-review, atomic-review]
---

# CR-14 — Autoplay, replay and result review

**Objective:** проверить full simulation pipeline: setup → auto-play → replay storage → result summary.

**Files:**
- Review: `backend/engine/ai/autoplay.py`
- Review: `backend/engine/replay.py`
- Review: `web/routes/api_replays.py`
- Review: `web/static/scenario_setup.js`
- Review: `web/static/replay_viewer.js`
- Review: `web/static/result_chart.js`
- Output: `docs/reviews/YYYY-MM-DD/CR-14-autoplay-replay-result.md`

**Steps:**
1. Проверить game_id serialization and redirect flow.
2. Проверить replay persistence JSON columns.
3. Проверить `_snapshot_state` includes units, positions, VP, map dimensions.
4. Проверить `_build_summary` parsing kills/damage/charges.
5. Проверить result winner fallback.
6. Проверить round viewer dynamic grid size.
7. Запустить replay/result tests and one TestClient E2E auto-play.

**Acceptance:** generated/saved rosters can run simulation and open `/result/{game_id}` with meaningful summary.

---

---

## Execution Status

**Status:** Request Changes

**Review report target:** `docs/reviews/2026-05-09/CR-14-autoplay-replay-and-result-review.md`

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
- **Completed at:** 2026-05-09T23:13:16+03:00
- **Verification:** `62 passed, 7 warnings in 11.41s`; custom replay/result probes confirmed game_id overwrite, stale final VP snapshots, duplicate-name summary attribution, VP parser mismatch, and result charge attribution gap.

## Triage summary

- [CR-14 triage entry](../../reviews/2026-05-10/triage-summary.md#cr-14)
- Current release triage verdict: not-release-ready until open Critical/Important findings are fixed/re-reviewed or explicitly accepted where allowed.

## Regression evidence — Task 0.1 (runtime unit identity)

**2026-05-16.** Fixed "duplicate-name summary attribution" finding:

1. **`_build_summary()`** — Now uses `strip_event_identity()` to extract authoritative
   `actor_id`/`target_id` from the `[actor_id=p1:Boyz:0; target_id=p2:Boyz:0]`
   suffix in log lines. Builds `runtime_id → player_id` map. Correct attribution
   even when both players have identically-named units (e.g. both field "Boyz").
   Fallback to display-name lookup for log lines without identity suffix.

2. **`_parse_log_events()`** — Updated all 17 patterns to strip identity suffix
   and use `meta.get("actor_id"/"target_id", …)` for `ReplayEvent` construction.
   Replay events now carry stable runtime IDs alongside display names.

3. **`RosterState.units`** — `dict[str, Unit]` → `list[tuple[str, Unit]]`.
   Duplicate unit names within a roster are representable end-to-end.

Verification: `uv run python -m pytest tests/ -q` → 471 passed, 3 skipped, 0 failures.
`ruff check` → All checks passed.

## Regression evidence — Task 0.2 (canonical GameState serializer)

**2026-05-16.** Two divergent `_snapshot_state` implementations consolidated into single
canonical `snapshot_game_state()` in `backend/state/game_state.py`. Both `autoplay.py`
and `replay.py` now delegate to it. Round snapshots and final snapshots share identical
shape. Unit records include `runtime_unit_id` as authoritative `id`, `player_id`,
`current_wounds`/`max_wounds`, and all status flags. VP at top-level only (not per-unit).

7 new tests: identical shape autoplay/replay, runtime_id keys, display_name preserved,
player_id per unit, mirrored-name distinct IDs, VP consistency, status flags.
Full suite: 478 passed, 0 failures.

## Regression evidence — Task 0.3 (non-destructive DB/replay)

**2026-05-16.** `DROP TABLE IF EXISTS replays` removed. `save_replay()` non-destructive by default.
`game_id` UUID-based. 6 new tests. 484 passed.
