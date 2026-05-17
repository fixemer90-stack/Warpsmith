---
title: "Code Review Remediation Plan"
parent: code-review
status: draft
priority: P0
source: triage-summary.md
scope: CR remediation after CR-24
---

# Code Review Remediation Plan

> **For Hermes:** Use `subagent-driven-development` or one focused implementation session per task. Do not batch unrelated fixes. Each task must end with tests, docs sync where applicable, and CR artifact/status updates.
> **Atomic tasks:** see [index.md](index.md). Each atomic task is also stored as its own `task-*.md` file in this folder.

**Goal:** turn the CR-00..CR-24 review result into an ordered remediation program that stabilizes canonical data, runtime state, core rules, replay/result truth, API/auth/persistence, and AI integration before re-running CR-24.

**Architecture:** fix foundations first. Canonical wiki data and runtime identity/state become the source of truth; validators and combat/gameplay consume that canonical layer; replay/result persists authoritative final state; API/auth/persistence hardening wraps the product boundary; AI integration is last so it uses stable movement/combat/game-state contracts.

**Tech stack:** Python 3.12, FastAPI, SQLite, Jinja2, Alpine.js, pytest, ruff, Warhammer 40k 10th edition rules.

## Non-negotiable separation rules

These are hard architectural boundaries for the whole remediation program:

- Display name != runtime identity.
  - Display names are UI/log labels only.
  - Runtime state, replay snapshots, damage, ownership, deaths, movement, charges, and result attribution must use stable runtime ids.
- Raw wiki data != runtime canonical data.
  - Wiki frontmatter/body is source input, not the object model consumed directly by validators/combat/game state.
  - The compiler/schema layer must normalize wiki data into canonical runtime records before game systems use it.
- AI decision != authoritative state mutation.
  - AI may propose actions/intents only.
  - Game-state/scenario engines validate and apply mutations; AI must not bypass movement, charge, combat, VP, ownership, or persistence invariants.
- Round snapshots != final result authority.
  - Round snapshots are replay timeline evidence.
  - The final result must come from an authoritative final state/result payload, with VP/winner/kills/losses derived from the same source.
- Tests passing != CR status closed.
  - Executable checks are necessary but not sufficient.
  - A finding is closed only when implementation, regression evidence, affected CR artifacts, `triage-summary.md`, and `code-review.md` are all updated.

## Dependency graph

| Phase                                             | Depends on | Unlocks                    |
| ------------------------------------------------- | ---------- | -------------------------- |
| 0. Canonical Data and Runtime State Stabilization | —          | 1                          |
| 1. Content Compiler and Schemas                   | 0          | 2, 3                       |
| 2. Roster Validator                               | 1          | 4                          |
| 3. Combat Math                                    | 1          | 4                          |
| 4. Game State, VP, Phase Invariants               | 2, 3       | 5                          |
| 5. Movement, Charge, Melee Identity               | 4          | 6                          |
| 6. Replay and Result Authoritative State          | 5          | 7, 8                       |
| 7. API, Auth, Persistence Hardening               | 6          | CR-24                      |
| 8. AI Integration                                 | 6          | CR-24                      |
| CR-24 Final Regression Gate                       | 7, 8       | Release readiness decision |

## Global rules for every phase

- Work in one phase at a time; do not start phase N+1 until phase N checkpoint passes.
- Write regression tests before production changes where feasible.
- Keep runtime identifiers separate from display names.
- No hardcoded faction/unit/detachment lists where wiki/API should be source of truth.
- After backend changes run at minimum the scoped tests plus:
  - `uv run ruff check .`
  - `uv run ruff format --check .`
  - `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/ -q`
- After JS/HTML changes also run:
  - `node -c web/static/team_builder.js`
  - `node -c web/static/scenario_setup.js`
  - `node -c web/static/battlefield_map.js`
  - Browser smoke for affected pages.
- Update relevant CR artifact(s), `code-review.md`, and `triage-summary.md` after each phase.
- Each phase is not complete until its phase completion artifact is written and linked from the affected review metadata.

## Phase completion artifact

At the end of every phase, update all three metadata surfaces:

- `docs/reviews/2026-05-10/triage-summary.md`
- affected `docs/requirements/code-review/CR-XX.md` artifacts, using the actual lowercase file names in this directory
- `docs/requirements/code-review/code-review.md`

Each phase update must include this required shape:

- phase number and phase title
- task IDs completed, for example `0.1`, `0.2`, `0.3`
- CR findings closed, grouped by CR id and finding id/title where available
- CR findings still open, grouped by CR id and finding id/title where available
- accepted debt, if any, with owner/rationale/revisit trigger; otherwise state `none`
- test commands run, including exit status and short result summary
- lint/format commands run, including exit status and short result summary
- browser/API smoke evidence where applicable, including URL, endpoint, replay id, screenshot path, or curl output summary
- remaining blockers before the next phase; otherwise state `none`

Minimum markdown template for the phase completion artifact:

```markdown
### Phase N completion — <phase title>

- Completed tasks: <task ids>
- Closed findings:
  - CR-XX: <finding id/title or summary>
- Still open:
  - CR-YY: <finding id/title or summary>
- Accepted debt: <none | explicit accepted debt entry>
- Tests run:
  - `<command>` → <exit code/result>
- Lint/format run:
  - `<command>` → <exit code/result>
- Browser/API smoke evidence:
  - <none | URL/endpoint/replay id/evidence summary>
- Remaining blockers before next phase: <none | blockers>
```

Do not mark a phase complete in `code-review.md` unless this artifact exists in `triage-summary.md` and the affected CR artifacts have been updated. This prevents CR-24 from passing executable gates while review metadata remains stale.

## Phase 0 — Canonical Data + Runtime State Stabilization

**Purpose:** establish stable runtime identity and canonical game state before touching validators, combat, movement, replay, or AI.

**Primary CRs:** CR-05, CR-06, CR-12, CR-14, CR-20.

**Files likely touched:**
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

### Task 0.1 — Define runtime unit identity contract

**Objective:** every runtime unit has a stable unique id independent of display name.

**Acceptance criteria:**
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

