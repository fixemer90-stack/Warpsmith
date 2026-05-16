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

- [ ] Compiler emits `factions.json`, `units.json`, `weapons.json`, `detachments.json`, `stratagems.json`, `enhancements.json`, and `rules.json` under `data/generated/content/` or an explicitly configured generated-content directory.
- [ ] Artifacts are keyed by stable canonical ids, not display names.
- [ ] `manifest.json` includes `schema_version`, `content_hash`, source paths, generated timestamp, all artifact filenames/hashes, and collision/exception report references.
- [ ] Unit records include `source_path`, `display_name`, `faction_id`, stats, points, squad_size, keywords, tags, and weapon_ids where applicable.
- [ ] `CanonicalContentRegistry` loads every canonical object kind from generated JSON: factions, units, weapons, detachments, stratagems, enhancements, and rules.
- [ ] All generated artifacts validate against strict canonical schemas before write.
- [ ] All cross-artifact references are validated during compilation.
- [ ] Duplicate canonical ids fail compilation.
- [ ] Duplicate display names emit a collision report but remain valid if canonical ids differ.
- [ ] Generated JSON output is byte-deterministic for identical source input.
- [ ] Canonical ids are deterministic, independent from display names and source file paths, and survive display/source-path changes when explicit `canonical_id` is present.
- [ ] Tests cover duplicate canonical ids, duplicate display names, dangling references, renamed source files, display-name changes, and deterministic rebuild output.

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
- `data/generated/content/units.json`
- `data/generated/content/weapons.json`
- `data/generated/content/detachments.json`
- `data/generated/content/stratagems.json`
- `data/generated/content/enhancements.json`
- `data/generated/content/rules.json`
- `tests/test_content_contracts.py`
- `tests/test_registry.py`

## Verification

- [ ] `uv run python -m pytest tests/test_content_contracts.py tests/test_registry.py -q`

## Completion requirements

- [ ] Implementation/change is complete for this task only; do not batch unrelated fixes.
- [ ] Regression evidence is recorded in the affected CR artifact(s).
- [ ] Phase 1 completion artifact states that canonical JSON artifacts are emitted for factions, units, weapons, detachments, stratagems, enhancements, and rules; schema-validated; and keyed by stable ids.
- [ ] Update `docs/reviews/2026-05-10/triage-summary.md`, affected `docs/requirements/code-review/cr-XX-*.md`, and `docs/requirements/code-review/code-review.md` with the Phase 1 completion artifact.
- [ ] `git diff --check` passes for touched files.
