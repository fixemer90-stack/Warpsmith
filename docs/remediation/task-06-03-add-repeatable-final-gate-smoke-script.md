---
title: "Task 6.3 — Add repeatable final gate smoke script"
parent: remediation-plan
status: pending
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

- [ ] Script creates deterministic isolated replay/result smoke.
- [ ] Script asserts runtime VP, API VP, and result payload/page VP match.
- [ ] Script uses isolated DB or cleans up its data.

## Files likely touched

- `Create: `scripts/smoke_final_gate.py``
- `Test: `tests/test_final_gate_smoke.py` or direct script invocation documented in CR-24.`

## Verification

- [ ] `uv run python scripts/smoke_final_gate.py`

## Completion requirements

- [ ] Implementation/change is complete for this task only; do not batch unrelated fixes.
- [ ] Regression evidence is recorded in the affected CR artifact(s).
- [ ] If this task completes a phase checkpoint, update `docs/reviews/2026-05-10/triage-summary.md`, affected `docs/requirements/code-review/cr-XX-*.md`, and `docs/requirements/code-review/code-review.md` with the phase completion artifact.
- [ ] `git diff --check` passes for touched files.