**Runtime unit id contract:**
- [x] Runtime unit id MUST be unique within a game.
- [x] Runtime unit id MUST be stable across serialization/deserialization/replay.
- [x] Runtime unit id MUST NOT be derived from `display_name` alone.
- [x] Runtime unit id SHOULD be composed from player scope, canonical unit id or roster slot id, and occurrence index.
- [x] Runtime unit id format MUST be documented in code/tests, for example `p1:<canonical_unit_id>:<index>`.
- [x] Display name MUST remain separate and MUST NOT be used as map key.

**Verification:**
- `uv run python -m pytest tests/test_game_state.py tests/test_autoplay.py -q`

### Task 0.2 — Normalize GameState serialization boundaries

**Objective:** make snapshots, replay payloads, and API payloads use one state shape.

**Acceptance criteria:**
- [x] Round snapshots and final snapshots are generated through the same serialization function/schema.
- [x] Round snapshots and final snapshots MUST NOT be assembled by separate ad-hoc dict builders.
- [x] Replay payloads and API payloads reuse the same serializer or canonical schema.
- [x] Snapshot unit records include `runtime_unit_id`, `display_name`, `owner_id`/`player_id`, `canonical_unit_id` if available, position, wounds, models, status flags, and VP-relevant state.
- [x] Unit entries are keyed by `runtime_unit_id` or include `runtime_unit_id` as the authoritative id field.
- [x] VP fields use the same names and nesting in round and final snapshots.
- [x] Existing UI consumers still receive display names, but legacy UI compatibility is preserved by keeping `display_name` fields, not by preserving display-name-keyed maps.
- [x] No consumer requires `display_name` as a lookup key.
- [x] Tests cover round snapshot and final snapshot having identical top-level/unit keys, result screen reading the same shape as round viewer, mirrored same-name units serializing as distinct runtime ids, replay payload round snapshots and final snapshot not diverging, and `display_name` remaining present for UI text.

**Canonical serialized GameState contract:**
- [x] Serialized GameState MUST have one canonical shape used by round snapshots, final snapshots, replay payloads, and API payloads consumed by result/round viewer screens.
- [x] Unit entries MUST be keyed by `runtime_unit_id` or include `runtime_unit_id` as the authoritative id field.
- [x] Display name MUST be included only as display metadata.
- [x] No consumer may require `display_name` as a lookup key.

**Verification:**
- `uv run python -m pytest tests/test_replay.py tests/test_round_viewer.py tests/test_result_screen.py -q`

### Task 0.3 — Stop destructive DB/replay behavior before further fixes

**Objective:** remove data-loss risks that can hide later regressions.

**Acceptance criteria:**
- [x] Existing replay rows survive app startup and DB initialization.
- [x] Startup and migration code are additive/non-destructive by default.
- [x] No startup path deletes, truncates, or recreates replay tables containing existing data unless running an explicit isolated test reset path.
- [x] Replay identity is generated independently from simulation seed.
- [x] Simulation seed may be stored as replay metadata, but MUST NOT be reused as durable `replay_id` by default.
- [x] Replay save fails with a controlled error on duplicate `replay_id` by default.
- [x] Replay overwrite is allowed only when caller passes explicit `overwrite=True` / `replace=True`.
- [x] Fixed seed produces repeatable simulation behavior but distinct durable replay ids across separate save attempts unless `replay_id` is explicitly provided.
- [x] Test fixtures may reset DB only through isolated test setup helpers, not production startup/migration code.
- [x] Do not solve this by disabling tests or by changing tests to accept replay deletion.
- [x] Tests cover database initialization preserving existing replay rows, duplicate `replay_id` save failing by default, duplicate `replay_id` save succeeding only with explicit overwrite, same fixed seed creating different replay ids across separate save attempts, replay metadata storing seed when provided, and production startup path not calling destructive reset helpers.

**Replay persistence contract:**
- [x] Replay identity MUST be generated independently from simulation seed.
- [x] Simulation seed MAY be stored as replay metadata.
- [x] Replay save MUST fail on duplicate `replay_id` by default.
- [x] Replay overwrite is allowed only when caller passes explicit `overwrite=True` / `replace=True`.
- [x] Startup and migration code MUST be additive/non-destructive by default.
- [x] No startup path may delete, truncate, or recreate replay tables containing existing data unless running an explicit test reset path.

**Non-goals:** Replay schema redesign is not in scope; replay playback logic changes are not in scope except where required to preserve/load existing replay ids.

**Verification:**
- `uv run python -m pytest tests/test_replay.py tests/test_db*.py -q`

### Checkpoint 0

- [x] Runtime unit identity is unique and tested.
- [x] No replay overwrite/data-loss regression.
- [x] Full tests pass.

## Phase 1 — Content compiler / schemas

**Purpose:** make wiki/frontmatter content compile into validated schemas before runtime use.

**Primary CRs:** CR-06, CR-11, CR-12, CR-21.

**Files likely touched:**
- `backend/model/unit.py`
- `backend/loader/parser.py`
- `backend/loader/registry.py`
- new: `backend/loader/compiler.py`
- new: `backend/loader/schemas.py`
- `wiki/`
- target/generated: `data/generated/content/manifest.json`
- target/generated: `data/generated/content/units/index.json`
- target/generated: `data/generated/content/units/<owning_or_source_faction_id>.json` definition shards
- target/generated: `data/generated/content/faction_units/index.json`
- target/generated: `data/generated/content/faction_units/<faction_id>.json` availability/link shards
- target/generated: `data/generated/content/weapons.json`
- target/generated: `data/generated/content/factions.json`
- target/generated: `data/generated/content/detachments.json`
- target/generated: `data/generated/content/stratagems.json`
- target/generated: `data/generated/content/enhancements.json`
- target/generated: `data/generated/content/rules.json`
- `tests/test_parser.py`
- `tests/test_registry.py`
- new: `tests/test_content_contracts.py`

### Task 1.1 — Create content contract tests

**Objective:** fail fast on invalid wiki content that breaks runtime logic.

**Acceptance criteria:**
- [ ] Unit files compile into typed Unit objects and/or canonical JSON records without silent defaults for required gameplay fields.
- [ ] Points, squad_size, model_count, weapons, faction, tags, keywords, OC/LD/SV/T/W/M are validated.
- [ ] Every faction/unit/weapon/detachment/stratagem/enhancement/rule has a stable canonical id or an explicit transitional collision report.
- [ ] Missing or duplicate canonical ids fail content contract tests.
- [ ] Generated canonical JSON validates against the `content.v1` schema contracts.
- [ ] Known allowed exceptions are explicit and documented in test data.

