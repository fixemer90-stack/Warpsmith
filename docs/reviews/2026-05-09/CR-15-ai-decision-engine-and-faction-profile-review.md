---
title: "CR-15 — AI decision engine and faction profile review"
review_id: CR-15
status: request-changes
verdict: request-changes
reviewed_at: 2026-05-09T23:22:36+03:00
reviewer: Hermes
scope:
  - backend/engine/ai/decision.py
  - backend/engine/ai/faction_ai.py
  - backend/engine/ai/deployment.py
  - backend/engine/ai/autoplay.py
  - backend/engine/scenario.py
  - wiki/factions/Orks.md
  - wiki/factions/T'au Empire.md
  - wiki/factions/Adeptus Mechanicus.md
  - tests/test_ai_decision.py
  - tests/test_faction_ai.py
  - tests/test_deployment_ai.py
  - tests/test_autoplay.py
severity_counts:
  critical: 3
  important: 4
  suggestions: 0
---

# CR-15 — AI decision engine and faction profile review

## Verdict

REQUEST CHANGES

The faction profile loader and isolated helper tests exist, and autoplay does load profiles before deployment/scenario. However, the accepted F3.1/F3.2 decision engine is not the live scenario decision path, action overrides are not applied, and target-priority semantics are only partially honored. Current tests pass because they mainly verify helpers and smoke completion, not that Orks/Tau/AdMech profiles actually drive live decisions end-to-end.

## Inspected scope

- `backend/engine/ai/decision.py`
- `backend/engine/ai/faction_ai.py`
- `backend/engine/ai/deployment.py`
- `backend/engine/ai/autoplay.py`
- `backend/engine/scenario.py`
- `wiki/factions/Orks.md`
- `wiki/factions/T'au Empire.md`
- `wiki/factions/Adeptus Mechanicus.md`
- `tests/test_ai_decision.py`
- `tests/test_faction_ai.py`
- `tests/test_deployment_ai.py`
- `tests/test_autoplay.py`

## Verification commands

```bash
rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_ai_decision.py tests/test_faction_ai.py tests/test_deployment_ai.py tests/test_autoplay.py -q
```

Result:

```text
101 passed in 9.81s
```

Custom integration probes executed:

```bash
python3 - <<'PY'
from backend.engine.ai.faction_ai import load_profile, get_target_multiplier, clear_cache, get_active_behavior_override, choose_action_with_faction_ai
from backend.engine.ai.decision import EvaluationContext
from backend.model.unit import Unit, Weapon
from backend.state.game_state import GameState, PlayerState, UnitState, GamePhase
from backend.engine.scenario import Scenario

clear_cache()
ork=load_profile('orks')
tau=load_profile('tau')
print('target_mult_ork_infantry', get_target_multiplier(ork, {'infantry'}), 'yaml', ork.target_priority.get('infantry'))
print('target_mult_ork_battleline', get_target_multiplier(ork, {'battleline'}), 'yaml', ork.target_priority.get('battleline'))

clear_cache(); ork=load_profile('orks')
print('override_before_wrapper', get_active_behavior_override(ork, GamePhase.CHARGE, 1))
actor=UnitState(unit_id='boyz', name='Boyz', faction='orks', position=(0,0), current_wounds=10, max_wounds=10, models_remaining=10, models_total=10, leadership=7, objective_control=2)
target=UnitState(unit_id='enemy', name='Enemy', faction='tau', position=(20,0), current_wounds=5, max_wounds=5, models_remaining=5, models_total=5, leadership=7, objective_control=1)
actor_model=Unit(name='Boyz', faction='orks', category='Infantry', movement=6, toughness=5, save=5, wounds=1, leadership=7, objective_control=2, melee_weapons=[Weapon(name='Choppa', type='melee', range_max=None, attacks_dice=(3,1,0), skill=3, strength=4, ap=-1, damage_dice=(1,1,0))])
state=GameState(game_id='ai-probe', mission_name='only_war', current_phase=GamePhase.CHARGE, players={'1': PlayerState(player_id='1', name='orks', faction='orks', units={'boyz':actor}), '2': PlayerState(player_id='2', name='tau', faction='tau', units={'enemy':target})})
ctx=EvaluationContext(actor=actor, actor_unit=actor_model, state=state, opponent_units=[target], phase=GamePhase.CHARGE, turn=1, opponent_units_map={'enemy': Unit(name='Enemy', faction='tau', category='Infantry', movement=6, toughness=4, save=4, wounds=1, leadership=7, objective_control=1)}, faction_profile=None)
action=choose_action_with_faction_ai(actor_model, ctx)
print('wrapper_action_type', action.type.value, 'score', action.score, 'ctx_has_profile', ctx.faction_profile is not None)

# Static live-use inventory was also run through search_files for choose_action / EvaluationContext.
PY
```

