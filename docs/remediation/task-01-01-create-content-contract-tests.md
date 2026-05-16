---
title: "Task 1.1 — Create content contract tests"
parent: remediation-plan
status: pending
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

- [ ] Unit files compile into typed Unit objects and/or canonical JSON records without silent defaults for required gameplay fields.
- [ ] Points, squad_size, model_count, weapons, faction, tags, keywords, OC/LD/SV/T/W/M are validated.
- [ ] Every faction/unit/weapon/detachment/stratagem/enhancement/rule has a stable canonical id or an explicit transitional collision report.
- [ ] Missing or duplicate canonical ids fail content contract tests.
- [ ] Generated canonical JSON validates against the `content.v1` schema contracts.
- [ ] Known allowed exceptions are explicit and documented in test data.

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

- [ ] `uv run python -m pytest tests/test_content_contracts.py -q`

## Completion requirements

- [ ] Implementation/change is complete for this task only; do not batch unrelated fixes.
- [ ] Regression evidence is recorded in the affected CR artifact(s).
- [ ] If this task completes a phase checkpoint, update `docs/reviews/2026-05-10/triage-summary.md`, affected `docs/requirements/code-review/cr-XX-*.md`, and `docs/requirements/code-review/code-review.md` with the phase completion artifact.
- [ ] `git diff --check` passes for touched files.