**Verification:**
- `uv run python -m pytest tests/test_content_contracts.py -q`

### Task 1.2 — Replace unsafe/stale cache behavior

**Objective:** registry cache must not load unsafe pickle or stale content after wiki changes.

**Acceptance criteria:**
- [ ] Unsafe pickle cache is removed for content loading.
- [ ] `data/generated/content/manifest.json` tracks `schema_version`, source paths, content hashes, `generated_at`, and emitted interim artifact filenames/hashes.
- [ ] Runtime content loading can read safe generated JSON artifacts when present and can detect stale generated artifacts after wiki changes.
- [ ] Tests cover adding/changing a wiki file and stale generated artifacts.
- [ ] This task does not define the final canonical artifact layout; Task 1.4 owns the canonical `units/` and `faction_units/` sharded layout and must replace the interim `units.json` artifact.

**Verification:**
- `uv run python -m pytest tests/test_registry.py tests/test_content_contracts.py -q`

### Task 1.3 — Compile squad/points metadata consistently

**Objective:** one canonical squad metadata shape feeds roster validation and UI.

**Acceptance criteria:**
- [ ] `unit.squad_size` from YAML/frontmatter is authoritative.
- [ ] `model_count` is not used as roster min/max replacement.
- [ ] Single-model vehicles and transport capacity cannot be misread as squad size.

**Verification:**
- `uv run python -m pytest tests/test_parser.py tests/test_roster*.py -q`

### Task 1.4 — Emit canonical JSON artifacts

**Objective:** build a deterministic canonical-content compilation pipeline that transforms wiki/frontmatter sources into schema-validated runtime JSON artifacts keyed by stable canonical ids and consumable without direct wiki parsing at runtime.

**Acceptance criteria:**
- [ ] Compiler emits canonical artifacts under `data/generated/content/`.
- [ ] Required top-level artifacts include `manifest.json`, `factions.json`, `weapons.json`, `detachments.json`, `stratagems.json`, `enhancements.json`, `rules.json`, `units/`, and `faction_units/`.
- [ ] Large logical artifact kinds MAY be physically sharded; canonical unit definitions MUST be emitted as `units/index.json` plus `units/<owning_or_source_faction_id>.json` shards rather than one monolithic `units.json`.
- [ ] Unit definition availability MUST be emitted separately as `faction_units/index.json` plus `faction_units/<faction_id>.json` shards.
- [ ] `units/index.json` is a lightweight index keyed by `unit_id` with source/owning `faction_id`, shard `file`, `display_name`, and record `hash`.
- [ ] `faction_units/<faction_id>.json` files contain availability/link records, not duplicated unit definitions.
- [ ] Shared/common units MUST be represented once as canonical unit definitions and exposed to multiple factions through faction availability/link artifacts, not duplicated per faction.
- [ ] `manifest.json` lists every emitted top-level artifact and shard with `sha256:<hex>` hash.
- [ ] Artifacts are keyed by stable canonical ids, not display names.
- [ ] `manifest.json` includes `schema_version`, `content_hash`, source paths, generated timestamp, artifact/shard filenames and hashes, and collision/exception report references.
- [ ] Unit records include `source_path`, `display_name`, `faction_id`, stats, points, squad_size, keywords, tags, and weapon_ids where applicable.
- [ ] `CanonicalContentRegistry` loads every canonical object kind from generated JSON and loads sharded unit definitions as one logical `units` collection, with faction availability exposed through `faction_units` links.
- [ ] All generated artifacts and shards validate against strict canonical schemas before write.
- [ ] All cross-artifact references are validated during compilation.
- [ ] Duplicate canonical ids fail compilation across all shards of the same logical object kind.
- [ ] Duplicate display names emit a collision report but remain valid if canonical ids differ.
- [ ] Generated JSON output is byte-deterministic for identical source input.
- [ ] Canonical ids are deterministic, independent from display names and source file paths, and survive display/source-path changes when explicit `canonical_id` is present.
- [ ] Tests cover duplicate canonical ids across shards, duplicate display names, dangling references, renamed source files, display-name changes, deterministic rebuild output, manifest shard hashes, registry loading sharded unit definitions as one logical collection, faction availability resolving shared units, and shared/common units not being duplicated into subfaction unit-definition shards.

**Artifact layout:**
- [ ] Physical layout under `data/generated/content/` is:
  - `manifest.json`
  - `factions.json`
  - `weapons.json`
  - `detachments.json`
  - `stratagems.json`
  - `enhancements.json`
  - `rules.json`
  - `units/index.json`
  - `units/<owning_or_source_faction_id>.json`, for example `units/space-marines.json`, `units/orks.json`, `units/tau-empire.json`.
  - `faction_units/index.json`
  - `faction_units/<faction_id>.json`, for example `faction_units/blood-angels.json`, `faction_units/dark-angels.json`.
- [ ] Unit definition != faction availability: common units are stored once in `units/` and linked from every eligible faction/subfaction through `faction_units/`.
- [ ] Do not shard one file per unit; shard unit definitions by source/owning faction and shard availability by faction to keep git diffs, merge conflicts, and manifest/hash control manageable.
- [ ] The logical object kind `units` remains canonical definitions; availability is a separate logical object kind `faction_units`.

**Canonical id contract:**
- [ ] Canonical ids use frontmatter `canonical_id` / object-specific id as the authoritative owner.
- [ ] Temporary derived slug ids are allowed only for migration fixtures and must produce a collision report.
- [ ] Registry allocator and full migration-map tooling are out of scope for this task.
- [ ] Canonical ids contain only lowercase ASCII letters, digits, `_`, and `-` after the artifact-type prefix is removed.
- [ ] Canonical ids are globally unique within each artifact type.

**Schema, determinism, collisions, references:**
- [ ] `backend/loader/schemas.py` defines strict versioned `content.v1` schemas for every artifact kind, forbids undeclared fields, normalizes enums, and rejects unknown enum values.
- [ ] Deterministic rebuild means identical input content produces byte-identical generated artifacts: sorted object keys, deterministic collection ordering, normalized whitespace, and documented `sha256:<hex>` hashes.
- [ ] Deterministic rebuild tests use an injected/frozen clock for `generated_at`, or exclude `generated_at` from byte-determinism assertions.
- [ ] Duplicate canonical ids fail compilation; duplicate display names do not fail if ids differ, but emit a manifest-linked collision report.
- [ ] Dangling cross-artifact references fail compilation, including `unit.weapon_ids -> weapons.json`, `unit.faction_id -> factions.json`, `faction_units.available_unit_ids -> units`, `faction_units` keys -> `factions.json`, detachment faction links, and stratagem/enhancement/rule references.
- [ ] Compiler writes generated artifacts atomically: validate everything first, then replace generated files; failed compilation must not leave partially updated generated artifacts.

