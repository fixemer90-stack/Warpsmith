---
title: "CR-08 — Game state and phase machine review"
status: request-changes
review_task: CR-08
date: 2026-05-09
source: ../../requirements/code-review/cr-08-game-state-and-phase-machine-review.md
---

# CR-08 — Game state and phase machine review

## Verdict

REQUEST CHANGES / PHASE STATE INVARIANTS AND SCORING SYNC REQUIRED

The 10ed phase enuyg at exactly half-strength and for single-model wounded units.
- Mission VP is accumulated in `VPTracker` but can fail to propagate to `PlayerState.victory_points`, which is what result summaries and winner calculation use.
- Round 1 command/fight priority is not initialized by the normal Command phase flow.
- Auto-play still ends early on army wipe despite the project convention that game-over should be round-limit only.
- Engagement/fight activation state is asymmetric after a charge.

## Scope reviewed

- `backend/state/game_state.py`
- `backend/engine/scenario.py`
- `backend/state/mission.py`
- `backend/engine/ai/autoplay.py`
- `tests/test_game_state.py`
- `tests/test_phase_transitions.py`
- `tests/test_f2_7_battle_shock_cp_stratagems.py`
- `tests/test_autoplay.py`
- Warpsmith 10ed references loaded from local skill:
  - `game-phases-10ed.md`
  - `cp-rules-10ed.md`
  - `battle-ready-vp.md`
  - `parse-log-kill-phase.md`

## Automated checks run

```bash
uv run python -m pytest tests/test_game_state.py tests/test_phase_transitions.py tests/test_f2_7_battle_shock_cp_stratagems.py tests/test_autoplay.py -q
```

Result:

```text
41 passed in 5.78s
```

Additional probes:

```text
EXACT_HALF_BATTLE_SHOCKED True
SINGLE_MODEL_LT_HALF_WOUNDS_BATTLE_SHOCKED False
VP_TRACKER_TOTAL {1: 5, 2: 0}
PLAYER_VP {'1': 0, '2': 0}
LOG_VP_LINES []
AUTOPLAY_ARMY_WIPE_ENDS True
ROUND1_PRIORITY_FLAGS_AFTER_COMMAND {'1': False, '2': False}
```

## Findings

### Critical — Battle-shock eligibility is not 10ed-correct

Location:

- `backend/state/game_state.py:65-68`
- `backend/engine/scenario.py:732-762`
- `tests/test_f2_7_battle_shock_cp_stratagems.py:48-184`

Current code:

```python
@property
def is_above_half_strength(self) -> bool:
    return self.models_remaining > (self.models_total / 2)
```

`Scenario._battle_shock_tests()` tests units when `not unit.is_above_half_strength`.

This makes an exactly-half unit count as test-eligible. That is wrong for 10ed wording: Battle-shock tests are for units Below Half-strength, i.e. remaining models are less than half the starting models. At exactly half, the unit is not below half.

The current implementation also ignores the single-model wounded-unit rule: a single-model unit is Below Half-strength when its remaining wounds are less than half its starting wounds. Current code sees `models_remaining == models_total == 1`, so a wounded single-model unit never tests.

Verified with probe:

```text
EXACT_HALF_BATTLE_SHOCKED True
SINGLE_MODEL_LT_HALF_WOUNDS_BATTLE_SHOCKED False
```

Expected:

```text
EXACT_HALF_BATTLE_SHOCKED False
SINGLE_MODEL_LT_HALF_WOUNDS_BATTLE_SHOCKED True
```

Recommendation:

- Replace the property with explicit `is_below_half_strength` semantics.
- For multi-model units: `models_remaining < models_total / 2`.
- For single-model units: `current_wounds < max_wounds / 2`.
- Update tests to cover:
  - 1/2 models: no test.
  - 1/3 models: test.
  - single model 1/4 wounds: test.
  - single model 2/4 wounds: no test.

### Critical — Mission VP is not consistently propagated to `PlayerState.victory_points`

Location:

- `backend/engine/scenario.py:124-148`
- `backend/state/mission.py:241-250`
- `backend/engine/ai/autoplay.py:277-297`

`apply_scoring()` records VP into `Scenario.vp_tracker`, but the copy back into `PlayerState.victory_points` is incorrectly nested under the faction-profile loop:

```python
for player_id, profile in self._faction_profiles.items():
    ...
    # Also update PlayerState.victory_points for backwards compat
    for i, player_id in enumerate(self.state.players):
        ...
        player.victory_points += vp_gained
```

If `_faction_profiles` is empty, mission scoring happens but player VP remains 0. The UI/result summary and winner calculation use `PlayerState.victory_points`, so this can produce VP=0 and null/tie winner even though `VPTracker` scored objectives.

Verified with a `take_and_hold` command phase and no faction profiles:

```text
VP_TRACKER_TOTAL {1: 5, 2: 0}
PLAYER_VP {'1': 0, '2': 0}
LOG_VP_LINES []
```

Recommendation:

- Move the `PlayerState.victory_points` sync out of the faction-profile loop.
- Add a test that calls `_command_phase()` with no faction profiles and verifies both:
  - `vp_tracker.total[...]` changed.
  - `game_state.players[...].victory_points` changed.
- Ensure no double-counting when multiple faction-profile entries exist. Current `run_auto_game()` stores profiles by both player id and faction id, so a naively nested VP sync risks duplication.

### Critical — Round 1 command/fight priority is not initialized in normal phase flow

Location:

