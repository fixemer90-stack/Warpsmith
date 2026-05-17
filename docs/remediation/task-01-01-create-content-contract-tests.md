---
title: "Task 1.1 — Create content contract tests"
parent: remediation-plan
status: completed
phase: "1 — Content compiler / schemas"
task_id: "1.1"
source: remediation-plan.md
---

# Task 1.1 — Create content contract tests

**Index:** [index.md](index.md)
**Source plan:** [remediation-plan.md](remediation-plan.md)
**Previous:** [0.3 — Stop destructive DB/replay behavior before further fixes](task-00-03-stop-destructive-db-replay-behavior-before-further-fixes.md)
**Next:** [1.2 — Replace unsafe/stale cache behavior](task-01-02-replace-unsafe-stale-cache-behavior.md)

## Phase context

**Phase:** 1 — Content compiler / schemas
**Purpose:** make wiki/frontmatter content compile into validated schemas before runtime use.
**Primary CRs:** CR-06, CR-11, CR-12, CR-21.
**Dependencies:** Phase 0 checkpoint

## Objective

fail fast on invalid wiki content that breaks runtime logic.

## Acceptance criteria

- [x] Unit files compile into typed Unit objects and/or canonical JSON records without silent defaults for required gameplay fields.
- [x] Points, squad_size, model_count, weapons, faction, tags, keywords, OC/LD/SV/T/W/M are validated.
- [x] Every faction/unit/weapon/detachment/stratagem/enhancement/rule has a stable canonical id or an explicit transitional collision report.
- [x] Missing or duplicate canonical ids fail content contract tests.
- [x] Generated canonical JSON validates against the `content.v1` schema contracts.
- [x] Known allowed exceptions are explicit and documented in test data.

## Files likely touched

- `backend/model/unit.py`
- `backend/loader/parser.py`
- `backend/loader/registry.py`
- new: `backend/loader/schema.py` (content.v1 Pydantic models)
- `wiki/`
- new: `tests/test_content_contracts.py`

## Verification

- [x] `uv run python -m pytest tests/test_content_contracts.py -v` — 15 passed.
- [x] `uv run python -m pytest tests/ -q` — 501 passed, 3 skipped, 38 warnings.
- [x] `uv run ruff check tests/test_content_contracts.py backend/loader/schema.py` — All checks passed.
- [x] `uv run ruff format --check tests/test_content_contracts.py backend/loader/schema.py` — Already formatted.

## Implementation

**Completed 2026-05-16.** Content contract test suite in `tests/test_content_contracts.py`:

- **15 tests**: registry loading, required fields (M/T/SV/W/LD/OC), points,
  weapons (required fields + skill range), model_count, tags/keywords (deterministic),
  canonical ID uniqueness, faction coverage, known exception documentation,
  content.v1 Pydantic schema validation, squad_size validation, source-level
  duplicate detection.
- **content.v1 schema**: `UnitV1` + `WeaponV1` Pydantic models in `backend/loader/schema.py`.
  `validate_unit_v1()` validates every wiki unit against the canonical schema.
- **Known exceptions** (explicitly documented):
  - 28 zero-point units (Legends/Forge World — no official 10e points)
  - 44 no-weapon units (2 genuine + 42 parser gap — CR-06 finding)
- All 160+ wiki units pass required-field, model_count, and duplicate-ID validation.

## Code review — 2026-05-16

**Verdict:** request changes → **FIXED 2026-05-16**.
**Report:** [../reviews/2026-05-16/task-01-01-create-content-contract-tests-review.md](../reviews/2026-05-16/task-01-01-create-content-contract-tests-review.md)

Findings — all resolved:
- ✅ Important 1: content.v1 Pydantic schema (UnitV1, WeaponV1) + `validate_unit_v1()`.
- ✅ Important 2: Source-level duplicate detection — scans frontmatter before dict insertion.
- ✅ Important 3: `squad_size` validated; `tags/keywords` deterministic (not threshold).
- ✅ Important 4: CR-11, CR-12, CR-21 updated with Task 1.1 regression evidence.

## Completion requirements

- [x] Implementation/change is complete for this task only; do not batch unrelated fixes.
- [x] Regression evidence is recorded in the affected CR artifact(s).
- [ ] If this task completes a phase checkpoint, update `docs/reviews/2026-05-10/triage-summary.md`, affected `docs/requirements/code-review/cr-XX-*.md`, and `docs/requirements/code-review/code-review.md` with the phase completion artifact. *(N/A — Phase 1 has 1 more task: 01-02)*
- [x] `git diff --check` passes for touched files.