**Registry semantics:**
- [ ] `CanonicalContentRegistry` records are immutable after load.
- [ ] Registry provides typed lookup by canonical id for every artifact kind.
- [ ] Display-name lookup, if provided, is reverse-index-only and never authoritative.
- [ ] Registry load validates that all required artifacts are present and references are resolved/resolvable.

**Non-goals:** runtime gameplay logic changes, AI behavior enrichment, localization/display-name translation, registry allocator implementation, and full migration-map tooling.

**Verification:**
- `uv run python -m pytest tests/test_content_contracts.py tests/test_registry.py -q`

### Checkpoint 1

- [ ] Wiki content compiles with explicit errors.
- [ ] Canonical JSON artifacts are emitted, schema-validated, manifest-hashed, and keyed by stable ids; unit definitions may be physically sharded while remaining one registry object kind, and faction availability is represented by separate `faction_units` links.
- [ ] No unsafe/stale cache risk.
- [ ] Runtime loaders can rely on `CanonicalContentRegistry`/generated JSON instead of raw wiki reads for factions, units, weapons, detachments, stratagems, enhancements, and rules.
- [ ] Roster validator can rely on canonical metadata.

## Phase 2 — Roster validator

**Purpose:** make roster validation authoritative and shared across API, generated rosters, saved rosters, and UI expectations.

**Primary CRs:** CR-12, CR-16, CR-17, CR-19.

**Files likely touched:**
- `backend/state/roster.py`
- `web/routes/api_rosters.py`
- `web/static/team_builder.js`
- `web/templates/team_builder.html`
- `tests/test_roster*.py`
- `tests/test_api_rosters.py`

### Task 2.1 — Lock the canonical PTS formula

**Objective:** lock one backend-owned canonical squad points formula and ensure API/frontend totals consume or prove parity with that backend contract.

**Acceptance criteria:**
- [ ] Backend formula: `(points / minSquad + loadoutPts) * squadSize + nobPts`.
- [ ] There is exactly one canonical backend function for squad total points.
- [ ] All backend roster totals use stored/calculated squad `totalPts` from that canonical function.
- [ ] API responses expose `totalPts` per squad and roster `totalPts`.
- [ ] Frontend displayed totals match API/backend totals for the same roster payload.
- [ ] Frontend MUST NOT reimplement divergent business logic; it either consumes backend-calculated `totalPts` or uses a shared exported formula/test fixture generated from the backend contract.
- [ ] Do not duplicate the formula independently in multiple backend/frontend locations without shared tests proving parity.
- [ ] Roster `totalPts` equals the sum of squad `totalPts`, not a recalculation from display fields.
- [ ] Tests cover Boyz minimum squad without upgrades, Boyz expanded squad, Boyz with per-model loadout upgrade, Boyz with Nob flat upgrade, Boyz with loadout + Nob upgrade together, Nobz squad if their minSquad/squadSize behavior differs, single-model vehicle with `minSquad=1` and `squadSize=1`, and roster `totalPts` summing squad `totalPts`.

**PTS formula contract:**
- [ ] Backend owns the canonical PTS calculation.
- [ ] Frontend MUST NOT reimplement divergent business logic.
- [ ] Frontend either consumes backend-calculated `totalPts` or uses a shared exported formula/test fixture generated from backend contract.

**Formula inputs:**
- [ ] `points` = base points for minimum squad size.
- [ ] `minSquad` = minimum squad model count.
- [ ] `squadSize` = selected model count.
- [ ] `loadoutPts` = per-model upgrade/loadout points unless explicitly marked flat.
- [ ] `nobPts` = flat squad-level Nob upgrade cost.

**Non-goals:** Changing canonical points source data is not in scope; implementing full roster legality validation is not in scope; frontend redesign is not in scope.

**Verification:**
- `uv run python -m pytest tests/test_roster*.py -q`
- Browser/API smoke if frontend changed.

### Task 2.2 — Enforce exactly one Warlord when required

**Objective:** saved and generated rosters have valid Warlord semantics.

**Acceptance criteria:**
- [ ] Warlord validation lives in shared backend roster validation, not only in Team Builder UI.
- [ ] Validator rejects rosters with multiple eligible Characters and no Warlord.
- [ ] Validator rejects rosters with more than one `is_warlord: true`.
- [ ] Validator rejects `is_warlord: true` on a non-Character unit.
- [ ] API save path uses the same backend validator as generated roster validation.
- [ ] Generated rosters always persist exactly one valid Warlord when eligible Characters exist.
- [ ] Team Builder disables or warns on save when Warlord state is invalid.
- [ ] Team Builder UI visibly exposes Warlord selection and warnings.
- [ ] Tests cover zero Characters, one Character auto/valid Warlord, multiple Characters with no Warlord invalid, multiple Characters with exactly one Warlord valid, two Warlords invalid, non-Character marked as Warlord invalid, generated roster setting exactly one valid Warlord, and API rejecting invalid Warlord payload.

**Warlord validation contract:**
- [ ] Roster MUST have exactly one Warlord when at least one eligible Character exists.
- [ ] Only units with `CHARACTER` keyword/tag are eligible to be Warlord.
- [ ] If roster has exactly one eligible Character, generated rosters MAY auto-select it.
- [ ] If roster has multiple eligible Characters, saved/user-created rosters MUST explicitly select exactly one.
- [ ] If roster has zero eligible Characters, Warlord requirement is not enforced unless faction/rules data explicitly requires otherwise.

**Non-goals:** Full detachment/faction-specific Warlord trait logic is not in scope; enhancement legality is not in scope; Commander/Leader attachment rules are not in scope.

**Verification:**
- `uv run python -m pytest tests/test_roster*.py tests/test_api_rosters.py -q`
- Browser smoke `/team-builder` for crown/warning/save-disabled state.

### Task 2.3 — Enforce plan/feature gates consistently

**Objective:** Free/Premium roster limits cannot be bypassed through duplicate/import paths.

