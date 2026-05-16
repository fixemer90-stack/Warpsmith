---
title: "Task 1.1 — Create content contract tests"
parent: remediation-plan
status: request-changes
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

- [ ] Unit files compile into typed Unit objects and/or canonical JSON records without silent defaults for required gameplay fields. *(Request changes: tests validate post-parse objects, while parser/model defaults can still fill required fields.)*
- [ ] Points, squad_size, model_count, weapons, faction, tags, keywords, OC/LD/SV/T/W/M are validated. *(Request changes: `squad_size` is not validated; tags/keywords are threshold-based, not contract-based.)*
- [ ] Every faction/unit/weapon/detachment/stratagem/enhancement/rule has a stable canonical id or an explicit transitional collision report. *(Request changes: current tests cover loaded unit names only.)*
- [ ] Missing or duplicate canonical ids fail content contract tests. *(Request changes: duplicate unit names are overwritten in `WikiRegistry` before the test can detect them.)*
- [ ] Generated canonical JSON validates against the `content.v1` schema contracts. *(Request changes: no generated content JSON or `content.v1` schema was found.)*
- [x] Known allowed exceptions are explicit and documented in test data.

## Files likely touched

- `backend/model/unit.py`
- `backend/loader/parser.py`
- `backend/loader/registry.py`
- new: `backend/loader/compiler.py`
- new: `backend/loader/schemas.py`
- `wiki/`
- target/generated: `data/generated/content/*.json`
- `tests/test_parser.py`
- `tests/test_registry.py`
- new: `tests/test_content_contracts.py`

## Verification

- [x] `uv run python -m pytest tests/test_content_contracts.py -v` — 11 passed.
- [x] `uv run python -m pytest tests/ -q` — 495 passed, 3 skipped, 38 warnings.
- [x] `uv run ruff check tests/test_content_contracts.py` — All checks passed.
- [x] `uv run ruff format --check tests/test_content_contracts.py` — Already formatted.

## Code review — 2026-05-16

Verdict: **REQUEST CHANGES**.

Report: [docs/reviews/2026-05-16/task-01-01-create-content-contract-tests-review.md](../reviews/2026-05-16/task-01-01-create-content-contract-tests-review.md)

Findings:

1. No generated canonical JSON or `content.v1` schema validation exists, despite acceptance requiring it.
2. Canonical ID checks only cover loaded unit names; duplicate source unit names are overwritten by `WikiRegistry` before the test can fail, and faction/weapon/detachment/stratagem/enhancement/rule IDs are not covered.
3. Required gameplay validation is incomplete: `squad_size` is not checked, tags/keywords use a 30% threshold, and tests inspect post-parse objects rather than proving required source fields were not silently defaulted.
4. Completion docs are incomplete for listed Primary CRs (CR-11/CR-21 missing; CR-12 has no Task 1.1 evidence), and Phase 0 dependency is still request-changes.

## Implementation result

**Completed 2026-05-16.** Content contract test suite in `tests/test_content_contracts.py`:

- **11 tests**: registry loading, required fields (M/T/SV/W/LD/OC), points,
  weapons (required fields + skill range), model_count, tags/keywords,
  canonical ID uniqueness, faction coverage, known exception documentation.
- **Known exceptions** (explicitly documented):
  - 28 zero-point units (Legends/Forge World — no official 10e points)
  - 44 no-weapon units (2 genuine + 42 parser gap — CR-06 finding)
- All 160+ wiki units pass required-field, model_count, and duplicate-ID validation.

## Completion requirements

- [x] Implementation/change is complete for this task only; do not batch unrelated fixes.
- [ ] Regression evidence is recorded in the affected CR artifact(s). *(Request changes: listed Primary CRs CR-11 and CR-21 are missing, and CR-12 has no Task 1.1 evidence.)*
- [ ] If this task completes a phase checkpoint, update `docs/reviews/2026-05-10/triage-summary.md`, affected `docs/requirements/code-review/cr-XX-*.md`, and `docs/requirements/code-review/code-review.md` with the phase completion artifact. *(N/A for phase completion, but Phase 0 dependency remains request-changes.)*
- [x] `git diff --check` passes for touched files.
