---
title: "Task 1.3 — Compile squad/points metadata consistently"
parent: remediation-plan
status: pending
phase: "1 — Content compiler / schemas"
task_id: "1.3"
source: remediation-plan.md
---

# Task 1.3 — Compile squad/points metadata consistently

**Index:** [index.md](index.md)
**Source plan:** [remediation-plan.md](remediation-plan.md)
**Previous:** [1.2 — Replace unsafe/stale cache behavior](task-01-02-replace-unsafe-stale-cache-behavior.md)
**Next:** [1.4 — Emit canonical JSON artifacts](task-01-04-emit-canonical-json-artifacts.md)

## Phase context

**Phase:** 1 — Content compiler / schemas
**Purpose:** make wiki/frontmatter content compile into validated schemas before runtime use.
**Primary CRs:** CR-06, CR-11, CR-12, CR-21.
**Dependencies:** [1.2 — Replace unsafe/stale cache behavior](task-01-02-replace-unsafe-stale-cache-behavior.md)

## Objective

one canonical squad metadata shape feeds roster validation and UI.

## Acceptance criteria

- [ ] `unit.squad_size` from YAML/frontmatter is authoritative.
- [ ] `model_count` is not used as roster min/max replacement.
- [ ] Single-model vehicles and transport capacity cannot be misread as squad size.

## Files likely touched

- `backend/model/unit.py`
- `backend/loader/parser.py`
- `backend/loader/registry.py`
- new: `backend/loader/compiler.py`
- new: `backend/loader/schemas.py`
- `wiki/`
- target/generated: `data/generated/content/units/index.json`, `data/generated/content/units/<owning_or_source_faction_id>.json` definition shards, and `data/generated/content/faction_units/<faction_id>.json` availability shards
- `tests/test_parser.py`
- `tests/test_registry.py`
- new: `tests/test_content_contracts.py`

## Verification

- [ ] `uv run python -m pytest tests/test_parser.py tests/test_roster*.py -q`

## Completion requirements

- [ ] Implementation/change is complete for this task only; do not batch unrelated fixes.
- [ ] Regression evidence is recorded in the affected CR artifact(s).
- [ ] If this task completes a phase checkpoint, update `docs/reviews/2026-05-10/triage-summary.md`, affected `docs/requirements/code-review/cr-XX-*.md`, and `docs/requirements/code-review/code-review.md` with the phase completion artifact.
- [ ] `git diff --check` passes for touched files.