**Acceptance criteria:**
- [ ] Create, duplicate, import/generate-save paths share one validator.
- [ ] Free limit matches product requirement and UI.
- [ ] Public roster creation respects feature flags.

**Verification:**
- `uv run python -m pytest tests/test_api_rosters.py tests/test_billing*.py -q`

### Checkpoint 2

- [ ] Roster validation is shared and test-covered.
- [ ] UI/API/generated roster behavior matches.

## Phase 3 — Combat math

**Purpose:** fix core hit/wound/save/damage/FNP math before tuning gameplay or AI.

**Primary CRs:** CR-07, CR-11.

**Files likely touched:**
- `backend/engine/combat.py`
- `backend/engine/modifiers.py`
- `backend/engine/scenario.py`
- `tests/test_combat*.py`
- `tests/test_modifiers.py`

### Task 3.1 — Fix natural 6 / Lethal Hits semantics

**Objective:** natural 6 auto-wounds only when Lethal Hits applies.

**Acceptance criteria:**
- [ ] Plain natural 6 to hit does not auto-wound.
- [ ] Lethal Hits natural 6 does auto-wound.
- [ ] Critical Hit detection is separate from Lethal Hits resolution.
- [ ] Plain Critical Hits do not increment wound count unless another rule explicitly says so.
- [ ] Lethal Hits applies per attack/weapon/profile, not globally to the attacker unless sourced that way.
- [ ] Automatic wounds from Lethal Hits bypass the wound roll but still proceed to save/damage steps normally.
- [ ] Do not implement this as “natural 6 always auto-wounds”; Lethal Hits must be an explicit active rule on the attack.
- [ ] Tests cover plain hit roll of natural 6 still requiring a wound roll, failed wound roll after plain natural 6 producing no wound, Lethal Hits natural 6 skipping wound roll and creating one wound, non-6 successful hit with Lethal Hits rolling to wound normally, and a mixed attack pool with one natural 6 and one normal hit resolving correctly.

**Combat semantics contract:**
- [ ] A natural 6 to Hit is still only a successful Hit unless the attack has Lethal Hits.
- [ ] Only attacks with active Lethal Hits convert Critical Hits into automatic wounds.
- [ ] Automatic wounds from Lethal Hits bypass the wound roll but still proceed to save/damage steps normally.

**Non-goals:** Devastating Wounds, AP/save behavior, Feel No Pain, Sustained Hits, and wound allocation changes are not in scope.

**Verification:**
- `uv run python -m pytest tests/test_combat*.py tests/test_modifiers.py -q`

### Task 3.2 — Fix AP/save application and Devastating Wounds

**Objective:** AP and Devastating Wounds follow one consistent 10e-compatible path.

**Acceptance criteria:**
- [ ] AP is applied exactly once regardless of terrain/modifier combinations.
- [ ] Cover bonuses are not double-applied with save modifiers.
- [ ] Cover/save modifiers are applied at the correct stage according to the canonical modifier pipeline.
- [ ] Normal save path and Devastating Wounds path are separated and tested independently.
- [ ] Combat logs/debug state clearly identify when Devastating Wounds triggered if combat logging exists.
- [ ] Do not solve AP duplication by suppressing later save modifiers globally.
- [ ] Tests cover AP modifying save exactly once, cover modifying save at the correct stage, AP and cover interaction producing expected effective save, normal wound using standard save path, Critical Wound without Devastating Wounds using standard save path, Critical Wound with Devastating Wounds bypassing normal save path, and Devastating Wounds damage reaching post-damage mitigation/FNP layers if implemented.

**Save/AP resolution contract:**
- [ ] AP modifies the defender save characteristic exactly once during save resolution.
- [ ] Cover and other save modifiers apply after AP according to the canonical modifier pipeline.
- [ ] Modified saves respect system caps/floor rules implemented by the engine.
- [ ] Save characteristic modification and save-roll modification are treated as separate stages if both exist.

**Devastating Wounds contract:**
- [ ] Devastating Wounds only triggers on Critical Wounds.
- [ ] Devastating Wounds converts damage from the triggering attack into mortal wounds according to current supported 10e semantics.
- [ ] Devastating Wounds bypasses normal armor saves once triggered.
- [ ] Feel No Pain and other post-damage defenses still apply if supported elsewhere by the engine.

**Non-goals:** Invulnerable save redesign, full terrain-system rewrite, and Damage spillover/allocation redesign are not in scope.

**Verification:**
- `uv run python -m pytest tests/test_combat*.py tests/test_terrain*.py -q`

### Task 3.3 — Fix Sustained Hits resolution

**Objective:** extra hits are resolved as real hit results, not dropped/no-op metadata.

**Acceptance criteria:**
- [ ] Sustained Hits adds correct additional hits.
- [ ] Downstream wound/save/damage counts include the extra hits.
- [ ] Hit resolution output includes both original hits and Sustained Hits extra hits.
- [ ] Downstream wound pool consumes the expanded hit count.
- [ ] Combat trace/log, if present, distinguishes original hits from Sustained Hits extra hits.
- [ ] Sustained Hits and Lethal Hits can coexist without dropping either effect.
- [ ] Do not represent Sustained Hits only as metadata; the extra hits must become downstream-resolvable hit entries or counts.
- [ ] Tests cover no Critical Hits producing no extra hits, one Critical Hit with Sustained Hits 1 producing two total hits, one Critical Hit with Sustained Hits 2 producing three total hits, extra hits rolling to wound normally, extra hits not being treated as auto-wounds from Lethal Hits, a mixed pool with normal hits/Critical Hits/misses, and Sustained Hits + Lethal Hits on the same natural 6 where the original Critical Hit can auto-wound via Lethal Hits while extra Sustained Hits roll to wound normally.

**Sustained Hits contract:**
- [ ] Sustained Hits triggers only on Critical Hits.
- [ ] Sustained Hits X adds X additional hit results for each triggering Critical Hit.
- [ ] Additional hits are normal successful hits, not Critical Hits.
- [ ] Additional hits continue into wound/save/damage resolution.
- [ ] Additional hits do not recursively trigger Sustained Hits or other Critical Hit effects.

**Non-goals:**
- [ ] Changing Lethal Hits semantics is not in scope.
- [ ] Changing Devastating Wounds/AP/save behavior is not in scope.
- [ ] Full combat log redesign is not in scope.

