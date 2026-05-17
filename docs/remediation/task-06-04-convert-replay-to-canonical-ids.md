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
**Purpose:** replay and result rendering use proper runtime/canonical IDs, not display names.
**Primary CRs:** CR-14, CR-18, CR-24.
**Dependencies:** Phase 5 checkpoint, Phase 1 checkpoint (canonical IDs exist)

## Objective

Convert `api_replays.py` (auto-play simulation launcher and replay persistence) and the result rendering path to use `canonical_unit_id` and `runtime_unit_id` rather than wiki display-name lookups.

Critical: do NOT replace display-name identity with canonical-id-only identity for runtime events. Replay events need `runtime_unit_id` to disambiguate duplicated unit instances (e.g. two copies of the same unit in one roster).

## Scope

In scope:

- `api_replays.py`: `units_from_db()` — resolve unit content by `canonical_unit_id` (via `CanonicalContentRegistry`) instead of `wiki.get_unit(display_name)`.
- `api_replays.py`: `auto_play_simulation()` — construct `Unit` copies with `canonical_unit_id` and generate `runtime_unit_id` for battle instance disambiguation.
- `api_replays.py`: replay persistence — store `canonical_unit_id` and `runtime_unit_id` per unit in replay payloads alongside display names (as denormalized UI metadata only).
- Result page (`result.html` + `result_chart.js`): consume IDs from replay payload, resolve display labels from canonical registry.
- Tests covering duplicate unit instances, cross-faction same-name, legacy replay backward compat.

Out of scope:

- Combat/scenario engine `unit.name` → runtime ID (Phase 5 scope).
- AI decision engine (Phase 8 scope).
- Frontend roster display (Phase 2 scope).
- Canonical registry population (Phase 1, already done).

## Replay unit identity contract

Replay payloads MUST include for every unit:

| Field | Format | Purpose |
|-------|--------|---------|
| `runtime_unit_id` | `p1:unit:orks:warboss:0` | Authoritative battle-instance identity |
| `canonical_unit_id` | `unit:orks:warboss` | Stable content lookup identity |
| `display_name` | `"Warboss"` | Denormalized UI metadata only |

Rules:
- `canonical_unit_id` is used for registry lookup (content/stats).
- `runtime_unit_id` is used for replay events, result aggregation, and same-unit-instance disambiguation.
- `display_name` MUST NOT be used as a lookup key.
- Two copies of the same canonical unit in one roster remain distinct by `runtime_unit_id`.
- Two same-name units from different factions remain distinct by `canonical_unit_id` and `runtime_unit_id`.

## Acceptance criteria

- [ ] `units_from_db()` resolves units by `canonical_unit_id` via `CanonicalContentRegistry`, not wiki display-name lookup.
- [ ] Auto-play constructed `Unit` objects carry `canonical_unit_id` metadata.
- [ ] Replay payloads include `canonical_unit_id` and `runtime_unit_id` per unit.
- [ ] Display names remain in replay payloads as denormalized UI metadata only.
- [ ] Result page renders correctly using IDs from replay payload.
- [ ] Two copies of the same canonical unit in one roster remain distinct by `runtime_unit_id`.
- [ ] Two same-name units from different factions remain distinct by `canonical_unit_id` and `runtime_unit_id`.
- [ ] Replay survives unit display-name rename in wiki.
- [ ] Existing legacy replays without `canonical_unit_id`/`runtime_unit_id` still load through a backward-compatible fallback path.
- [ ] Fallback path is marked legacy and does NOT become the primary lookup path.
- [ ] New replay does NOT call `wiki.get_unit(display_name)` on the primary path.

## Files likely touched

- `web/routes/api_replays.py`
- `web/static/result_chart.js`
- `web/templates/result.html`
- `tests/test_replay.py`

## Test requirements

- Same canonical unit duplicated twice in one roster → distinct `runtime_unit_id`s in replay payload.
- Two same-name units from different factions → distinct `canonical_unit_id` and `runtime_unit_id`.
- Legacy replay with only `unit_name` still renders via fallback (not primary lookup path).
- New replay does not call `wiki.get_unit(display_name)` on the primary path.
- Rename a wiki unit's display name → old replay still loads and resolves via `canonical_unit_id`.
- Existing replay fixture loads with backward compat.

## Verification

- `uv run python -m pytest tests/test_replay.py -q`
- `uv run python -m pytest tests/test_result_screen.py -q`

## Completion requirements

- [ ] Implementation/change is complete for this task only.
- [ ] Regression evidence is recorded in the affected CR artifact(s).
- [ ] `git diff --check` passes for touched files.
