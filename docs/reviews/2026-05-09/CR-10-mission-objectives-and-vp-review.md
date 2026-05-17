---
title: "CR-10 — Mission, objectives and VP review"
parent: code-review
status: request-changes
date: 2026-05-09
tags: [review, code-review, mission, objectives, vp]
---

# CR-10 — Mission, objectives and VP review

## Verdict

REQUEST CHANGES

The mission registry normalization, dynamic objective placement, and OC contest logic are mostly working, but the scoring pipeline is still not safe to approve. The main blocker is that mission scoring updates `Scenario.vp_tracker` but does not reliably update `PlayerState.victory_points`, so API/result/replay consumers can still show 0 VP / no winner even when mission scoring awarded VP. End-game logic also still uses stale VP-cap and army-wipe paths, which contradicts the current project rule that the game ends by rounds only.

## Scope

Reviewed:

- `backend/state/mission.py`
- `backend/engine/scenario.py`
- `backend/engine/ai/autoplay.py`
- Mission/VP/result-related tests:
  - `tests/test_mission.py`
  - `tests/test_scenario.py`
  - `tests/test_autoplay.py`
  - `tests/test_result_screen.py`

Required checks from CR-10:

1. Mission registry and `create_mission` normalization.
2. Objective placement scales with map size.
3. OC-based objective control within 3 inches.
4. `kill_points` missions do not require objective scoring for VP but keep objectives for movement.
5. Battle Ready +10 VP timing.
6. Winner/draw logic.
7. Mission tests.

## Verification commands

```bash
rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_mission.py tests/test_scenario.py tests/test_autoplay.py tests/test_result_screen.py -q
```

Result:

```text
49 passed in 9.96s
```

Additional probes were run with `python3` in the repository root to verify normalization, OC control, command scoring synchronization, end-game conditions, repeated kill-points scoring, and Battle Ready replay snapshot behavior.

## Findings

### Critical-1 — Command-phase scoring updates `VPTracker` but often leaves `PlayerState.victory_points` at 0

Files:

- `backend/engine/scenario.py`
- `backend/state/mission.py`
- `backend/engine/ai/autoplay.py`

Evidence:

`Scenario._command_phase()` calls:

```python
apply_scoring(self.state, self.state.mission, self.vp_tracker)
```

But the block that copies `vp_tracker` values into `player.victory_points` is indented under:

```python
for player_id, profile in self._faction_profiles.items():
```

If no faction AI profiles are loaded, that loop does not run, so mission VP is never copied into the player state and no VP log line is emitted.

Probe result:

```text
COMMAND_VP_TRACKER {1: 5, 2: 0} PLAYER_VP {'1': 0, '2': 0} VP_LOGS []
```

Impact:

- The actual mission scorer awards VP.
- The UI/result/replay-facing `PlayerState.victory_points` remains 0.
- `AutoPlayResult.to_dict()` and `_build_summary()` determine winner from `PlayerState.victory_points`, so winner can be `None` even after scoring happened.
- This directly violates CR-10 acceptance: VP can still appear to stay 0 because the visible state is stale.

Recommendation:

Move the VP-to-player-state synchronization out of the faction-profile loop. Make it run once after `apply_scoring()` for every player, regardless of AI profile availability. Add a regression test that puts one unit on a Take and Hold objective, runs command phase with empty faction profiles, and asserts both `vp_tracker.total` and `PlayerState.victory_points` changed.

### Critical-2 — Mission end-game logic still ends games by VP cap and army wipe, not by rounds only

Files:

- `backend/state/mission.py`
- `backend/engine/scenario.py`

Evidence:

`check_end_game()` still returns terminal `GameResult` for:

- `vp.total[player_num] >= 100`
- an army being wiped
- `round_num >= mission.config.max_rounds`

Probe result:

```text
CHECK_VP_CAP_R3 vp_cap
CHECK_ARMY_WIPE_R2 army_wiped
CHECK_MAX_ROUND_5 army_wiped
```

The max-round probe returned `army_wiped` first, proving army wipe takes precedence over the round-only ending condition.

Impact:

- Current project convention says game over is by rounds only.
- A player can win before Battle Ready VP is applied.
- A replay/result can end before the intended round horizon.
- Winner/draw logic becomes inconsistent between `mission.check_end_game()`, `GameState.is_game_over`, `autoplay._check_game_end()`, and result summary code.

Recommendation:

Align all end-game checks with the current rule: rounds only. If army-wipe or VP-cap data is still useful, record it as a log/summary flag, not as a terminal condition. Add tests that a VP cap and an army wipe before max rounds do not end the game.

### Important-1 — Battle Ready +10 VP is applied after round snapshots, so replay/end-state VP is stale

Files:

- `backend/engine/ai/autoplay.py`

Evidence:

`run_auto_game()` captures the final `round_log['end_state']` before applying Battle Ready VP:

```python
end_state = _snapshot_state(state)
...
# later
for player in state.players.values():
    player.victory_points += 10
```

Probe result:

```text
BR_STATE_VP {'1': 10, '2': 10}
BR_LAST_END_STATE_VP {'1': 0, '2': 0}
BR_LOG_AFTER_ROUNDS ['A roster gains 10 Battle Ready VP (total: 10)', 'B roster gains 10 Battle Ready VP (total: 10)']
```