**Verification:**
- `uv run python -m pytest tests/test_modifiers.py tests/test_combat*.py -q`

### Checkpoint 3

- [ ] Focused combat tests pass.
- [ ] Existing scenario tests still pass.

## Phase 4 — Game state / VP / phase invariants

**Purpose:** lock 10e phase flow, CP/VP, battle-shock, objective control, and end-game invariants.

**Primary CRs:** CR-08, CR-10, CR-14, CR-24.

**Files likely touched:**
- `backend/state/game_state.py`
- `backend/state/mission.py`
- `backend/engine/scenario.py`
- `backend/engine/ai/autoplay.py`
- `tests/test_game_state.py`
- `tests/test_scenario.py`
- `tests/test_mission*.py`
- `tests/test_autoplay.py`

### Task 4.1 — Assert 5-phase 10e loop invariants

**Objective:** Command -> Movement -> Shooting -> Charge -> Fight only.

**Acceptance criteria:**
- [ ] GamePhase has exactly 5 members.
- [ ] Battle-shock runs in Command, not separate Morale.
- [ ] Round increments after Fight only.
- [ ] Phase progression uses one canonical ordered phase list.
- [ ] Autoplay/scenario code consumes the same phase order, not duplicated hardcoded lists.
- [ ] Replay/snapshot phase names match the canonical GamePhase values.
- [ ] No tests or UI paths expect a separate Morale phase.
- [ ] Do not fix this by aliasing Morale/Battle-shock to Command while keeping them as phase enum members.
- [ ] Tests cover GamePhase having exactly five members, phase order being Command -> Movement -> Shooting -> Charge -> Fight, advancing from Fight moving to the next player/round boundary as designed, battle-shock hooks running during Command phase, no separate Morale phase appearing in snapshots/replay/scenario progression, and autoplay completing a full turn using only the five phases.

**Phase loop contract:**
- [ ] GamePhase MUST contain exactly `COMMAND`, `MOVEMENT`, `SHOOTING`, `CHARGE`, and `FIGHT`.
- [ ] GamePhase MUST NOT contain `MORALE`, `BATTLESHOCK`, `PSYCHIC`, or `END` as runtime phase loop enum members.
- [ ] Battle-shock is resolved as a Command phase step.
- [ ] Round advances only after both players complete Fight phase, or after the engine's existing full-round boundary if turns are modeled differently.

**Non-goals:**
- [ ] Full battle-shock rules implementation is not in scope.
- [ ] Mission scoring redesign is not in scope.
- [ ] Turn/round persistence redesign is not in scope unless required to remove invalid phase states.

**Verification:**
- `uv run python -m pytest tests/test_game_state.py tests/test_scenario.py -q`

### Task 4.2 — Lock CP and battle-shock reset semantics

**Objective:** CP starts at 0, each player gains CP only at the start of their own Command phase, and reset semantics are split across explicit turn and round boundaries.

**CP / reset semantics contract:**
- [ ] Both players start the game with 0 CP.
- [ ] Each player gains exactly +1 CP at the start of their own Command phase unless a future explicit rule modifies this.
- [ ] CP gain happens once per player turn, not once per phase transition and not once per full battle round.
- [ ] Repeated Command phase processing is idempotent for CP unless the call explicitly advances turn state.
- [ ] The opponent does not gain CP during the active player’s Command phase.
- [ ] There is no Warlord-based starting CP and no Warlord-based bonus CP.
- [ ] `is_battle_shocked` is cleared only during that unit owner’s Command phase reset step.
- [ ] Battle-shock reset does not occur during Movement, Shooting, Charge, or Fight.
- [ ] `has_advanced` is cleared at the start of a new battle round before any unit acts.
- [ ] Round-level flags and turn-level flags are reset at separate explicit boundaries.
- [ ] Do not hide old Warlord CP behavior behind default config or compatibility paths.

**Acceptance criteria:**
- [ ] Both players start with 0 CP.
- [ ] Active player gains +1 CP on their own Command phase.
- [ ] Opponent does not gain CP during active player Command phase.
- [ ] No Warlord CP bonus is applied.
- [ ] CP gain happens once per player turn, not once per phase transition or full round.
- [ ] Repeated Command phase processing is idempotent for CP unless explicitly advancing turn state.
- [ ] `is_battle_shocked` clears in Command only, during that unit owner’s Command phase reset step.
- [ ] `is_battle_shocked` remains set through Movement, Shooting, Charge, and Fight.
- [ ] `has_advanced` resets at the new battle-round boundary before any unit acts.
- [ ] Round-level flags and turn-level flags are reset at separate explicit boundaries.

**Tests:**
- [ ] Both players start with 0 CP.
- [ ] Player gains +1 CP on own Command phase.
- [ ] Opponent does not gain CP during active player Command phase.
- [ ] No Warlord CP bonus is applied.
- [ ] Battle-shock clears in Command only.
- [ ] Battle-shock remains set through non-Command phases.
- [ ] `has_advanced` clears at new round boundary.
- [ ] CP is not double-awarded when snapshots, replay, or autoplay touch Command logic.

**Non-goals:**
- [ ] Stratagem CP spending/refund rules are not in scope.
- [ ] Faction-specific CP generation is not in scope.
- [ ] Full battle-shock test/rules implementation is not in scope.

**Verification:**
- `uv run python -m pytest tests/test_game_state.py tests/test_scenario.py -q`

### Task 4.3 — Lock VP, objectives, mission normalization, Battle Ready

**Objective:** VP source is deterministic, 10e-aligned, and shared by runtime, replay, result screen, and autoplay.

**VP / mission scoring contract:**
- [ ] Primary/dynamic VP scoring uses one canonical scoring pipeline shared by runtime, replay, result screen, and autoplay.
- [ ] Mission names are normalized before lookup/comparison using a deterministic normalization function.
- [ ] Battle Ready is a post-game bonus applied exactly once to the final authoritative VP state.
- [ ] Intermediate snapshots MAY omit Battle Ready, but final authoritative state MUST include it.
- [ ] Final authoritative VP state is the single source of truth for result screens and replay summaries.
- [ ] Do not solve mission normalization by duplicating alias maps independently across runtime/UI/replay layers.

