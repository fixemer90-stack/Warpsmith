---
title: "CR-14 — Autoplay, replay and result review"
review_id: CR-14
status: request-changes
verdict: request-changes
reviewed_at: 2026-05-09T23:13:16+03:00
reviewer: Hermes
scope:
  - backend/engine/ai/autoplay.py
  - backend/engine/replay.py
  - web/routes/api_replays.py
  - web/static/scenario_setup.js
  - web/static/replay_viewer.js
  - web/static/result_chart.js
  - web/templates/round_viewer.html
  - web/templates/result.html
  - tests/test_autoplay.py
  - tests/test_replay.py
  - tests/test_round_viewer.py
  - tests/test_result_screen.py
summary:
  critical: 3
  important: 4
  suggestions: 0
---

# CR-14 — Autoplay, replay and result review

## Verdict

REQUEST CHANGES

The full setup → auto-play → replay storage → result pipeline is present and the focused tests pass, but the stored replay/result contract is not reliable enough yet. The same simulation seed overwrites previous replays, final replay/result snapshots omit Battle Ready/final VP state, mirrored/same-name armies corrupt summary attribution, and several UI/API summary fields do not parse or display the data emitted by the engine.

No production code was changed during this review.

## Scope reviewed

- `backend/engine/ai/autoplay.py`
- `backend/engine/replay.py`
- `web/routes/api_replays.py`
- `web/static/scenario_setup.js`
- `web/static/replay_viewer.js`
- `web/static/result_chart.js`
- `web/templates/round_viewer.html`
- `web/templates/result.html`
- `tests/test_autoplay.py`
- `tests/test_replay.py`
- `tests/test_round_viewer.py`
- `tests/test_result_screen.py`
- `tests/test_canvas_map.py`
- `tests/test_scenario.py`

## Verification commands

```bash
rm -f *.db-shm *.db-wal && uv run python -m pytest \
  tests/test_autoplay.py \
  tests/test_replay.py \
  tests/test_round_viewer.py \
  tests/test_result_screen.py \
  tests/test_canvas_map.py \
  tests/test_scenario.py -q
```

Result:

```text
62 passed, 7 warnings in 11.41s
```

Additional probes executed:

- `run_auto_game()` replay snapshot/summary inspection with fixed seed `1414`.
- `TestClient` E2E `POST /api/auto-play` with DB-backed rosters and fixed seed `141400`, followed by `GET /api/results/{game_id}`.
- `_parse_log_events()` probe against actual VP and Battle Ready log formats.
- `_build_summary()` probe with duplicate unit names across both players.

## Critical findings

### CR-14-C1 — Fixed seed produces a non-unique `game_id` and overwrites existing replays

**Severity:** Critical  
**Files:** `backend/engine/ai/autoplay.py`, `web/routes/api_replays.py`, `backend/engine/replay.py`

`run_auto_game()` derives the persisted game id directly from the seed:

```python
state = GameState(
    game_id=f"auto_{actual_seed}",
    ...
)
```

`save_replay()` persists with `INSERT OR REPLACE`:

```python
INSERT OR REPLACE INTO replays (game_id, ...)
```

That means two simulations with the same explicit seed use the same `game_id` and the second run replaces the first replay. A seed is useful for reproducibility, but it is not a durable replay identity.

Evidence from `TestClient` E2E probe:

```text
post 0 200 auto_141400 None
post 1 200 auto_141400 None
replay_rows [('auto_141400', 1, 23715, '{"winner": null, ...')]
```

Only one row remained for two successful simulations with the same seed.

**Impact:** Users can lose previous battle results/replays just by repeating a seed. Shared result links are not immutable.

**Recommendation:** Generate a unique game id independent of seed, for example `auto_{uuid4}` or DB sequence/UUID, while storing seed as replay metadata. Avoid `INSERT OR REPLACE` for replay creation unless overwrite is an explicit admin operation.

---

### CR-14-C2 — Final replay/result snapshots omit Battle Ready and final VP state

**Severity:** Critical  
**Files:** `backend/engine/ai/autoplay.py`, `web/routes/api_replays.py`, `web/static/result_chart.js`, `web/templates/result.html`

