---
title: "Task 9.1 — Run final CR-24 regression gate and reconcile review metadata"
parent: remediation-plan
status: pending
phase: "9 — Final CR-24 re-run"
task_id: "9.1"
source: remediation-plan.md
---

# Task 9.1 — Run final CR-24 regression gate and reconcile review metadata

**Index:** [index.md](index.md)
**Source plan:** [remediation-plan.md](remediation-plan.md)
**Previous:** [8.3 — Verify deployment objectives and faction styles](task-08-03-verify-deployment-objectives-and-faction-styles.md)
**Next:** none

## Phase context

**Phase:** 9 — Final CR-24 re-run
**Purpose:** final readiness gate after phases 0-8.
**Primary CRs:** CR-24.
**Dependencies:** [8.3 — Verify deployment objectives and faction styles](task-08-03-verify-deployment-objectives-and-faction-styles.md), Checkpoint 8

## Objective

re-run the final static/test/browser/smoke gates and make CR metadata counts match the executed evidence.

## Acceptance criteria

- [ ] Static gates, full tests, local health check, browser smoke, and final result consistency smoke are executed.
- [ ] triage-summary.md, code-review.md, and affected CR artifacts contain the final evidence and matching counts.
- [ ] Release readiness decision is explicit: pass, blocked, or accepted debt with guardrails.

## Files likely touched

- `docs/reviews/2026-05-10/triage-summary.md`
- `docs/requirements/code-review/code-review.md`
- affected docs/requirements/code-review/cr-XX-*.md artifacts

## Verification

- [ ] `uv run ruff check .`
- [ ] `uv run ruff format --check .`
- [ ] `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/ -q`
- [ ] `curl -i -sS http://127.0.0.1:8000/api/health`
- [ ] `uv run python scripts/smoke_final_gate.py`

## Execution steps from source plan

- 1. Reconcile CR report counts:
-   - Normalize CR frontmatter/counts or regenerate `code-review.md` from reports.
- 2. Run final static gates:
-   - `uv run ruff check .`
-   - `uv run ruff format --check .`
-   - `node -c web/static/team_builder.js`
-   - `node -c web/static/scenario_setup.js`
-   - `node -c web/static/battlefield_map.js`
- 3. Run full tests:
-   - `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/ -q`
- 4. Start server without reload:
-   - `uv run python3 -c "import uvicorn; uvicorn.run('main:app', host='127.0.0.1', port=8000, reload=False)"`
- 5. Check health:
-   - `curl -i -sS http://127.0.0.1:8000/api/health`
- 6. Browser smoke:
-   - `/`
-   - `/team-builder`
-   - `/scenario-setup`
-   - `/my-rosters`
-   - `/result/<generated_game_id>`
- 7. Run final result consistency smoke:
-   - `uv run python scripts/smoke_final_gate.py`
- 8. Update:
-   - `docs/reviews/2026-05-10/triage-summary.md`
-   - `docs/requirements/code-review/code-review.md`
-   - affected CR artifacts
-   - docs/indexes if feature/code docs changed.

## Completion requirements

- [ ] Implementation/change is complete for this task only; do not batch unrelated fixes.
- [ ] Regression evidence is recorded in the affected CR artifact(s).
- [ ] If this task completes a phase checkpoint, update `docs/reviews/2026-05-10/triage-summary.md`, affected `docs/requirements/code-review/cr-XX-*.md`, and `docs/requirements/code-review/code-review.md` with the phase completion artifact.
- [ ] `git diff --check` passes for touched files.