Impact:

- Final `game_state` has Battle Ready VP.
- The last replay round `end_state` does not.
- Any round viewer/result screen that relies on round snapshots can show final VP as 0 or miss the +10.

Recommendation:

Apply Battle Ready before the final replay snapshot, or append/update a final snapshot/event after Battle Ready is awarded. Add a regression test asserting that final round `end_state['victory_points']` matches `game_state.players[*].victory_points`.

### Important-2 — Kill-points scoring re-adds cumulative destroyed percentage every Command phase

Files:

- `backend/state/mission.py`

Evidence:

`score_kill_points()` returns percentage of the opponent army destroyed. `apply_scoring()` then adds that full percentage to the `VPTracker` every time scoring is applied. A destroyed enemy unit stays destroyed, so the same 100% can be awarded repeatedly.

Probe result:

```text
KILL_POINTS_REPEATED {1: [100, 100, 100], 2: [0, 0, 0]} {1: 300, 2: 0}
```

Impact:

- VP can exceed the apparent 100 VP cap by repeated scoring.
- A player receives points for the same destroyed units every scoring interval.
- The behavior is not documented as intentional and conflicts with VP cap/end-game assumptions.

Recommendation:

Decide whether kill-points scoring is cumulative total or per-round delta. If cumulative total, do not add the full value every round; store/report it as current score. If per-round delta, track which destroyed units were already scored and only add newly destroyed units.

### Important-3 — Winner/draw tie-break code is internally inconsistent

Files:

- `backend/state/mission.py`

Evidence:

On max rounds, `check_end_game()` calculates:

```python
leader = vp.leader()
if vp.is_tied():
    leader = _resolve_tie(state)
return GameResult(
    winner=_int_to_player(leader) if not vp.is_tied() else None,
    ...
)
```

If VP is tied, `_resolve_tie(state)` is called, but its result is discarded because `winner` is set to `None` whenever `vp.is_tied()` remains true.

Impact:

- The code advertises tie-breakers but always returns a draw for VP ties.
- Tests do not verify tie behavior.
- This is easy to misread and can cause future winner/draw regressions.

Recommendation:

Choose one intended behavior:

- If tied VP must be a draw, remove `_resolve_tie()` from this path and test draw behavior explicitly.
- If tie-breakers are intended, return the resolved winner and test killed-points/objective tie-breaks.

### Important-4 — Mission tests pass but do not catch the blocking VP/result bugs

Files:

- `tests/test_mission.py`
- `tests/test_scenario.py`
- `tests/test_autoplay.py`
- `tests/test_result_screen.py`

Evidence:

The focused suite passed:

```text
49 passed in 9.96s
```

But probes still found:

- `VPTracker` updated while `PlayerState.victory_points` stayed 0.
- Early `vp_cap` and `army_wiped` terminal paths still active.
- Battle Ready missing from final round snapshots.
- Kill-points scoring could add 100 VP repeatedly.

Some existing tests are too permissive. Example: kill-points tests use `>= 0` for damaged or killed cases, which cannot fail for many broken implementations.

Recommendation:

Add explicit regression tests for:

- Command phase updates both `VPTracker` and player-visible VP with no faction profiles.
- Result/replay winner derives from final visible VP.
- Battle Ready VP appears in final snapshot and result summary.
- VP cap and army wipe do not end the game before max rounds if round-only ending is the intended rule.
- Kill-points scoring is delta-based or otherwise documented and capped.

## Positive checks

The following CR-10 checks passed in direct probes:

### Mission name normalization

`create_mission()` handles spaces and hyphens:

```text
MISSION Only War True Only War progressive 3
MISSION only-war True Only War progressive 3
MISSION take-and-hold True Take and Hold standard 5
MISSION purge-the-foe True Purge the Foe kill_points 5
MISSION purge the foe True Purge the Foe kill_points 5
```

### Objective placement scales with map size

For a 60x44 map, dynamic objectives were placed inside the map:

```text
Take and Hold: [(30, 22), (15, 22), (45, 22), (30, 11), (30, 33)]
Only War: [(30, 22), (15, 22), (45, 22)]
Purge the Foe: [(30, 22), (15, 22), (45, 22), (30, 11), (30, 33)]
```

### OC-based objective control within 3 inches

Probe result:

```text
OC_RANGE3 p1 False
OC_TIE None True
OC_HIGHER p2 False
```

This confirms:

- A unit exactly 3 inches away controls an objective.
- Equal OC contests.
- Higher OC controls.

## Required changes before approval

1. Fix command-phase VP synchronization so player-visible VP is updated independently from faction AI profiles.
2. Align mission/game end checks with the round-only ending rule.
3. Ensure Battle Ready VP is included in final replay/result snapshots.
4. Clarify and fix kill-points scoring accumulation semantics.
5. Add regression tests for the above.

## Review metadata

- Review date: 2026-05-09
- Verdict: request-changes
- Critical findings: 2
- Important findings: 4
- Suggestions: 0
- Verification: `49 passed in 9.96s`
