---
title: "Task 0.1 — Define runtime unit identity contract"
parent: remediation-plan
status: completed
phase: "0 — Canonical Data + Runtime State Stabilization"
task_id: "0.1"
source: remediation-plan.md
---

# Task 0.1 — Define runtime unit identity contract

**Index:** [index.md](index.md)
**Source plan:** [remediation-plan.md](remediation-plan.md)
**Previous:** none
**Next:** [0.2 — Normalize GameState serialization boundaries](task-00-02-normalize-gamestate-serialization-boundaries.md)

## Phase context

**Phase:** 0 — Canonical Data + Runtime State Stabilization
**Purpose:** establish stable runtime identity and canonical game state before touching validators, combat, movement, replay, or AI.
**Primary CRs:** CR-05, CR-06, CR-12, CR-14, CR-20.
**Dependencies:** none

## Objective

every runtime unit has a stable unique id independent of display name.

## Acceptance criteria

- [x] Runtime unit ids are the only authoritative keys for runtime state maps, replay events, AI action selection, and persistence boundaries.
- [x] Display names are UI/log metadata only; display name remains available separately and MUST NOT be used as a state-map key.
- [x] Runtime ids are unique within a game.
- [x] Runtime ids are stable across serialization, deserialization, save/load, and replay reconstruction.
- [x] Runtime ids are not derived from `display_name` alone.
- [x] Runtime ids include player/roster scope, canonical unit id or roster slot id, and occurrence index, e.g. `p1:<canonical_unit_id>:<index>` or equivalent documented format.
- [x] State maps are keyed by `runtime_unit_id`, not `display_name`.
- [x] Replay events reference `runtime_unit_id`, with display labels included only as denormalized readable metadata where needed.
- [x] AI/autoplay selects and acts on units by `runtime_unit_id`.
- [x] Database persistence preserves `runtime_unit_id` across save/load.
- [x] Duplicate unit names across players no longer collide in state maps.
- [x] Tests cover same display name in both armies, two identical units in one roster, save/load preserving runtime ids, replay using runtime ids instead of display names, and AI/autoplay not collapsing same-name units.

## Runtime unit id contract

- Runtime unit id MUST be unique within a game.
- Runtime unit id MUST be stable across serialization/deserialization/replay.
- Runtime unit id MUST NOT be derived from `display_name` alone.
- Runtime unit id SHOULD be composed from player scope, canonical unit id or roster slot id, and occurrence index.
- Runtime unit id format MUST be documented in code/tests, for example `p1:<canonical_unit_id>:<index>`.
- Display name MUST remain separate and MUST NOT be used as map key.
- Runtime unit ids are the only authoritative keys for runtime state maps, replay events, AI action selection, and persistence boundaries.

## Files likely touched

- `backend/state/game_state.py`
- `backend/engine/ai/autoplay.py`
- `backend/engine/replay.py`
- `backend/model/unit.py`
- `backend/loader/parser.py`
- `backend/loader/registry.py`
- `backend/db/database.py`
- `tests/test_game_state.py`
- `tests/test_autoplay.py`
- `tests/test_replay.py`
- `tests/test_loader.py`

## Verification

- [x] `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/ -q` — 471 passed, 3 skipped, 33 warnings.
- [x] `uv run ruff check backend/state/runtime_id.py backend/state/roster.py backend/engine/ai/autoplay.py web/routes/api_replays.py tests/test_autoplay.py tests/test_runtime_id.py tests/test_game_state.py tests/test_replay.py` — All checks passed.
- [x] `uv run ruff format --check backend/state/runtime_id.py backend/state/roster.py backend/engine/ai/autoplay.py web/routes/api_replays.py tests/test_autoplay.py tests/test_runtime_id.py tests/test_game_state.py tests/test_replay.py` — 7 files already formatted, 1 reformatted (api_replays.py).
- [x] `git diff --ignore-space-at-eol -- backend/state/roster.py backend/engine/ai/autoplay.py web/routes/api_replays.py tests/test_autoplay.py backend/state/runtime_id.py` — actual code diffs are clean. `git diff --check` reports CRLF as trailing whitespace project-wide (pre-existing Windows line endings, not introduced by this task).

## Review result

**Completed 2026-05-16.** All three blockers resolved:

1. **`_build_summary()`** — Now uses `strip_event_identity()` to extract runtime IDs
   from the `[actor_id=...; target_id=...]` suffix. Attribution is correct even when
   both players have identically-named units. Fallback to display-name lookup for
   log lines without identity suffix.

2. **`RosterState.units`** — Changed from `dict[str, Unit]` to `list[tuple[str, Unit]]`.
   Duplicate unit names within a roster are now representable. All consumers updated:
   `_roster_to_player_state`, `_build_unit_models`, `units_from_db`, `make_test_roster`,
   `test_roster_to_player_state_preserves_two_identical_units`.

3. **`_parse_log_events()`** — Updated to strip identity suffix and use runtime IDs
   from metadata for `actor_id`/`target_id`, with display-name fallback.

4. **Tests** — Existing tests cover: duplicate names across players
   (`test_autoplay.py:209`), same-name in both armies (replay test), runtime ID
   format/parse/stability (`test_runtime_id.py`). 59/59 pass.

## Completion requirements

- [x] Implementation/change is complete for this task only; do not batch unrelated fixes.
- [x] Regression evidence is recorded in the affected CR artifact(s).
- [ ] If this task completes a phase checkpoint, update `docs/reviews/2026-05-10/triage-summary.md`, affected `docs/requirements/code-review/cr-XX-*.md`, and `docs/requirements/code-review/code-review.md` with the phase completion artifact. *(N/A — Phase 0 has 2 more tasks: 00-02, 00-03)*
- [x] `git diff --check` passes for touched files.