**Acceptance criteria:**
- [ ] Mission normalization treats whitespace, casing, underscores, and hyphens consistently.
- [ ] Objective scoring values are sourced from normalized mission definitions, not hardcoded ad-hoc comparisons.
- [ ] Dynamic objectives: Only War 3 VP, Take and Hold 5 VP, Purge the Foe 5 VP.
- [ ] Battle Ready +10 VP is applied exactly once and visible in final authoritative state.
- [ ] Replay, result screen, and final snapshot display the same final VP totals.
- [ ] Game termination is driven by round cap, army wipe/table state, and explicit mission-end conditions, not arbitrary VP thresholds.
- [ ] Game does not end early at `VP >= 10`.

**Tests:**
- [ ] Mission name normalization with spaces, hyphens, underscores, and case variants.
- [ ] Only War dynamic objective awards 3 VP.
- [ ] Take and Hold awards 5 VP.
- [ ] Purge the Foe awards 5 VP.
- [ ] Battle Ready applies exactly once.
- [ ] Repeated finalization does not duplicate Battle Ready.
- [ ] Final replay/result snapshot includes Battle Ready VP.
- [ ] Game does not end at `VP >= 10`.
- [ ] Game ends correctly by round cap or wipe condition.

**Non-goals:**
- [ ] Secondary objective system redesign is not in scope.
- [ ] Tournament scoring variants are not in scope.
- [ ] UI redesign for result presentation is not in scope.

**Verification:**
- `uv run python -m pytest tests/test_mission*.py tests/test_autoplay.py tests/test_result_screen.py -q`

### Checkpoint 4

- [ ] Game loop invariants pass.
- [ ] VP/final score agrees across runtime, API, and planned replay contract.

## Phase 5 — Movement / charge / melee identity

**Purpose:** make movement, charge, engagement, melee damage, and unit identity coherent before replay/result and AI.

**Primary CRs:** CR-09, CR-11, CR-14, CR-15.

**Files likely touched:**
- `backend/engine/scenario.py`
- `backend/state/game_state.py`
- `backend/state/map.py`
- `backend/engine/ai/decision.py`
- `tests/test_movement*.py`
- `tests/test_scenario.py`
- `tests/test_autoplay.py`

### Task 5.1 — Fix charge destination and engagement identity

**Objective:** charge moves to adjacent legal cell and marks scoped units as engaged.

**Acceptance criteria:**
- [ ] Charge never attempts to occupy enemy cell.
- [ ] Engagement uses runtime ids, not names.
- [ ] Same-name mirrored units can engage independently.

**Verification:**
- `uv run python -m pytest tests/test_movement*.py tests/test_scenario.py -q`

### Task 5.2 — Fix melee target selection and damage logging

**Objective:** melee resolves adjacent targets and logs parsable damage with actor/target identity.

**Acceptance criteria:**
- [ ] Adjacent melee attacks resolve.
- [ ] Damage log/event uses `hits ... for ... damage` or structured equivalent.
- [ ] Summary attribution is not name-based.

**Verification:**
- `uv run python -m pytest tests/test_scenario.py tests/test_result_screen.py -q`

### Task 5.3 — Fix terrain/LoS movement-related blockers

**Objective:** terrain/LoS cache and cover integration do not corrupt movement/shooting assumptions.

**Acceptance criteria:**
- [ ] `set_terrain()` invalidates LoS cache.
- [ ] Cover helper argument order is correct.
- [ ] AP0 cover cap is enforced.

**Verification:**
- `uv run python -m pytest tests/test_terrain*.py tests/test_scenario.py -q`

### Checkpoint 5

- [ ] Melee units can move, charge, engage, and deal damage.
- [ ] Duplicate unit names do not corrupt movement/melee/result attribution.

## Phase 6 — Replay/result authoritative state

**Purpose:** make persisted replay and result pages derive from one authoritative final state.

**Primary CRs:** CR-14, CR-18, CR-24.

**Files likely touched:**
- `backend/engine/ai/autoplay.py`
- `backend/engine/replay.py`
- `web/routes/api_replays.py`
- `web/static/replay_viewer.js`
- `web/static/result_chart.js`
- `web/templates/result.html`
- `tests/test_replay.py`
- `tests/test_round_viewer.py`
- `tests/test_result_screen.py`

### Task 6.1 — Persist authoritative final snapshot

**Objective:** final replay/result state includes all post-game scoring and final unit state.

**Acceptance criteria:**
- [ ] Battle Ready VP is included in final persisted state.
- [ ] `/api/results/{game_id}` and `/result/{game_id}` show same final VP.
- [ ] VP chart/stat cards use the same authoritative source.

**Verification:**
- `uv run python -m pytest tests/test_replay.py tests/test_result_screen.py -q`
- Deterministic generated replay smoke.

### Task 6.2 — Fix event parsing and summary attribution

**Objective:** result summaries derive from scoped ids/structured events, not ambiguous display names.

**Acceptance criteria:**
- [ ] Kills/damage/charges attributed correctly in same-faction/same-name games.
- [ ] VP logs with totals and Battle Ready parse as VP events or are represented by structured final state.
- [ ] Player 2 charge card can show non-zero normal events.

**Verification:**
- `uv run python -m pytest tests/test_result_screen.py tests/test_replay.py -q`

### Task 6.3 — Add repeatable final gate smoke script

**Objective:** replace ad-hoc `/tmp` CR-24 replay probes with repo-owned smoke.

**Acceptance criteria:**
- [ ] Script creates deterministic isolated replay/result smoke.
- [ ] Script asserts runtime VP, API VP, and result payload/page VP match.
- [ ] Script uses isolated DB or cleans up its data.

**Files likely touched:**
- Create: `scripts/smoke_final_gate.py`
- Test: `tests/test_final_gate_smoke.py` or direct script invocation documented in CR-24.

**Verification:**
- `uv run python scripts/smoke_final_gate.py`

### Checkpoint 6

- [ ] Replay/result identity and final state are authoritative.
- [ ] CR-24 result VP bug is fixed and covered.

## Phase 7 — API/auth/persistence hardening

**Purpose:** close release blockers around public boundaries, auth/ownership, billing gates, deployment safety, and DB persistence.

**Primary CRs:** CR-02, CR-03, CR-04, CR-05, CR-13, CR-19, CR-20, CR-22.

