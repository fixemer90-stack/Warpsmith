---
title: "Task 6.3 — Add repeatable final gate smoke script"
parent: remediation-plan
status: completed
phase: "6 — Replay/result authoritative state"
task_id: "6.3"
source: remediation-plan.md
---

# Task 6.3 — Add repeatable final gate smoke script

**Index:** [index.md](index.md)
**Source plan:** [remediation-plan.md](remediation-plan.md)
**Previous:** [6.2 — Fix event parsing and summary attribution](task-06-02-fix-event-parsing-and-summary-attribution.md)
**Next:** [7.1 — Fail closed on secrets/JWT/webhook config](task-07-01-fail-closed-on-secrets-jwt-webhook-config.md)

## Phase context

**Phase:** 6 — Replay/result authoritative state
**Purpose:** make persisted replay and result pages derive from one authoritative final state.
**Primary CRs:** CR-14, CR-18, CR-24.
**Dependencies:** [6.2 — Fix event parsing and summary attribution](task-06-02-fix-event-parsing-and-summary-attribution.md)

## Objective

replace ad-hoc `/tmp` CR-24 replay probes with repo-owned smoke.

## Acceptance criteria

- [x] Script creates deterministic isolated replay/result smoke.
- [x] Script asserts runtime VP, API VP, and result payload/page VP match.
- [x] Script uses isolated DB or cleans up its data.

## Files likely touched

- `Create: `scripts/smoke_final_gate.py``
- `Test: `tests/test_final_gate_smoke.py` or direct script invocation documented in CR-24.`

## Verification

- [x] `rm -f *.db-shm *.db-wal && uv run python scripts/smoke_final_gate.py` → exit 0 (deterministic isolated smoke passed).
- [x] `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_final_gate_smoke.py tests/test_result_screen.py tests/test_replay.py -q` → 46 passed, 0 failed.
- [x] `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/ -q` → 633 passed, 3 skipped, 0 failed.
- [x] `uv run ruff check scripts/smoke_final_gate.py tests/test_final_gate_smoke.py` → All checks passed.
- [x] `uv run ruff format --check scripts/smoke_final_gate.py tests/test_final_gate_smoke.py` → 2 files already formatted.

## Code review

Review file: `docs/reviews/2026-05-19/task-06-03-add-repeatable-final-gate-smoke-script-check.md`

**Verdict: APPROVED 2026-05-19.**

Repo-owned smoke script now validates final VP authority parity through runtime/replay/result API and result-page VP wiring on an isolated DB.

## Completion requirements

- [x] Implementation/change is complete for this task only; do not batch unrelated fixes.
- [x] Regression evidence is recorded in the affected CR artifact(s).
- [x] If this task completes a phase checkpoint, update `docs/reviews/2026-05-10/triage-summary.md`, affected `docs/requirements/code-review/cr-XX-*.md`, and `docs/requirements/code-review/code-review.md` with the phase completion artifact. *(N/A: Task 6.3 is not the last task in Phase 6.)*
- [x] `git diff --check` passes for touched files.