`run_auto_game()` snapshots each round before/after `scenario.run_round()`, then applies Battle Ready VP after all round snapshots are already appended:

```python
end_state = _snapshot_state(state)
round_logs.append(... end_state ...)
...
for player in state.players.values():
    player.victory_points += 10
```

The final `AutoPlayResult.to_dict()` sees the final VP, but the persisted replay/result page is driven by `replay.rounds[-1].end_state.victory_points`, so the result UI and `/api/results/{game_id}` can show stale scores.

Evidence from fixed-seed probe:

```text
result_dict victory_points {'1': 34, '2': 10}
final player vp {'1': 34, '2': 10}
last snapshot vp {'1': 24, '2': 0}
```

Evidence from DB-backed `/api/results/{game_id}` probe:

```text
result_summary {'winner': None, ...}
last_end_vp {'1': 0, '2': 0}
```

**Impact:** The battle result page can display the wrong final VP totals and a wrong/unknown winner even though the in-memory simulation result had final VP after Battle Ready.

**Recommendation:** Apply all final scoring before the last persisted `end_state`, or append a final result snapshot. Ensure `/api/results/{game_id}`, result stat cards, VP chart, and summary winner all use the same final authoritative VP source.

---

### CR-14-C3 — Mirrored/same-name armies corrupt summary attribution

**Severity:** Critical  
**Files:** `backend/engine/ai/autoplay.py`, `web/routes/api_replays.py`, `web/static/result_chart.js`

`_build_summary()` builds ownership by unit name only:

```python
unit_owner[uname] = pid
```

For mirrored games or rosters with the same unit names, player 2 overwrites player 1 in this map. Damage, kills and charges are then attributed to the wrong player. The same unit-name identity also flows into parsed replay events and result UI helpers.

Probe with both players owning `Boyz`:

```text
dup_summary {
  'winner': None,
  'total_kills': {'1': 1},
  'total_damage': {'2': 3.0},
  'charge_count': {},
  ...
}
```

A single log line `Boyz hits Boyz for 3 damage` was credited to player 2 because the owner map retained only one `Boyz` key.

The same weakness appeared in a real same-faction API probe:

```text
result_summary {'winner': None, 'total_kills': {'1': 1}, 'total_damage': {'2': 14.0}, ...}
```

**Impact:** Orks-vs-Orks, Tau-vs-Tau, or any two rosters sharing unit names get unreliable damage/kills/charges in result summaries and stat cards.

**Recommendation:** Use globally unique runtime unit ids that include player/roster scope, e.g. `p1:Boyz:0`, and preserve both `actor_id` and `actor_name` separately in all logs/events. Build summary attribution from scoped ids, not display names.

## Important findings

### CR-14-I1 — Actual VP logs are parsed as generic `info`, not structured VP events

**Severity:** Important  
**Files:** `web/routes/api_replays.py`, `backend/engine/scenario.py`, `backend/engine/ai/autoplay.py`

`_parse_log_events()` only matches:

```regex
^(.+?)\s+gained\s+([\d.]+)\s+VP$
```

But actual emitted logs include totals and Battle Ready wording:

```text
orks roster gained 3 VP (total: 3)
tau roster gains 10 Battle Ready VP (total: 10)
```

Probe output:

```text
vp_parser [
  ('info', '', '', None, 'orks roster gained 3 VP (total: 3)'),
  ('info', '', '', None, 'tau roster gained 10 Battle Ready VP (total: 10)'),
  ('vp', 'command', 'Plain Army', 5.0, None)
]
```

**Impact:** Replay phase/event views do not get structured VP events for the logs the engine actually produces. This limits result explainability even when snapshots contain VP totals.

**Recommendation:** Align log emitters and parsers. Either emit structured events from the engine directly, or support current log variants including `(total: N)` and Battle Ready text.

---

### CR-14-I2 — Result page player 2 charge card is effectively always zero for normal events

**Severity:** Important  
**Files:** `web/templates/result.html`, `web/static/result_chart.js`, `web/routes/api_replays.py`

The result template counts player 2 charges by checking whether `actor_id` starts with `player2`:

