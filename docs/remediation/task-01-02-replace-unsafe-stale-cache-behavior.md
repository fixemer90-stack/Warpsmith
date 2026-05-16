---
title: "Task 1.2 — Replace unsafe/stale cache behavior"
parent: remediation-plan
status: pending
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

- [ ] Unsafe pickle cache is removed for content loading.
- [ ] `data/generated/content/manifest.json` tracks `schema_version`, source paths, content hashes, `generated_at`, and all emitted artifact filenames/hashes.
- [ ] Runtime content loading reads canonical JSON/registry, not raw wiki markdown.
- [ ] Tests cover adding/changing a wiki file and stale generated artifacts.

## Files likely touched

- `backend/model/unit.py`
- `backend/loader/parser.py`
- `backend/loader/registry.py`
- new: `backend/loader/compiler.py`
- new: `backend/loader/schemas.py`
- `wiki/`
- target/generated: `data/generated/content/manifest.json`
- target/generated: `data/generated/content/factions.json`
- target/generated: `data/generated/content/units.json`
- target/generated: `data/generated/content/weapons.json`
- target/generated: `data/generated/content/detachments.json`
- target/generated: `data/generated/content/stratagems.json`
- target/generated: `data/generated/content/enhancements.json`
- target/generated: `data/generated/content/rules.json`
- `tests/test_parser.py`
- `tests/test_registry.py`
- new: `tests/test_content_contracts.py`

## Verification

- [ ] `uv run python -m pytest tests/test_registry.py tests/test_content_contracts.py -q`

## Completion requirements

- [ ] Implementation/change is complete for this task only; do not batch unrelated fixes.
- [ ] Regression evidence is recorded in the affected CR artifact(s).
- [ ] If this task completes a phase checkpoint, update `docs/reviews/2026-05-10/triage-summary.md`, affected `docs/requirements/code-review/cr-XX-*.md`, and `docs/requirements/code-review/code-review.md` with the phase completion artifact.
- [ ] `git diff --check` passes for touched files.
