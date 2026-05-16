---
title: "Task 1.4 — Emit canonical JSON artifacts"
parent: remediation-plan
status: pending
phase: "1 — Content compiler / schemas"
task_id: "1.4"
source: remediation-plan.md
---

# Task 1.4 — Emit canonical JSON artifacts

**Index:** [index.md](index.md)
**Source plan:** [remediation-plan.md](remediation-plan.md)
**Previous:** [1.3 — Compile squad/points metadata consistently](task-01-03-compile-squad-points-metadata-consistently.md)
**Next:** [2.1 — Lock the canonical PTS formula](task-02-01-lock-the-canonical-pts-formula.md)

## Phase context

**Phase:** 1 — Content compiler / schemas
**Purpose:** make wiki/frontmatter content compile into validated schemas before runtime use.
**Primary CRs:** CR-06, CR-11, CR-12, CR-21.
**Dependencies:** [1.3 — Compile squad/points metadata consistently](task-01-03-compile-squad-points-metadata-consistently.md)

## Objective

Build a deterministic canonical-content compilation pipeline that transforms wiki/frontmatter sources into schema-validated runtime JSON artifacts keyed by stable canonical ids and consumable without direct wiki parsing at runtime.

## Acceptance criteria

- [ ] Compiler emits canonical artifacts under `data/generated/content/` or an explicitly configured generated-content directory.
- [ ] Required top-level artifacts include `manifest.json`, `factions.json`, `weapons.json`, `detachments.json`, `stratagems.json`, `enhancements.json`, `rules.json`, `units/`, and `faction_units/`.
- [ ] Large logical artifact kinds MAY be physically sharded; canonical unit definitions MUST be emitted as `units/index.json` plus `units/<owning_or_source_faction_id>.json` shards rather than one monolithic `units.json`.
- [ ] Unit definition availability MUST be emitted separately as `faction_units/index.json` plus `faction_units/<faction_id>.json` shards.
- [ ] `units/index.json` is a lightweight index keyed by `unit_id` with source/owning `faction_id`, shard `file`, `display_name`, and record `hash`.
- [ ] `units/<owning_or_source_faction_id>.json` files contain canonical unit definition records keyed by stable canonical unit ids.
- [ ] `faction_units/index.json` is a lightweight index keyed by `faction_id` with shard `file`, availability record `hash`, and counts.
- [ ] `faction_units/<faction_id>.json` files contain availability/link records, not duplicated unit definitions.
- [ ] Shared/common units MUST be represented once as canonical unit definitions and exposed to multiple factions through faction availability/link artifacts, not duplicated per faction.
- [ ] `manifest.json` lists every emitted top-level artifact and every emitted shard with `sha256:<hex>` hash, including `units/index.json`, each `units/<owning_or_source_faction_id>.json`, `faction_units/index.json`, and each `faction_units/<faction_id>.json`.
- [ ] Artifacts are keyed by stable canonical ids, not display names.
- [ ] `manifest.json` includes `schema_version`, `content_hash`, source paths, generated timestamp, artifact/shard filenames and hashes, and collision/exception report references.
- [ ] Unit records include `source_path`, `display_name`, `faction_id`, stats, points, squad_size, keywords, tags, and weapon_ids where applicable.
- [ ] `CanonicalContentRegistry` loads every canonical object kind from generated JSON: factions, units, weapons, detachments, stratagems, enhancements, and rules.
- [ ] `CanonicalContentRegistry` loads sharded artifacts as one logical object kind, so callers query `units` without caring that records are physically stored by faction shard.
- [ ] All generated artifacts and shards validate against strict canonical schemas before write.
- [ ] All cross-artifact references are validated during compilation.
- [ ] Duplicate canonical ids fail compilation across all shards of the same logical object kind.
- [ ] Duplicate display names emit a collision report but remain valid if canonical ids differ.
- [ ] Generated JSON output is byte-deterministic for identical source input.
- [ ] Canonical ids are deterministic, independent from display names and source file paths, and survive display/source-path changes when explicit `canonical_id` is present.
- [ ] Tests cover duplicate canonical ids across shards, duplicate display names, dangling references, renamed source files, display-name changes, deterministic rebuild output, manifest shard hashes, and registry loading sharded units as one logical collection.

## Artifact layout contract

The logical artifact kind is still `units`, but physical storage MUST be sharded by canonical unit definition ownership/source faction to keep generated JSON reviewable and merge-friendly. Do not emit a single monolithic `units.json` for all units. Availability is a separate logical artifact kind: `faction_units`.

Unit definition != faction availability. A shared/common datasheet is stored once as a canonical unit definition, then exposed to each faction/subfaction by availability/link records.

```text
data/generated/content/
  manifest.json
  factions.json
  weapons.json
  detachments.json
  stratagems.json
  enhancements.json
  rules.json
  units/
    index.json
    space-marines.json
    orks.json
    tau-empire.json
  faction_units/
    index.json
    space-marines.json
    blood-angels.json
    dark-angels.json
```

`units/index.json` is the unit-definition lookup/index layer. It MUST be small enough to diff quickly and MUST map each canonical `unit_id` to at least:

```json
{
  "unit:space-marines:intercessor-squad": {
    "faction_id": "faction:space-marines",
    "file": "units/space-marines.json",
    "display_name": "Intercessor Squad",
    "hash": "sha256:<record_hash>"
  }
}
```

`units/<owning_or_source_faction_id>.json` contains canonical unit definitions, not availability copies. Example:

```json
{
  "unit:space-marines:intercessor-squad": {
    "display_name": "Intercessor Squad",
    "faction_id": "faction:space-marines",
    "keywords": ["adeptus astartes", "imperium", "infantry"],
    "weapon_ids": ["weapon:space-marines:bolt-rifle"]
  }
}
```

