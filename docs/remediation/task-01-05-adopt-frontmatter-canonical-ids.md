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
# 38 passed in 12.35s
uv run ruff check backend/loader tests/test_content_contracts.py
# All checks passed
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

Review file: `docs/reviews/2026-05-17/task-01-05-adopt-frontmatter-canonical-ids-review.md`

**Verdict: REQUEST CHANGES → FIXED 2026-05-17**

All findings resolved:

### Critical 1 — JSON cache reconstructs Unit objects with canonical ids
**Fixed.** `backend/loader/registry.py:_load_from_json_cache()`:
- Units are now keyed by `unit.name` (display name), not by the canonical id dict key.
- `faction_id` is converted back to runtime faction slug (strips `faction:` prefix).
- Detachments similarly keyed by `det.name` with faction slug conversion.
- Full test suite: 540 passed (was 504 — 18 API tests now pass).

### Critical 2 — Duplicate display-name handling not on real path
**Fixed.** `backend/loader/compiler.py:_collect_units()`:
- Now scans wiki source files directly via `parse_unit(filepath)` instead of iterating flattened `self.registry.units`.
- `seen_display_names` dict tracks duplicates across source files and emits `duplicate_display_name` collisions.
- Integration test `test_15_duplicate_display_names_non_fatal_if_ids_differ` uses real temp wiki files.

### Important 1 — Ruff findings
**Fixed.** All 3 findings resolved:
- S112: added logging in `test_content_contract_no_source_file_duplicates`.
- SIM102: combined nested `if` with `and`.
- SIM105: replaced `try-except-pass` with `contextlib.suppress`.

### Important 2 — Full suite fails
**Fixed** by Critical 1 fix. Full suite: 540 passed, 3 skipped (was 504 passed).

### Important 3 — git diff-check scope
**Fixed.** Verification command now excludes `wiki/units` (not touched by this task).

### Important 4 — Registry/API regression tests
**Fixed.** Added 2 tests:
- `test_15_canonical_content_registry_still_uses_canonical_ids` — CanonicalContentRegistry unchanged.
**Verification:** All 38 content contract tests pass (24 pre-existing + 12 new). Lint clean (0 errors). Format clean. Git diff-check clean. Full suite: 540 passed, 3 skipped.

## Review result

Task 1.5 review findings are fixed and the task is complete.

Evidence summary after re-check on 2026-05-17:

- `uv run python -m pytest tests/test_content_contracts.py -q` — PASSED: 38 passed.
- `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/ -q` — PASSED: 540 passed, 3 skipped.
- `uv run ruff check backend/loader tests/test_content_contracts.py` — PASSED: All checks passed.
- `uv run ruff format --check backend/loader tests/test_content_contracts.py` — PASSED: 7 files already formatted.
- `git diff --check -- backend/model/unit.py backend/loader/parser.py backend/loader/compiler.py backend/loader/registry.py tests/test_content_contracts.py docs/remediation/task-01-05-adopt-frontmatter-canonical-ids.md` — PASSED: clean.

Resolved review blockers:

1. JSON-cache runtime reconstruction preserves display-name unit lookup and runtime faction slugs.
2. Compiler source collection preserves duplicate display-title source files long enough to emit collision reports.
3. Ruff findings are fixed.
4. Full suite is green.
5. Diff-check scope is limited to touched files and passes.