- `backend/state/game_state.py:219-251`
- `backend/engine/scenario.py:85-149`
- `backend/engine/scenario.py:637-663`
- `tests/test_phase_transitions.py:9-52`

`GameState._determine_command_priority()` exists, but the normal `Scenario._command_phase()` does not call it for round 1. `GameState.next_phase()` only calls `_determine_command_priority()` when wrapping from Fight to the next round's Command phase.

That means round 1 Fight phase normally has no priority player. `_fight_phase()` then falls back to dictionary order instead of the 10ed non-priority-first activation order.

Verified:

```text
ROUND1_PRIORITY_FLAGS_AFTER_COMMAND {'1': False, '2': False}
```

Recommendation:

- Initialize command priority at the start of Command phase if no priority has been assigned for the current round.
- Add an integration test that runs `Scenario.run_round()` from a fresh game and asserts that round 1 Fight has a valid one-player priority assignment before resolving activations.

### Important — Auto-play still ends early on army wipe

Location:

- `backend/engine/ai/autoplay.py:300-317`
- `backend/engine/ai/autoplay.py:482-484`

Project convention/memory says game over is by rounds only. `GameState.is_game_over` already follows that rule:

```python
return self.current_round > self.max_rounds
```

But auto-play still has a separate `_check_game_end()` that returns `True` when fewer than two players have living units:

```python
if players_alive < 2:
    return True
```

Verified:

```text
AUTOPLAY_ARMY_WIPE_ENDS True
```

This means `run_auto_game()` can stop before the configured round count when an army is wiped. That contradicts the round-limit-only rule and can produce inconsistent replay length/result data compared with `GameState.is_game_over`.

Recommendation:

- Align `_check_game_end()` with `GameState.is_game_over` unless early army-wipe endings are intentionally restored in the spec.
- Add a regression test that a wiped player does not stop auto-play before `max_rounds` if the round-limit-only rule remains the source of truth.

### Important — Mission `check_end_game()` has stale VP-cap and army-wipe end conditions

Location:

- `backend/state/mission.py:65-110`
- `backend/engine/scenario.py:58-69`

`check_end_game()` still contains:

- VP cap end at 100 VP.
- Army wiped end.
- Max rounds check using `round_num >= mission.config.max_rounds`.

`Scenario.run_round()` currently only logs this result and does not mutate `GameState.is_game_over`, but the stale logic is dangerous because it contradicts the canonical `GameState.is_game_over` rule and can be reintroduced accidentally by future code.

Recommendation:

- Either remove non-round end conditions from `check_end_game()` or clearly mark the function as diagnostic-only.
- Prefer a single source of truth for game-over: `GameState.is_game_over` / `current_round > max_rounds`.
- Update comments in `Scenario.run_round()` lines 67-68, which still mention old VP/round checks.

### Important — Charge engagement state is asymmetric

Location:

- `backend/engine/scenario.py:578-635`
- `backend/engine/scenario.py:637-689`

On successful charge, only the charging unit is marked engaged:

```python
unit.is_engaged = True
```

The charged target is not marked `is_engaged = True`. As a result, Fight phase eligibility only includes the charging unit. The target can deal immediate return damage through `_resolve_melee_combat()`, but it is not eligible for its own later activation because `_fight_phase()` filters on `unit.is_engaged`.

This breaks fight activation state even if simplified counter-damage masks it in current tests.

Recommendation:

- On successful charge, mark both charger and target engaged.
- Add a test that a charged target is eligible to activate in Fight phase if alive and not already fought.
- Use `has_fought` consistently instead of the temporary `is_fighting` flag for phase activation tracking.

### Important — Tests encode incorrect Battle-shock semantics

Location:

- `tests/test_f2_7_battle_shock_cp_stratagems.py:48-184`

The tests describe 1/2 models as “below half strength”:

```python
# Unit below half strength (1/2 models)
```

That is exactly half, not below half. Because of this, the tests currently validate the bug instead of detecting it.

Recommendation:

- Rewrite the Battle-shock tests around true Below Half-strength cases.
- Add exact-half negative tests.
- Add single-model wound-threshold tests.

### Suggestion — State naming should encode rules, not inverse approximations

Location:

- `backend/state/game_state.py:65-68`

`is_above_half_strength` is used as an inverse proxy for Battle-shock eligibility. This makes exact-half semantics easy to get wrong.

Recommendation:

- Add `is_below_half_strength` and use it directly in battle-shock code.
- Keep `is_above_half_strength` only if UI needs it, but do not use it for rules gating.

## Positive notes

- `GamePhase` correctly contains five 10ed phases only: Command, Movement, Shooting, Charge, Fight.
- Basic `next_phase()` ordering is correct and advances the round after Fight.
- `GameState.is_game_over` now uses `current_round > max_rounds`, matching the round-limit-only convention.
- CP generation is aligned with current project rule: 0 start and +1 CP per Command phase, capped at 10 in the current implementation.
- Battle Ready +10 VP is applied after auto-play simulation.

## Required fixes before closing CR-08

1. Correct Below Half-strength / Battle-shock eligibility.
2. Move mission VP sync to `PlayerState.victory_points` out of the faction-profile loop and prevent double-counting.
3. Initialize round 1 command priority through the normal Command phase flow.
4. Align auto-play `_check_game_end()` with round-limit-only game-over semantics.
5. Remove or quarantine stale VP-cap/army-wipe logic in mission `check_end_game()`.
6. Make charge engagement state symmetric and use a clear fought-this-phase flag.
7. Replace incorrect Battle-shock tests with rule-correct regression coverage.
