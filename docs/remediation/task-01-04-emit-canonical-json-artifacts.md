---
title: "Task 1.4 — Emit canonical JSON artifacts"
parent: remediation-plan
status: completed
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
**Primary CRs:** CR-06, CR-11, CR-12, CR-21.
**Dependencies:** [1.3 — Compile squad/points metadata consistently](task-01-03-compile-squad-points-metadata-consistently.md)

## Objective

Deterministic canonical-content compilation pipeline producing schema-validated JSON artifacts keyed by stable canonical ids.

## Acceptance criteria (all 50+ met — key highlights)

- [x] Compiler emits artifacts under `data/generated/content/`
- [x] Required artifacts: `manifest.json`, `factions.json`, `weapons.json`, `detachments.json`, `stratagems.json`, `enhancements.json`, `rules.json`, `units/`, `faction_units/`
- [x] Units sharded by faction: `units/index.json` + `units/<faction>.json`
- [x] Faction availability: `faction_units/index.json` + `faction_units/<faction>.json`
- [x] `manifest.json` has schema_version, content_hash, source_hashes, all artifact sha256 hashes, collision report
- [x] Schema-validated before write (UnitV1Strict, WeaponV1, etc. — extra="forbid")
- [x] Canonical IDs: deterministic, format `type:scope:name` — e.g. `unit:orks:boyz`
- [x] `CanonicalContentRegistry` loads all artifact kinds, resolves faction_units→units links
- [x] Duplicate IDs fail, duplicate display names emit collision report
- [x] Dangling cross-refs (unit→faction, detachment→faction) detected
- [x] Deterministic rebuild: sorted keys, stable serialization
- [x] Rules artifact emitted (placeholder)

## Changed files

- `backend/loader/compiler.py` — full rewrite: sharding, canonical IDs, schema validation, deterministic JSON
- `backend/loader/schema.py` — strict content.v1 schemas for all artifact kinds
- `backend/loader/registry.py` — CanonicalContentRegistry class
- `tests/test_content_contracts.py` — updated for sharded layout
- `data/generated/content/` — 15 generated JSON artifacts

## Verification

- [x] `uv run python -m pytest tests/test_content_contracts.py -q` — 23 passed.
- [x] Compiler outputs: 15 artifacts, 0 critical collisions (1 dangling ref expected: core detachments).
- [x] `uv run ruff check backend/loader/` — All checks passed.
- [x] `uv run ruff format --check backend/loader/` — Already formatted.

## Completion requirements

- [x] Implementation/change is complete for this task only.
- [x] Regression evidence in CR artifacts.
- [x] Phase 1 completion artifact: see below.
- [x] `git diff --check` passes.

## Phase 1 — Content compiler / schemas — COMPLETE

All Phase 1 tasks (1.1, 1.2, 1.3, 1.4) done:

| Task | Key result |
|------|-----------|
| 1.1 — Content contract tests | 23 tests, content.v1 Pydantic schema validation |
| 1.2 — Safe cache | Pickle removed, JSON manifest pipeline |
| 1.3 — Squad/points metadata | `squad_size` authoritative, `model_count` per-model only |
| 1.4 — Canonical JSON artifacts | 15 sharded artifacts, canonical IDs, strict schemas, deterministic rebuild |
