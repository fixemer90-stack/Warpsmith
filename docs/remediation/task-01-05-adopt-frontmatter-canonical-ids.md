---
title: "Task 1.5 — Adopt frontmatter canonical IDs"
parent: remediation-plan
status: completed
phase: "1 — Content compiler / schemas"
task_id: "1.5"
source: task-01-04 review follow-up
---

# Task 1.5 — Adopt frontmatter canonical IDs

**Index:** [index.md](index.md)
**Source review:** [Task 1.4 / Phase 1 review](../reviews/2026-05-17/task-01-04-emit-canonical-json-artifacts-and-phase-1-review.md)
**Previous:** [1.4 — Emit canonical JSON artifacts](task-01-04-emit-canonical-json-artifacts.md)
**Next:** [2.1 — Lock the canonical PTS formula](task-02-01-lock-the-canonical-pts-formula.md)

## Phase context

**Phase:** 1 — Content compiler / schemas
**Primary CRs:** CR-06, CR-11, CR-12, CR-21.
**Dependencies:** [1.4 — Emit canonical JSON artifacts](task-01-04-emit-canonical-json-artifacts.md)
**Checkpoint policy:** follow-up hardening task. It must not be used as a retroactive blocker for Task 1.4 unless the source plan explicitly promotes frontmatter `canonical_id` to Task 1.4 acceptance criteria.

## Objective

Introduce optional authoritative `canonical_id` frontmatter support for canonical content records, starting with units, without breaking legacy wiki files that do not yet declare explicit ids.

The goal is to make canonical ids survive display-name and source-file renames while keeping the current deterministic generated-id fallback available during migration.

## Scope

In scope:

- Unit frontmatter `canonical_id` parsing.
- Unit compiler id selection and validation.
- Source path preservation in canonical unit records.
- Duplicate/invalid explicit-id reporting.
- Tests for explicit-id stability and fallback behavior.
- Migration/reporting support for files missing explicit ids.

Out of scope for this task:

- Mandatory `canonical_id` on every wiki file.
- Bulk migration of every existing wiki file unless needed for tests/fixtures.
- Frontmatter ids for detachments, stratagems, enhancements, factions, or rules. Those should be follow-up tasks after the unit path is proven.
- Changing runtime unit ids or roster instance ids.
- Changing display names, faction names, or source directory layout.

## Contract

- `canonical_id` is an optional wiki frontmatter field.
- If `canonical_id` is present, it is authoritative for the canonical unit record id.
- If `canonical_id` is absent, the compiler keeps the current deterministic fallback: `unit:<faction_slug>:<display_slug>`.
- Explicit ids must use the canonical id format: `unit:<scope>:<name>`.
- Explicit ids are stable identifiers, not display labels.
- Explicit ids must be unique across all compiled unit records.
- Generated fallback ids must remain deterministic for unchanged display name and faction slug.
- Runtime unit instance identity remains separate from canonical unit identity.

## Acceptance criteria

- [x] Unit parser/compiler reads optional `canonical_id` from wiki frontmatter.
- [x] Explicit `canonical_id` wins over generated fallback id when present.
- [x] Missing `canonical_id` keeps deterministic fallback behavior for legacy wiki files.
- [x] Duplicate explicit canonical ids fail compilation before artifacts are written.
- [x] Invalid explicit canonical id format fails compilation with an actionable error that includes the source path.
- [x] Canonical unit records include `source_path` pointing back to the wiki source file.
- [x] Display-name changes do not change unit id when explicit `canonical_id` remains unchanged.
- [x] Source-file path changes do not change unit id when explicit `canonical_id` remains unchanged.
- [x] Collision/migration report distinguishes explicit-id duplicates from duplicate display names and fallback-id collisions.
- [x] No runtime loader starts treating canonical ids as runtime instance ids.

## Suggested implementation steps

1. Extend parser/compiler data flow so each source unit carries source-path metadata and optional raw frontmatter `canonical_id` into canonical compilation.
2. Add a single helper for unit canonical id selection:
   - validate explicit id if present;
   - otherwise produce fallback id from faction/display name;
   - return enough metadata for collision reports.
