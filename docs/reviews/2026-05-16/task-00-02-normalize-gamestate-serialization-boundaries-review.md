# Review — task-00-02-normalize-gamestate-serialization-boundaries

Date: 2026-05-16
Task artifact: ../../remediation/task-00-02-normalize-gamestate-serialization-boundaries.md
Scope reviewed:
- backend/state/game_state.py
- backend/engine/ai/autoplay.py
- backend/engine/replay.py
- web/routes/api_replays.py
- tests/test_replay.py
- tests/test_autoplay.py

Verdict: REQUEST CHANGES

Severity counters:
- Critical: 0
- Important: 2
- Suggestions: 1
- Nit/FYI: 0

## Findings

### Important 1 — canonical unit record does not expose the explicit identity/display contract from the task

Files:
- backend/state/game_state.py:338-353
- tests/test_replay.py:542-569
- docs/remediation/task-00-02-normalize-gamestate-serialization-boundaries.md:33,36-38

Task acceptance says snapshot unit records include `runtime_unit_id`, `display_name`, `owner_id`/`player_id`, and `canonical_unit_id` if available. The implementation serializes only `id` and `name`:

```python
return {
    "id": getattr(unit, "unit_id", ""),
    "name": getattr(unit, "name", str(unit)),
    "player_id": player_id,
    ...
}
```

The tests also say "runtime_unit_id" / "display_name" in docstrings, but assert `unit["id"]` and `unit["name"]`. This means the tests do not enforce the stated contract. A future consumer can still treat `name` as a lookup/display field ambiguously, and the serialized API shape does not contain the explicit display-only alias the task requires.

Recommendation:
- Keep `id`/`name` temporarily only as legacy aliases if needed by existing JS.
- Add explicit fields:
  - `runtime_unit_id`: same value as `unit.unit_id`; authoritative identity.
  - `display_name`: same value as `unit.name`; UI text only.
  - `canonical_unit_id`: parsed from runtime id or model metadata when available.
  - optionally `owner_id`: alias of `player_id` if the contract wants both.
- Update tests to assert these field names directly, not only aliases.

### Important 2 — replay/result final snapshots are stale after Battle Ready VP is applied

Files:
- backend/engine/ai/autoplay.py:487-516
- web/routes/api_replays.py:419-445,497-515

`run_auto_game()` captures each round `end_state` before awarding Battle Ready VP, then adds +10 VP directly to `state.players` after the loop. The persisted replay is built only from `result.round_logs`, so `/api/replays/{game_id}` and `/api/results/{game_id}` expose the last round `end_state.victory_points` without Battle Ready points.

Probe output:

```text
final_state_vp= {'1': 19, '2': 10}
last_round_end_vp= {'1': 9, '2': 0}
canonical_now_vp= {'1': 19, '2': 10}
```

This violates the task goal that final snapshots/replay/API payloads use one state shape and do not diverge. It also affects result UI numbers because result_chart/result.html read VP from the last round `end_state`.

Recommendation:
- After applying Battle Ready VP, recapture the final canonical snapshot with `snapshot_game_state(state)` and persist it as the authoritative final state.
- Minimal fix for current shape: update the last `round_logs[-1]["end_state"]` after Battle Ready VP is applied, or add a replay-level `final_state` and update consumers to use it.
- Add a regression test where `result.game_state` VP equals persisted replay/result final snapshot VP after Battle Ready.

### Suggestion 1 — `_unit_snapshot(unit)` wrapper in replay.py produces `player_id=""`

Files:
- backend/engine/replay.py:261-265
- tests/test_replay.py:503-515

The compatibility wrapper delegates to the canonical serializer with `player_id=""`. Existing tests for this helper do not check `player_id`, so direct callers can get an invalid owner field. If the helper remains public/imported, either require `player_id` explicitly or mark it as legacy/test-only and adjust tests to prevent use as a full canonical record.

## Verification commands run

```bash
rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_replay.py tests/test_round_viewer.py tests/test_result_screen.py -q
# 43 passed, 12 warnings in 1.02s

uv run ruff check backend/state/game_state.py backend/engine/ai/autoplay.py backend/engine/replay.py tests/test_replay.py tests/test_autoplay.py
# All checks passed!

uv run ruff format --check backend/state/game_state.py backend/engine/ai/autoplay.py backend/engine/replay.py tests/test_replay.py tests/test_autoplay.py
# 5 files already formatted

git diff --check -- backend/state/game_state.py backend/engine/ai/autoplay.py backend/engine/replay.py tests/test_replay.py tests/test_autoplay.py docs/remediation/task-00-02-normalize-gamestate-serialization-boundaries.md
# passed

uv run python - <<'PY'
# custom integration probe: compare final GameState VP vs last replay end_state VP and inspect unit fields
PY
# final_state_vp= {'1': 19, '2': 10}
# last_round_end_vp= {'1': 9, '2': 0}
# unit_keys= ['current_wounds', 'id', 'is_alive', 'is_battle_shocked', 'is_engaged', 'max_wounds', 'models_remaining', 'models_total', 'name', 'player_id', 'position']
# canonical_now_vp= {'1': 19, '2': 10}
```

## Positives

- `autoplay._snapshot_state()` and `replay._snapshot_state()` now delegate to `snapshot_game_state()`, removing the previous duplicated ad-hoc builders.
- Runtime IDs distinguish mirrored same-name units (`p1:Boyz:0` vs `p2:Boyz:0`).
- Focused replay/round/result tests pass.
- No static lint/format/diff-check issues in reviewed files.

## Required follow-up

Do not mark task 00-02 as review-approved until:
1. The serialized unit record exposes the explicit task fields (`runtime_unit_id`, `display_name`, `canonical_unit_id` when available, owner/player field).
2. Persisted replay/result final state matches the post-Battle-Ready authoritative GameState.
3. Tests assert the explicit contract and the final snapshot equality, not only alias fields.
