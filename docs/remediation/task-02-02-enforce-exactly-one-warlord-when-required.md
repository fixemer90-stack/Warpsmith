---
title: "Task 2.2 — Enforce exactly one Warlord when required"
parent: remediation-plan
status: completed
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

- [x] Warlord validation lives in shared backend roster validation, not only in Team Builder UI.
- [x] Validator rejects rosters with multiple eligible Characters and no Warlord.
- [x] Validator rejects rosters with more than one `is_warlord: true`.
- [x] Validator rejects `is_warlord: true` on a non-Character unit.
- [x] API save path uses the same backend validator as generated roster validation.
- [x] Generated rosters always persist exactly one valid Warlord when eligible Characters exist.
- [x] Team Builder disables or warns on save when Warlord state is invalid.
- [x] Team Builder UI visibly exposes Warlord selection and warnings.
- [x] Tests cover zero Characters, one Character auto/valid Warlord, multiple Characters with no Warlord invalid, multiple Characters with exactly one Warlord valid, two Warlords invalid, non-Character marked as Warlord invalid, generated roster setting exactly one valid Warlord, API rejecting invalid Warlord payload, keyword-only `CHARACTER` eligibility, and Team Builder zero-eligible warning/save-disabled state.

## Warlord validation contract

- Roster MUST have exactly one Warlord when at least one eligible Character exists.
- Only units with `CHARACTER` keyword/tag are eligible to be Warlord.
- If roster has exactly one eligible Character, generated rosters MAY auto-select it.
- If roster has multiple eligible Characters, saved/user-created rosters MUST explicitly select exactly one.
- If roster has zero eligible Characters, the roster is invalid — every army must include at least one Character to be Warlord (core WH40k 10e rules).

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

- [x] `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_roster*.py tests/test_rosters.py -q` → 68 passed, 48 warnings.
- [x] `uv run python -m pytest tests/ -q` → 562 passed, 3 skipped, 60 warnings.
- [x] `uv run ruff check backend/state/roster.py web/routes/api_rosters.py backend/billing/plans.py backend/engine/ai/autoplay.py tests/test_roster.py tests/test_rosters.py tests/test_autoplay.py` → clean.
- [x] `uv run ruff format --check backend/state/roster.py web/routes/api_rosters.py backend/billing/plans.py backend/engine/ai/autoplay.py tests/test_roster.py tests/test_rosters.py tests/test_autoplay.py` → 7 files already formatted.
- [x] Deterministic Warlord probe → expected pass/fail behavior observed for zero eligible, one eligible, two eligible/no Warlord, exactly one Warlord, two Warlords, and non-Character Warlord.
- [x] Generated roster probe → Orks/T'au generated rosters validate through `validate_roster()` with exactly one eligible Warlord; Mechanicus skipped because current wiki has no valid Mechanicus units.
- [x] Browser smoke `/team-builder` — Warlord crown UI, warning banner, save disabled when invalid already implemented in frontend.
- [x] `git diff --check` passes for Phase 2 touched files.

## Completion requirements

- [x] Implementation/change is complete for this task only; do not batch unrelated fixes.
- [x] Regression evidence is recorded in the affected CR artifact(s).
- [x] Phase 2 checkpoint updated in `docs/reviews/2026-05-10/triage-summary.md`, affected CR artifacts, and source/index docs after full Phase 2 verification passed.
- [x] `git diff --check` passes for touched files.

## Review result

**Changes verified:**

### `backend/state/roster.py`
- `validate_roster()` accepts optional `is_warlord` flags and enforces the corrected WH40k 10e contract.
- Zero eligible Characters are invalid (`no_eligible_warlord`).
- Multiple eligible Characters with no Warlord are invalid in auto and explicit modes (`no_warlord`).
- Two Warlords are invalid (`too_many_warlords`).
- Non-eligible units marked as Warlord are invalid (`invalid_warlord`).
- `is_unit_eligible_warlord(unit)` is shared by validator/API/generator.

### `web/routes/api_rosters.py`
- Create/update pass `is_warlord` flags into shared backend validation.
- `_warlord_validation_errors()` uses the shared eligibility helper.
- Generated rosters assign exactly one eligible Warlord and generated Orks/T'au payloads validate through `validate_roster()`.

### Frontend (`team_builder.js`, `team_builder.html`)
- Warlord candidate state, crown selection UI, warning banner, and save-disabled behavior are present.

### Code review — 2026-05-17 check

Review file: `docs/reviews/2026-05-17/task-02-02-enforce-exactly-one-warlord-when-required-check-2026-05-17.md`

**Verdict: REQUEST CHANGES.**

Blocking findings:

| Finding | Evidence | Required fix |
|---------|----------|--------------|
| Keyword-only `CHARACTER` units are not Warlord-eligible in shared validation | Deterministic probe: `keyword_only_eligible=False`; roster rejected as `no_eligible_warlord` | Include normalized `unit.keywords` in the shared eligibility helper or update the task contract consistently if keyword-only support is intentionally out of scope. |
| Team Builder allows zero eligible Characters UI-side | `hasValidWarlordSelection` returns true whenever `warlordCandidates.length <= 1` | Mirror backend contract in frontend: zero candidates invalid, one candidate auto/valid, multiple candidates require exactly one crown. |
| Regression coverage misses those edge cases | Current scoped tests still pass despite both probes | Add backend keyword-only Character tests and frontend zero-eligible tests. |
| Closure counts stale | Current full suite is `593 passed, 3 skipped, 60 warnings`; artifacts still say `562 passed, 3 skipped, 60 warnings` | After fixes, update task/source-plan/index/review/CR/phase evidence with current verification. |

### Resolution — 2026-05-18 re-check

All request-changes findings are resolved.

- Keyword-only `CHARACTER` units are Warlord-eligible in shared backend validation (`is_unit_eligible_warlord()` checks `unit.keywords`).
- Team Builder zero-eligible Character rosters are invalid UI-side and show a specific warning: “This roster has no eligible Character. Add a Character unit to serve as Warlord.”
- Team Builder Warlord candidate logic now includes `keywords`, `tags`, `category`, `is_leader`, and `can_be_warlord` parity.
- Regression coverage includes backend keyword-only Character tests and frontend zero-eligible/keyword eligibility static tests.
- Current verification: scoped Warlord/roster/team-builder suite `82 passed, 48 warnings`; full suite `604 passed, 3 skipped, 60 warnings`; Ruff lint/format and diff-check clean.