**Files likely touched:**
- `backend/auth/__init__.py`
- `backend/auth/providers/*`
- `backend/billing/*`
- `backend/db/database.py`
- `web/routes/api.py`
- `web/routes/api_rosters.py`
- `web/routes/api_replays.py`
- `web/routes/auth.py`
- `main.py`
- `tests/test_auth*.py`
- `tests/test_billing*.py`
- `tests/test_api*.py`
- `tests/test_deployment*.py`

### Task 7.1 — Fail closed on secrets/JWT/webhook config

**Objective:** production cannot run with insecure fallback secrets or unsigned billing webhooks.

**Acceptance criteria:**
- [ ] HOSTING/production requires explicit JWT secret.
- [ ] Stripe webhook rejects unsigned/invalid events.
- [ ] No secret values are printed in logs or committed test files.

**Verification:**
- `uv run python -m pytest tests/test_auth*.py tests/test_billing*.py tests/test_deployment*.py -q`

### Task 7.2 — Enforce ownership on roster/replay/subscription APIs

**Objective:** users can only read/write their own protected resources.

**Acceptance criteria:**
- [ ] Roster CRUD checks owner.
- [ ] Replay list/detail respects public/private/owner policy.
- [ ] Subscription/portal endpoints are user-bound.

**Verification:**
- `uv run python -m pytest tests/test_api_rosters.py tests/test_api_replays.py tests/test_auth*.py -q`

### Task 7.3 — Enforce billing/feature gates consistently

**Objective:** Free/Premium constraints match product and cannot be bypassed.

**Acceptance criteria:**
- [ ] Auto-play quota/auth gate is enforced or explicitly disabled from paid claims.
- [ ] Free roster limit matches UI/product requirement.
- [ ] `/api/me` exposes feature flags/trial state needed by UI.
- [ ] `require_tier()` is implemented or removed from claims.

**Verification:**
- `uv run python -m pytest tests/test_billing*.py tests/test_api*.py -q`

### Task 7.4 — Production hardening pass

**Objective:** deployment route and runtime safety issues are closed.

**Acceptance criteria:**
- [ ] Public `/sentry-debug` is disabled outside local/dev explicit mode.
- [ ] CSP decision is documented and tested; if enabled, browser still works.
- [ ] Rate limiting is production-appropriate or accepted with explicit deployment guardrail.
- [ ] Error responses include request id where expected.

**Verification:**
- `uv run python -m pytest tests/test_deployment*.py tests/test_api*.py -q`

### Checkpoint 7

- [ ] Auth/ownership/billing/production P0 blockers are closed.
- [ ] Full tests pass.
- [ ] Local server `/api/health` smoke passes.

## Phase 8 — AI integration

**Purpose:** wire AI decisions into already-stable movement/combat/game-state contracts.

**Primary CRs:** CR-15, CR-17.

**Files likely touched:**
- `backend/engine/ai/decision.py`
- `backend/engine/ai/faction_ai.py`
- `backend/engine/ai/deployment.py`
- `backend/engine/ai/autoplay.py`
- `backend/engine/scenario.py`
- `wiki/factions/*.md`
- `tests/test_faction_ai.py`
- `tests/test_ai_decision.py`
- `tests/test_autoplay.py`

### Task 8.1 — Use decision engine in live scenario phases

**Objective:** F3.1/F3.2 decision logic is not dead code.

**Acceptance criteria:**
- [ ] Movement/shooting/charge phases call decision engine or a documented adapter.
- [ ] `EvaluationContext.faction_profile` reaches scoring functions.
- [ ] Tests prove a faction profile changes decisions.

**Verification:**
- `uv run python -m pytest tests/test_ai_decision.py tests/test_faction_ai.py tests/test_autoplay.py -q`

### Task 8.2 — Fix behavior overrides and target priorities

**Objective:** faction profile weights/overrides affect runtime behavior predictably.

**Acceptance criteria:**
- [ ] `action_override` is honored or removed from schema/docs.
- [ ] Target multipliers below 1.0 can de-prioritize targets.
- [ ] Behavior activation marks behavior used once as intended.

**Verification:**
- `uv run python -m pytest tests/test_faction_ai.py tests/test_ai_decision.py -q`

### Task 8.3 — Verify deployment objectives and faction styles

**Objective:** Orks, Tau, and AdMech exhibit distinct deployment/movement tendencies from profile weights.

**Acceptance criteria:**
- [ ] Orks melee units bias toward engagement.
- [ ] Tau ranged units prefer ranged positioning/targets.
- [ ] Deployment uses faction profile role preferences.

**Verification:**
- `uv run python -m pytest tests/test_autoplay.py tests/test_faction_ai.py -q`
- Deterministic scenario probes with fixed seed.

### Checkpoint 8

- [ ] AI is integrated into live autoplay/scenario paths.
- [ ] Faction styles are observable and test-covered.

## Final CR-24 re-run

After phases 0-8:

1. Reconcile CR report counts:
   - Normalize CR frontmatter/counts or regenerate `code-review.md` from reports.
2. Run final static gates:
   - `uv run ruff check .`
   - `uv run ruff format --check .`
   - `node -c web/static/team_builder.js`
   - `node -c web/static/scenario_setup.js`
   - `node -c web/static/battlefield_map.js`
3. Run full tests:
   - `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/ -q`
4. Start server without reload:
   - `uv run python3 -c "import uvicorn; uvicorn.run('main:app', host='127.0.0.1', port=8000, reload=False)"`
5. Check health:
   - `curl -i -sS http://127.0.0.1:8000/api/health`
6. Browser smoke:
   - `/`
   - `/team-builder`
   - `/scenario-setup`
   - `/my-rosters`
   - `/result/<generated_game_id>`
7. Run final result consistency smoke:
   - `uv run python scripts/smoke_final_gate.py`
8. Update:
   - `docs/reviews/2026-05-10/triage-summary.md`
   - `docs/requirements/code-review/code-review.md`
   - affected CR artifacts
   - docs/indexes if feature/code docs changed.

## Exit criteria

- [ ] P0 release blocker group has zero open Critical/Important items.
- [ ] P1 core correctness group has zero open Critical items and all Important items fixed or explicitly accepted with guardrails.
- [ ] P2 important debt is either fixed or listed in Accepted/postponed with owner/date/guardrail.
- [ ] Final CR-24 gate passes.
- [ ] `triage-summary.md` and `code-review.md` counts match the CR artifacts.
- [ ] Full tests/lint/browser smoke evidence is recorded in the final CR-24 report.
