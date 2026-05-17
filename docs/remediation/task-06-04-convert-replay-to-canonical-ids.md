---
title: "Task 6.4 — Convert api_replays and result runtime to canonical unit IDs"
parent: remediation-plan
status: pending
phase: "6 — Replay/result authoritative state"
task_id: "6.4"
source: gap-analysis
---
# Task 6.4 — Convert api_replays and result runtime to canonical unit IDs

**Index:** [index.md](index.md)
**Source plan:** [remediation-plan.md](remediation-plan.md)
**Previous:** [6.3 — Add repeatable final gate smoke script](task-06-03-add-repeatable-final-gate-smoke-script.md)

## Phase context

**Phase:** 6 — Replay/result authoritative state
**Purpose:** replay and result rendering use runtime IDs, not display names.
**Primary CRs:** CR-14, CR-18, CR-24.
**Dependencies:** Phase 5 checkpoint, Phase 1 checkpoint (canonical IDs exist)

## Objective

Convert `api_replays.py` (auto-play simulation launcher and replay persistence) and the result rendering path to use canonical unit IDs rather than wiki display-name lookups. This ensures replays survive display-name changes, two same-name units from different factions don't collide, and the replay layer is decoupled from the mutable wiki loader.

## Scope

In scope:

- `api_replays.py`: `units_from_db()` — lookup units by canonical id (via `CanonicalContentRegistry`) instead of `wiki.get_unit(display_name)`.
- `api_replays.py`: `auto_play_simulation()` — construct `Unit` copies with `unit_id` metadata for runtime use.
- `api_replays.py`: replay persistence — store `unit_id` in replay payloads alongside or replacing display names.
- Result page (`result.html` + `result_chart.js`): consume `unit_id` from replay payload, resolve display labels from canonical registry.
- Tests: verify auto-play with same-name units across factions works; replay survives unit rename; result page reads `unit_id`.

Out of scope:

- Combat/scenario engine `unit.name` → runtime ID (Phase 5 scope).
- AI decision engine (Phase 8 scope).
- Frontend roster display (Phase 2 scope).
- Canonical registry population (Phase 1, already done).

## Contract

- Replay payloads include `unit_id` (canonical id, e.g. `unit:orks:warboss`) as the authoritative unit reference.
- Display names remain in replay payloads as denormalized UI metadata only.
- `wiki.get_unit(display_name)` lookups in the auto-play path are replaced with `CanonicalContentRegistry.get_unit(unit_id)`.
- Replay viewer and result page consume `unit_id` for identity, display name for labels.

## Acceptance criteria

- [ ] `units_from_db()` resolves units by canonical id, not wiki display-name lookup.
- [ ] Auto-play constructed `Unit` objects carry `unit_id` metadata.
- [ ] Replay payloads include `unit_id` per unit.
- [ ] Result page renders correctly using `unit_id` from replay payload.
- [ ] Two same-name units from different factions do not collide in replay/result.
- [ ] Replay survives unit display-name rename in wiki.
- [ ] Existing replays continue to load and display (backward compat).

## Files likely touched

- `web/routes/api_replays.py`
- `web/static/result_chart.js`
- `web/templates/result.html`
- `tests/test_replay.py`

## Test requirements

- Two rosters with same-named units from different factions → auto-play → distinct unit_ids in replay.
- Rename a wiki unit's display name → old replay still loads and resolves.
- Existing replay fixture loads with backward compat.

## Verification

- `uv run python -m pytest tests/test_replay.py -q`
- `uv run python -m pytest tests/test_result_screen.py -q`

## Completion requirements

- [ ] Implementation/change is complete for this task only.
- [ ] Regression evidence is recorded in the affected CR artifact(s).
- [ ] `git diff --check` passes for touched files.