Observed output excerpt:

```text
target_mult_ork_infantry 1.0 yaml 0.9
target_mult_ork_battleline 1.0 yaml 0.8
override_before_wrapper charge
wrapper_action_type hold score 0.0 ctx_has_profile False
```

## Findings

### Critical 1 — F3.1 greedy decision engine is not used by the live scenario/autoplay phases

Files:
- `backend/engine/ai/decision.py`
- `backend/engine/ai/faction_ai.py`
- `backend/engine/scenario.py`
- `backend/engine/ai/autoplay.py`

Evidence:
- `choose_action_with_faction_ai()` is defined only in `backend/engine/ai/faction_ai.py` and has no production call sites.
- `choose_action()` is returned by `resolve_ai_for_faction()` for fallback, but `resolve_ai_for_faction()` itself is only exercised by tests and not used in `run_auto_game()` or `Scenario` phase execution.
- `Scenario._movement_phase()`, `_shooting_phase()`, and `_charge_phase()` use ad hoc logic: objective assignment, closest target, random movement action, and closest charge target.

Impact:
- Most of F3.1 is effectively dead for live simulations.
- Weights such as `kill_efficiency`, `threat_reduction`, `survival_risk`, and decision-engine scoring do not consistently influence live actions.
- Passing tests for `decision.py` do not prove that autoplay uses those decisions.

Recommendation:
- Route live movement/shooting/charge decisions through `EvaluationContext` + `choose_action_with_faction_ai()` or delete/replace the unused F3.1 path with the real `Scenario` AI implementation.
- Add integration tests that monkeypatch or instrument `choose_action_with_faction_ai()` and assert it is invoked during `run_auto_game()` for Movement/Shooting/Charge.

### Critical 2 — Faction behavior `action_override` is retrieved but never applied to the selected action

File:
- `backend/engine/ai/faction_ai.py:320-330`

Evidence:
- `choose_action_with_faction_ai()` computes:
  - `ctx.weights = get_weights(...)`
  - `override = get_active_behavior_override(...)`
- The override is only logged; it is not used to force/filter candidates or override the return value.
- Probe: Orks `Ere We Go` returns `charge` before the wrapper, but a too-far charge context still returns `hold` with score `0.0`.

Observed:

```text
override_before_wrapper charge
wrapper_action_type hold score 0.0 ctx_has_profile False
```

Impact:
- YAML behaviors such as Orks `ere_we_go` and any future forced behavior are declarative but not operational.
- The CR acceptance asks that faction profiles really drive autoplay decisions; this override path does not.

Recommendation:
- Define explicit semantics for `action_override`:
  - force action type only if legal, or
  - bias that action type strongly, or
  - apply a phase-specific modifier such as charge reroll.
- Add tests proving an active override changes the selected action or combat/charge resolution.

### Critical 3 — Faction profile does not reach decision scoring in `choose_action_with_faction_ai()`

Files:
- `backend/engine/ai/faction_ai.py:318-330`
- `backend/engine/ai/decision.py:328-337`, `372-381`

Evidence:
- `score_shoot()` and `score_charge()` only apply target priority when `ctx.faction_profile is not None`.
- `choose_action_with_faction_ai()` loads `profile` and updates `ctx.weights`, but never sets `ctx.faction_profile = profile`.
- Probe output:

```text
wrapper_action_type hold score 0.0 ctx_has_profile False
```

Impact:
- Even when callers use the wrapper, target-priority multipliers in the F3.1 engine remain disabled unless the caller manually pre-populates `ctx.faction_profile`.
- The wrapper name promises faction-AI-aware decision-making but only partially wires the data.

Recommendation:
- Set `ctx.faction_profile = profile` before calling `choose_action()`.
- Add a test where two targets differ only by target-priority keyword and the wrapper chooses the priority target.

### Important 1 — Target-priority values below 1.0 are ignored

File:
- `backend/engine/ai/faction_ai.py:257-271`