`faction_units/<faction_id>.json` contains faction availability/link records. Example:

```json
{
  "faction:blood-angels": {
    "available_unit_ids": [
      "unit:space-marines:intercessor-squad",
      "unit:blood-angels:death-company-marines"
    ]
  }
}
```

Shared units such as `Intercessor Squad` MUST NOT be duplicated into every Space Marines subfaction shard. Blood Angels, Dark Angels, Ultramarines, etc. link to the one shared canonical unit definition. Unique faction units live in their own definition shard and are also exposed through that faction's availability record.

The compiler MAY later shard other large logical kinds, for example weapons by faction/source, but this task only requires unit-definition and faction-availability sharding. Do not shard one file per unit; that creates too many small files and makes manifest/hash control noisier.

## Canonical id contract

- Stable canonical ids MUST be deterministic.
- Stable canonical ids MUST be independent from source file path.
- Stable canonical ids MUST survive display name changes when explicit `canonical_id` is present.
- Stable canonical ids MUST contain only lowercase ASCII letters, digits, `_`, and `-` after the artifact-type prefix is removed.
- Stable canonical ids MUST be globally unique within each artifact type.
- Canonical ids MUST NOT be generated from `display_name` when an explicit `canonical_id` exists.
- Canonical id ownership order is explicit:
  1. frontmatter `canonical_id` / object-specific id is authoritative.
  2. Temporary derived slug is allowed only for migration fixtures and MUST produce a collision report.
  3. Registry allocator is out of scope for this task.
  4. Migration map is out of scope for this task except as a documented future input.

## Schema contract

- `backend/loader/schemas.py` defines versioned `content.v1` schemas for every artifact kind.
- Schemas MUST run in strict mode and forbid undeclared extra fields.
- Schemas MUST normalize enums and reject unknown enum values.
- Compiler MUST validate generated records against strict canonical schemas before writing JSON artifacts.
- A schema validation failure MUST fail compilation and MUST NOT write partial updated artifacts.

## Deterministic rebuild contract

Deterministic rebuild means identical input content produces byte-identical generated artifacts:

- JSON output uses stable serialization formatting.
- Object keys are sorted deterministically.
- Collections are serialized in deterministic order after normalization.
- Whitespace is normalized before hashing and serialization.
- Content hashes use a single documented algorithm, `sha256`, with the `sha256:<hex>` string form.
- Manifest artifact hashes remain stable across repeated runs with unchanged source content.
- Deterministic rebuild tests MUST use an injected/frozen clock for `generated_at`, or exclude `generated_at` from byte-determinism assertions.

## Collision and reference behavior

- Duplicate canonical ids MUST fail compilation.
- Duplicate display names MUST NOT fail compilation when canonical ids differ, but MUST emit a collision report referenced from `manifest.json`.
- Dangling cross-artifact references MUST fail compilation, including `unit.weapon_ids -> weapons.json`, `unit.faction_id -> factions.json`, detachment faction links, stratagem/enhancement/rule references, and any object-specific relationship added to `content.v1`.
- Manifest MUST report build status as failed/succeeded for the attempted compilation or the compiler MUST fail before replacing prior generated artifacts.
- Compiler writes generated artifacts atomically: validate everything first, then replace generated files.

## Registry semantics

- `CanonicalContentRegistry` is loaded from generated JSON artifacts, not raw wiki markdown.
- Registry records are immutable after load.
- Registry provides typed lookup by canonical id for every artifact kind.
- Display-name lookup, if provided, is reverse-index-only and MUST NOT be authoritative.
- Registry load validates that all required artifacts are present and that cross-artifact references are already resolved or resolvable.

## Non-goals

- Runtime gameplay logic changes are not in scope.
- AI behavior enrichment is not in scope.
- Localization/display-name translation is not in scope.
- Registry allocator implementation is not in scope.
- Full migration-map tooling is not in scope.

## Files likely touched

- `backend/loader/compiler.py`
- `backend/loader/schemas.py`
- `backend/loader/registry.py`
- `backend/loader/parser.py`
- `backend/model/unit.py`
- `data/generated/content/manifest.json`
- `data/generated/content/factions.json`
- `data/generated/content/weapons.json`
- `data/generated/content/detachments.json`
- `data/generated/content/stratagems.json`
- `data/generated/content/enhancements.json`
- `data/generated/content/rules.json`
- `data/generated/content/units/index.json`
- `data/generated/content/units/<owning_or_source_faction_id>.json` definition shards, e.g. `space-marines.json`, `orks.json`, `tau-empire.json`
- `data/generated/content/faction_units/index.json`
- `data/generated/content/faction_units/<faction_id>.json` availability/link shards, e.g. `blood-angels.json`, `dark-angels.json`
- `tests/test_content_contracts.py`
- `tests/test_registry.py`

## Verification

- [ ] `uv run python -m pytest tests/test_content_contracts.py tests/test_registry.py -q`

## Completion requirements

- [ ] Implementation/change is complete for this task only; do not batch unrelated fixes.
- [ ] Regression evidence is recorded in the affected CR artifact(s).
- [ ] Phase 1 completion artifact states that canonical JSON artifacts are emitted for factions, units (canonical definitions physically sharded by source/owning faction), faction_units (availability/link shards), weapons, detachments, stratagems, enhancements, and rules; schema-validated; manifest-hashed; and keyed by stable ids.
- [ ] Update `docs/reviews/2026-05-10/triage-summary.md`, affected `docs/requirements/code-review/cr-XX-*.md`, and `docs/requirements/code-review/code-review.md` with the Phase 1 completion artifact.
- [ ] `git diff --check` passes for touched files.
