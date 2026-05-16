---
title: "Task 2.2 — Enforce exactly one Warlord when required"
parent: remediation-plan
status: pending
phase: "2 — Roster validator"
task_id: "2.2"
source: remediation-plan.md
---

# Task 2.2 — Enforce exactly one Warlord when required

**Index:** [index.md](index.md)
**Source plan:** [remediation-plan.md](remediation-plan.md)
**Previous:** [2.1 — Lock the canonical PTS formula](task-02-01-lock-the-canonical-pts-formula.md)
**Next:** [2.3 — Enforce plan/feature gates consistently](task-02-03-enforce-plan-feature-gates-consistently.md)

## Phase context

**Phase:** 2 — Roster validator
**Purpose:** make roster validation authoritative and shared across API, generated rosters, saved rosters, and UI expectations.
**Primary CRs:** CR-12, CR-16, CR-17, CR-19.
**Dependencies:** [2.1 — Lock the canonical PTS formula](task-02-01-lock-the-canonical-pts-formula.md)

## Objective

saved and generated rosters have valid Warlord semantics.

## Acceptance criteria

- [ ] Warlord validation lives in shared backend roster validation, not only in Team Builder UI.
- [ ] Validator rejects rosters with multiple eligible Characters and no Warlord.
- [ ] Validator rejects rosters with more than one `is_warlord: true`.
- [ ] Validator rejects `is_warlord: true` on a non-Character unit.
- [ ] API save path uses the same backend validator as generated roster validation.
- [ ] Generated rosters always persist exactly one valid Warlord when eligible Characters exist.
- [ ] Team Builder disables or warns on save when Warlord state is invalid.
- [ ] Team Builder UI visibly exposes Warlord selection and warnings.
- [ ] Tests cover zero Characters, one Character auto/valid Warlord, multiple Characters with no Warlord invalid, multiple Characters with exactly one Warlord valid, two Warlords invalid, non-Character marked as Warlord invalid, generated roster setting exactly one valid Warlord, and API rejecting invalid Warlord payload.

## Warlord validation contract

- Roster MUST have exactly one Warlord when at least one eligible Character exists.
- Only units with `CHARACTER` keyword/tag are eligible to be Warlord.
- If roster has exactly one eligible Character, generated rosters MAY auto-select it.
- If roster has multiple eligible Characters, saved/user-created rosters MUST explicitly select exactly one.
- If roster has zero eligible Characters, Warlord requirement is not enforced unless faction/rules data explicitly requires otherwise.

## Non-goals

- Full detachment/faction-specific Warlord trait logic is not in scope.
- Enhancement legality is not in scope.
- Commander/Leader attachment rules are not in scope.

## Files likely touched

- `backend/state/roster.py`
- `web/routes/api_rosters.py`
- `web/static/team_builder.js`
- `web/templates/team_builder.html`
- `tests/test_roster*.py`
- `tests/test_api_rosters.py`

## Verification

- [ ] `uv run python -m pytest tests/test_roster*.py tests/test_api_rosters.py -q`
- [ ] Browser smoke `/team-builder` for crown/warning/save-disabled state.

## Completion requirements

- [ ] Implementation/change is complete for this task only; do not batch unrelated fixes.
- [ ] Regression evidence is recorded in the affected CR artifact(s).
- [ ] If this task completes a phase checkpoint, update `docs/reviews/2026-05-10/triage-summary.md`, affected `docs/requirements/code-review/cr-XX-*.md`, and `docs/requirements/code-review/code-review.md` with the phase completion artifact.
- [ ] `git diff --check` passes for touched files.