3. Add duplicate-id detection before artifact writes.
4. Add invalid-id diagnostics with source path and field name.
5. Emit `source_path` in `UnitV1Strict` / canonical unit JSON.
6. Add focused temporary-fixture tests for explicit id, fallback id, rename stability, duplicates, invalid format, and source path.
7. Regenerate canonical artifacts only if checked-in generated content is expected to change for this repository state.
8. Update affected CR evidence and this task file after verification.

## Files likely touched

- `backend/loader/parser.py`
- `backend/loader/compiler.py`
- `backend/loader/schema.py`
- `tests/test_content_contracts.py`
- `data/generated/content/` if generated artifacts are checked in
- selected `wiki/units/**.md` fixtures only if explicit ids are added to real content
- affected CR artifacts under `docs/requirements/code-review/`

## Test requirements

Add or update tests that cover:

- explicit `canonical_id` overrides fallback id;
- missing `canonical_id` uses fallback id;
- invalid id format fails with source path;
- duplicate explicit id fails before write;
- duplicate display names remain a non-fatal collision report if ids differ;
- display-name rename preserves id when explicit id is unchanged;
- source-file rename preserves id when explicit id is unchanged;
- source path is present in emitted unit records;
- runtime ids remain distinct from canonical ids where relevant.

Prefer `tmp_path` wiki/output fixtures. Do not rely on mutable pre-existing `data/generated/content` for regression tests.

## Verification

Minimum commands before marking complete:

```bash
sed -i 's/\r$//' backend/loader/parser.py backend/loader/compiler.py backend/model/unit.py tests/test_content_contracts.py
uv run python -m pytest tests/test_content_contracts.py -q
# 36 passed in 11.82s
uv run ruff check backend/loader tests/test_content_contracts.py
# 3 pre-existing warnings (S112, SIM102, SIM105 — all in pre-existing code)
uv run ruff format --check backend/loader tests/test_content_contracts.py
# 7 files already formatted
git diff --check -- backend/model/unit.py backend/loader/parser.py backend/loader/compiler.py tests/test_content_contracts.py
# Clean (exit 0)
```

If backend loader behavior changes, also run a local app smoke:

```bash
uv run python3 -c "import uvicorn; uvicorn.run('main:app', host='127.0.0.1', port=8000, reload=False)"
curl -fsS http://127.0.0.1:8000/api/health
```

## Completion requirements

- [x] Implementation/change is complete for this task only; do not batch unrelated compiler/cache fixes.
- [x] All acceptance criteria are checked with evidence.
- [x] Regression evidence is recorded in affected CR artifacts.
- [x] Review findings, if any, are resolved in both this task file and the review file.
- [x] `git diff --check` passes for touched files.
- [x] Telegram notification is sent after completion/review fix.

## Code review

No review file attached for this task yet — standalone Task 1.5 execution.

## Review result

Implementation of Task 1.5 completed:

**Changes made:**
1. **backend/model/unit.py**: Added `source_path: str = ""` field to Unit dataclass to track source file path.
2. **backend/loader/parser.py**: Passes `source_path=str(filepath)` to Unit constructor during parsing.
3. **backend/loader/compiler.py**: 
   - Added `_validate_unit_canonical_id()` function: validates explicit canonical_id format (`unit:<scope>:<name>`) with actionable error including source path.
   - Updated `_collect_units()`: validates format before using explicit id, raises RuntimeError on invalid format; tracks source_path in unit records; improved collision reporting with `id_kind` and `sources` fields.
   - Added pre-write fatal collision check in `compile_content()`: fatal collisions (unit_id, faction_id, dangling_ref) are checked BEFORE any artifact JSON is written, so duplicate explicit IDs prevent artifact output entirely.
4. **tests/test_content_contracts.py**: 12 new tests covering all acceptance criteria:
   - Explicit canonical_id overrides fallback
   - Missing canonical_id uses fallback
   - Invalid format fails with source path
   - Invalid format error includes source file path
   - Duplicate explicit ID fails before write
   - Duplicate display names (different IDs) non-fatal collision
   - Source path in unit records
   - Display-name rename preserves id
   - Source-file rename preserves id
   - Fallback id determinism
   - Collision report distinguishes duplicate types
   - Runtime IDs distinct from canonical IDs

**Verification:** All 36 content contract tests pass (24 pre-existing + 12 new). Lint clean (3 pre-existing warnings). Format clean. Git diff-check clean.
