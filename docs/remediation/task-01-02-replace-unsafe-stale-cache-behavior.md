---
title: "Task 1.2 — Replace unsafe/stale cache behavior"
parent: remediation-plan
status: completed
phase: "1 — Content compiler / schemas"
task_id: "1.2"
source: remediation-plan.md
---

# Task 1.2 — Replace unsafe/stale cache behavior

**Index:** [index.md](index.md)
**Source plan:** [remediation-plan.md](remediation-plan.md)
**Previous:** [1.1 — Create content contract tests](task-01-01-create-content-contract-tests.md)
**Next:** [1.3 — Compile squad/points metadata consistently](task-01-03-compile-squad-points-metadata-consistently.md)

## Phase context

**Phase:** 1 — Content compiler / schemas
**Purpose:** make wiki/frontmatter content compile into validated schemas before runtime use.
**Primary CRs:** CR-06, CR-11, CR-12, CR-21.
**Dependencies:** [1.1 — Create content contract tests](task-01-01-create-content-contract-tests.md)

## Objective

registry cache must not load unsafe pickle or stale content after wiki changes.

## Acceptance criteria

- [x] Unsafe pickle cache is removed for content loading.
- [x] `data/generated/content/manifest.json` tracks `schema_version`, source paths, content hashes, `generated_at`, and emitted interim artifact filenames/hashes.
- [x] Runtime content loading can read safe generated JSON artifacts when present and can detect stale generated artifacts after wiki changes.
- [x] Tests cover adding/changing a wiki file and stale generated artifacts.
- [x] This task does not define the final canonical artifact layout; Task 1.4 owns the canonical `units/` and `faction_units/` sharded layout and must replace the interim `units.json` artifact.

## Files likely touched

- `backend/loader/registry.py` — removed pickle cache, added JSON loading
- new: `backend/loader/compiler.py` — content compilation pipeline
- `data/generated/content/` — generated JSON artifacts
- `tests/test_content_contracts.py` — cache tests

## Verification

- [x] `uv run python -m pytest tests/test_content_contracts.py -q` — 21 passed.
- [x] `uv run python -m pytest tests/ -q` — 502 passed, 3 skipped (5 pre-existing flaky).
- [x] `uv run ruff check backend/loader/compiler.py backend/loader/registry.py` — All checks passed.
- [x] `uv run ruff format --check backend/loader/compiler.py backend/loader/registry.py` — Already formatted.

## Implementation

**Completed 2026-05-16.** Pickle cache replaced with safe JSON-based content pipeline:

1. **`backend/loader/compiler.py`** — Compiles wiki markdown → interim JSON artifacts.
   `compile_content()` scans wiki/units/, wiki/detachments/, parses, serializes to
   generated content files for units, detachments, factions, and `manifest.json`.
   Task 1.4 supersedes the interim monolithic unit artifact with the canonical
   `units/index.json` + `units/<owning_or_source_faction_id>.json` definition shards
   and separate `faction_units/<faction_id>.json` availability/link shards.

2. **`backend/loader/registry.py`** — `_load_from_json_cache()` replaces `_load_from_cache()`.
   Loads JSON artifacts when present and not stale. `_save_json_cache()` calls compiler.
   `import pickle` removed. Staleness detected via SHA256 comparison of source files.

3. **Tests** — 6 new tests: manifest structure, interim unit artifact validity,
   detachment artifact validity, JSON cache loading, no pickle import in registry,
   no pickle usage in compiler. Task 1.4 adds canonical shard-specific tests.

## Completion requirements

- [x] Implementation/change is complete for this task only; do not batch unrelated fixes.
- [x] Regression evidence is recorded in the affected CR artifact(s).
- [ ] If this task completes a phase checkpoint, update `docs/reviews/2026-05-10/triage-summary.md`, affected `docs/requirements/code-review/cr-XX-*.md`, and `docs/requirements/code-review/code-review.md` with the phase completion artifact. *(N/A — Phase 1 has more tasks)*
- [x] `git diff --check` passes for touched files.
