---
title: "Code Review — Task 1.1 create content contract tests"
date: 2026-05-16
reviewer: Hermes
verdict: request-changes
task: ../remediation/task-01-01-create-content-contract-tests.md
---

# Code Review — Task 1.1 create content contract tests

Verdict: **REQUEST CHANGES**

Scope reviewed:
- `tests/test_content_contracts.py`
- `backend/loader/parser.py`
- `backend/loader/schema.py`
- `backend/loader/registry.py`
- `backend/model/unit.py`
- `docs/remediation/task-01-01-create-content-contract-tests.md`
- touched CR/triage documentation

## Summary

The new test file is useful as a first wiki-unit smoke suite: it loads the registry, checks basic `Unit` fields, points, weapons, model count, weapon skill ranges, and documents known exceptions.

It does not yet satisfy the Task 1.1 acceptance contract. The task asks for schema-backed content contracts and canonical IDs across factions, units, weapons, detachments, stratagems, enhancements, and rules. The implementation currently validates only loaded unit objects and cannot detect several classes of content failure.

## Findings

### Important 1 — `content.v1` canonical JSON/schema contract is not implemented or tested

Acceptance requires:

> Generated canonical JSON validates against the `content.v1` schema contracts.

Repository search found no generated content JSON, no `content.v1` contract, and no schema validation path for this task:

```text
search *content* -> only task doc and tests/test_content_contracts.py
search content.v1|canonical_id|jsonschema|pydantic -> 0 matches
Path not found: /mnt/d/Python/Balthier/simulator/data
```

The only existing `backend/loader/schema.py` contains coercion helpers (`parse_optional_int`, `parse_model_count`, `ensure_list`) rather than a canonical `content.v1` schema. Therefore this acceptance criterion is unchecked and should not be marked complete.

Required fix: add explicit content schema contracts or mark the schema/generator portion as out of scope with a follow-up task. If accepting Task 1.1 as written, tests must validate generated canonical records against the declared `content.v1` schema.

### Important 2 — Canonical ID coverage is unit-only and misses duplicate source files

Acceptance requires stable canonical IDs for:

> Every faction/unit/weapon/detachment/stratagem/enhancement/rule

Current test `test_content_contract_no_duplicate_canonical_ids` iterates over `wiki.units.items()`. `WikiRegistry._scan_and_parse()` stores units in a dict keyed by `unit.name`:

```python
units[unit.name] = unit
```

This overwrites duplicate source files before the test sees them. Probe:

```text
files=2 loaded_units= 1 unit_names= ['Duplicate Unit']
```

So duplicate canonical unit IDs in source content are silently collapsed, not failed. The test also does not cover faction IDs, weapon IDs, detachment IDs, stratagem IDs, enhancement IDs, or rule IDs.

Required fix: validate canonical IDs at the source-file/canonical-record layer before insertion into dicts, and add coverage for all content types named by the acceptance criteria. If some types do not yet have canonical IDs, produce an explicit transitional collision/missing-ID report and assert it is intentional.

### Important 3 — Required gameplay fields are still allowed to come from silent parser/model defaults

Acceptance says unit files must compile without silent defaults for required gameplay fields, and points/squad_size/model_count/weapons/faction/tags/keywords/OC/LD/SV/T/W/M must be validated.

Current implementation still has silent defaults in the production parser/model path, for example:

```python
# backend/loader/parser.py
"category": str(metadata.get("category", "Infantry"))
kwargs["model_count"] = parse_model_count(metadata.get("model_count", (1, 1)))
kwargs["squad_size"] = metadata.get("squad_size", {"min": 1, "max": 1, "step": 1})

# backend/model/unit.py
points: int = 0
model_count: tuple[int, int] = (1, 1)
squad_size: dict[str, int] = field(default_factory=lambda: {"min": 1, "max": 1, "step": 1})
```

`tests/test_content_contracts.py` checks the post-parse object, not whether fields were present in source content or inferred by documented rules. It also does not validate `squad_size` at all, and `tags/keywords` only fail when more than 30% of units have neither.

Required fix: tests should distinguish explicit source values from parser defaults for required gameplay fields, validate `squad_size` shape/ranges, and make tag/keyword requirements deterministic or document exact allowed exceptions.

### Important 4 — Completion docs are incomplete for the listed Primary CRs and dependency is not accepted

Task 1.1 lists Primary CRs: CR-06, CR-11, CR-12, CR-21. The diff adds Task 1.1 regression evidence to CR-06 only. CR-12 only received Task 0.3 evidence, and CR-11/CR-21 were not updated.

Also, Task 1.1 depends on the Phase 0 checkpoint. Current reviewed state has Task 0.2 and Task 0.3 in `request-changes`, so the dependency is not accepted.

Required fix: update all affected CR artifacts or explicitly record why a listed Primary CR is not affected. Do not mark the Phase 1 task complete while its Phase 0 dependency remains request-changes.

## Positive checks

Confirmed:
- `tests/test_content_contracts.py` is present and collected.
- The registry load path uses `WikiRegistry().load(use_cache=False)`.
- Unit-level smoke checks cover required stat presence, positive points except documented exceptions, weapon presence except documented exceptions, model_count, weapon fields, and skill range.
- Known exception entries are asserted to still exist in the loaded registry.

## Verification run

Passed:

```text
uv run python -m pytest tests/test_content_contracts.py -v
11 passed

uv run python -m pytest tests/test_parser.py tests/test_unit.py tests/test_weapon.py tests/test_content_contracts.py -q
25 passed, 1 skipped

uv run python -m pytest tests/ -q
495 passed, 3 skipped, 38 warnings

uv run ruff check tests/test_content_contracts.py
All checks passed!

uv run ruff format --check tests/test_content_contracts.py
1 file already formatted

git diff --check -- tests/test_content_contracts.py docs/remediation/task-01-01-create-content-contract-tests.md docs/requirements/code-review/cr-06-wiki-loader-and-parser-review.md docs/requirements/code-review/cr-12-roster-validation-and-points-review.md docs/reviews/2026-05-10/triage-summary.md
# empty output, exit 0
```

Stale command corrected:

```text
uv run python -m pytest tests/test_loader.py tests/test_registry.py tests/test_content_contracts.py -q
ERROR: file or directory not found: tests/test_loader.py
```

The repository has `tests/test_parser.py`, `tests/test_unit.py`, and `tests/test_weapon.py`, so the corrected focused command above was used.

Probe:

```text
Duplicate source-file probe: files=2 loaded_units= 1 unit_names= ['Duplicate Unit']
```

This confirms duplicate unit names are overwritten before the current duplicate-ID test can see them.

## Verdict

Request changes. Keep the useful unit smoke tests, but do not accept Task 1.1 until schema validation, source-level canonical ID/collision checks, complete required-field validation, CR evidence, and Phase 0 dependency status match the task contract.