```html
.filter(e => e.event_type==='charge' && e.result_value > 0 && e.actor_id?.startsWith('player2'))
```

Parsed replay events currently use unit names as `actor_id`, for example `Boyz`, `Warboss`, or synthetic `Unit 1`, not `player2...` scoped ids.

**Impact:** Player 2 successful charges are not reflected in the result stat cards. Player 1 card can also be inflated because it counts all non-`player2` charge actor ids.

**Recommendation:** Use the same player-ownership helper used for damage attribution, or add explicit `actor_player_id` to `ReplayEvent`.

---

### CR-14-I3 — The replay recorder model is mostly bypassed by auto-play persistence

**Severity:** Important  
**Files:** `backend/engine/replay.py`, `backend/engine/ai/autoplay.py`, `web/routes/api_replays.py`

`ReplayRecorder` provides typed event recording methods, timestamps and round lifecycle helpers, but `auto_play_simulation()` does not use it. It reconstructs events later by parsing plain text logs:

```python
parsed_events = _parse_log_events(phase_logs, round_num)
```

This creates two different snapshot paths:

- `backend.engine.replay._snapshot_state()` does not include map dimensions.
- `backend.engine.ai.autoplay._snapshot_state()` does include `map_width`/`map_height` for the round viewer.

**Impact:** Replay fidelity depends on fragile regex parsing and duplicate serialization code. The typed recorder is tested, but the live auto-play pipeline does not exercise it.

**Recommendation:** Integrate `ReplayRecorder` into `Scenario`/auto-play or make auto-play the single canonical recorder. Remove duplicate snapshot contracts or add contract tests that assert the live persisted replay schema.

---

### CR-14-I4 — Existing tests pass but do not assert the core E2E result correctness properties

**Severity:** Important  
**Files:** `tests/test_autoplay.py`, `tests/test_replay.py`, `tests/test_round_viewer.py`, `tests/test_result_screen.py`

The focused suite passes, but current tests mostly assert page existence, basic serialization, and non-crashing simulation. They do not assert the properties that broke in probes:

- two simulations do not overwrite each other;
- `/api/auto-play` persists a replay with a unique `game_id`;
- `/api/results/{game_id}` final VP equals the final simulation VP including Battle Ready;
- VP logs become structured `vp` events;
- mirrored rosters attribute damage/kills/charges to the correct player;
- result cards split charges/damage by actual player ownership.

Existing round viewer test explicitly notes a placeholder:

```python
# in a real scenario we'd seed a replay with known VP values and verify they change between rounds.
```

**Impact:** The replay/result pipeline can regress while all current tests stay green.

**Recommendation:** Add a DB-backed `TestClient` E2E test that creates two rosters, runs `/api/auto-play`, fetches `/api/replays/{game_id}` and `/api/results/{game_id}`, then asserts unique persistence, final VP/winner, map dimensions, events, and summary attribution.

## Positive notes

- Focused tests pass: `62 passed, 7 warnings in 11.41s`.
- The pipeline has the expected high-level endpoints:
  - `POST /api/auto-play`
  - `GET /api/replays/{game_id}`
  - `GET /api/results/{game_id}`
- `_snapshot_state()` in `backend/engine/ai/autoplay.py` includes units, positions, VP and dynamic map dimensions.
- `replay_viewer.js` reads `map_width`/`map_height` from replay data rather than relying on the old fixed 19×14 grid.
- `scenario_setup.js` redirects to `/result/{game_id}` when the API returns a game id.

## Required remediation before approval

1. Make replay `game_id` unique and independent of seed.
2. Persist final authoritative VP/winner state, including Battle Ready, into the replay/result contract.
3. Replace unit-name ownership attribution with scoped runtime unit ids/player ids.
4. Align actual engine logs with `_parse_log_events()` or emit structured replay events directly.
5. Fix result-page charge and damage attribution to use explicit player ownership.
6. Add DB-backed E2E tests for `/api/auto-play` → replay → result.

## Final status

- Verdict: REQUEST CHANGES
- Critical: 3
- Important: 4
- Suggestions: 0
- Production code changed: no