Evidence:
- `get_target_multiplier()` initializes `best = 1.0` and then returns `max(best, profile.target_priority[kw])`.
- YAML intentionally defines deprioritized targets:
  - Orks `infantry: 0.9`
  - Orks `battleline: 0.8`
  - Tau `battleline: 0.9`
- Probe output:

```text
target_mult_ork_infantry 1.0 yaml 0.9
target_mult_ork_battleline 1.0 yaml 0.8
```

Impact:
- Profiles can only boost target priority, never lower it, despite YAML using values below 1.
- Orks cannot actually deprioritize battleline/infantry as authored.

Recommendation:
- If the desired behavior is “best matching configured multiplier”, return the highest configured match and fallback to `1.0` only when no keywords match.
- Add explicit tests for values below `1.0`.

### Important 2 — `get_weights()` marks behaviors as used even when only reading weights, which can consume one-shot/cooldown behavior state

File:
- `backend/engine/ai/faction_ai.py:227-254`

Evidence:
- `get_weights()` applies `weights_override` and immediately calls `mark_behavior_used()` for every active behavior.
- This includes active behaviors with empty `weights_override` but an `action_override`.
- The function name and tests treat it as a getter, but it mutates runtime behavior state.

Impact:
- Calling `get_weights()` for inspection or before separately checking `get_active_behavior_override()` can consume behavior availability.
- This creates order-dependent behavior bugs and makes tests/probes fragile.

Recommendation:
- Split pure calculation from mutation:
  - `compute_active_weights(profile, phase, turn) -> weights, active_behaviors`
  - `mark_behavior_used()` only after the behavior is actually applied in the live action.
- Add tests that one-shot/cooldown behaviors are consumed only when their effect is applied.

### Important 3 — Autoplay deployment passes no objectives to `deploy_game()`

File:
- `backend/engine/ai/autoplay.py:429-437`

Evidence:

```python
placements = deploy_game(
    game_state=state,
    unit_models=unit_models,
    deployment_type=config.deployment_type,
    battlefield=game_map,
    objectives=[],
    faction_ai_profiles=faction_ai_profiles,
)
```

Impact:
- `deployment.py` has objective-aware placement (`_is_on_objective`, objective score for melee fallback), but live autoplay always supplies an empty objective list.
- Deployment behavior is therefore less tied to mission context than tests imply.

Recommendation:
- Pass `state.mission.config.objectives` after `GameState` mission creation.
- Add a deployment integration test that mission objectives influence initial placement when expected.

### Important 4 — Tests prove helper behavior but not live faction-specific decisions

Files:
- `tests/test_ai_decision.py`
- `tests/test_faction_ai.py`
- `tests/test_deployment_ai.py`
- `tests/test_autoplay.py`

Evidence:
- Focused suite passes: `101 passed in 9.81s`.
- Missing assertions:
  - `run_auto_game()` invokes `choose_action_with_faction_ai()` or otherwise uses F3.1 decisions.
  - Orks melee units choose enemy-hunting more often than Tau in the same state.
  - Tau shooting target priority changes actual target selection.
  - `action_override` changes a live action.
  - target-priority values below 1.0 are respected.
  - mission objectives are passed to deployment.

Impact:
- Tests can pass while acceptance is not met: “Orks/Tau/AdMech behavior profiles реально используются в autoplay decisions.”

Recommendation:
- Add black-box integration tests around `run_auto_game()` or `Scenario` with deterministic states and seeded/random-patched choices.
- Assert concrete behavioral deltas, not just `result.error is None`.

## Positives

- Faction YAML profiles for Orks and Tau contain meaningful `weights`, `behaviors`, `target_priority`, and `deployment` sections.
- `load_profile()` supports relaxed/fuzzy filename matching and has cache isolation tests.
- `deploy_game()` accepts `faction_ai_profiles` and can use deployment roles when supplied.
- `decision.py` has focused tests for scoring, objective movement candidates, and basic action selection.

## Required follow-up

1. Decide whether `Scenario` should call F3.1/F3.2 directly or whether F3.1 should be retired in favor of Scenario-native AI.
2. Wire `ctx.faction_profile` and enforce/apply `action_override` semantics.
3. Fix target-priority multipliers below 1.0.
4. Pass mission objectives into live deployment.
5. Add deterministic integration tests proving faction profiles alter live autoplay decisions.
