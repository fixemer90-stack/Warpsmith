---
title: "CR-12 — Roster validation and points review"
status: request-changes
reviewed_at: 2026-05-09T22:45:59+03:00
reviewer: Hermes Agent
scope: roster-validation-points
source_task: ../../requirements/code-review/cr-12-roster-validation-and-points-review.md
verdict: request-changes
critical_findings: 3
important_findings: 4
suggestions: 0
---

# CR-12 — Roster validation and points review

## Verdict

REQUEST CHANGES.

The focused roster tests pass, but direct review and deterministic probes found that saved API rosters can diverge from validated points, generated rosters can return an invalid empty/no-Warlord army, and the core validator still cannot represent explicit Warlord selection. These block the acceptance criterion that saved and generated rosters are valid and do not diverge between UI and backend.

## Scope reviewed

Task file:

- `docs/requirements/code-review/cr-12-roster-validation-and-points-review.md`

Production code:

- `backend/state/roster.py`
- `web/routes/api_rosters.py`
- `web/static/team_builder.js`
- `web/static/unit_modal.js`
- `web/routes/api.py` for unit-detail fields used by Team Builder
- `backend/loader/parser.py` for squad-size and wargear source fields

Tests:

- `tests/test_roster.py`
- `tests/test_rosters.py`
- `tests/test_generate_roster.py`

Relevant project rules and expectations:

- PTS formula from project memory and skill reference:
  - `totalCost = (points / minSquad + loadoutPts) * squadSize + nobPts`
  - `totalPts = sum(pts)` where roster `pts` is already the final unit cost.
- Squad-size validation must use `unit.squad_size` from YAML frontmatter, not `model_count` fallback.
- Generated rosters must be directly saveable and runnable.

## Verification commands

### Focused roster suite

Command:

```bash
rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_roster.py tests/test_rosters.py tests/test_generate_roster.py -q
```

Result:

```text
45 passed, 26 warnings in 8.78s
```

### API save probe for frontend/backend points divergence

Command summary:

- Registered a test user with `TestClient`.
- Posted `/api/rosters` with `pts_limit=200`.
- Payload contained `Warboss` and `Boyz`, each with client-provided `pts=1500`.
- Backend validator recalculated only base wiki points and accepted the roster.

Observed result:

```text
register 302 create 200
{"id":486,"name":"Invalid expensive payload","faction":"orks","pts_limit":200,...
 "units":[{"unit_name":"Warboss","squad_size":1,"pts":1500,...},
          {"unit_name":"Boyz","squad_size":10,"pts":1500,...}]}
```

### Generate-roster validity probe

Command summary:

- Called `/api/rosters/generate` for Orks with very small `pts_limit` values.

Observed result:

```text
limit 1 status 200 units 0 warlords 0 total 0 first []
limit 40 status 200 units 1 warlords 1 total 30 first [{'unit_name': 'Mek', 'squad_size': 1, 'is_warlord': True}]
```

### Core Warlord validation probe

Command summary:

- Loaded wiki registry.
- Called `validate_roster([('Warboss', 1), ('Big Mek', 1)], registry.units, pts_limit=2000)`.

Observed result:

```text
core_valid True errors [] total 115
```

### Squad-size and total-model probes

Observed result for a unit with `model_count=(1,20)` but `squad_size={'min':10,'max':20,'step':10}`:

```text
validate_squad_size 5: None
validate_roster errors: [('squad_too_small', 'YAMLSizeUnit: min 10 models, got 5')] total_pts 50 models 100
```

Observed result for a 5-model unit with `model_count=(5,10)` and selected `squad_size=5`:

```text
total_models expected 5 actual 50 errors []
```

## Findings

### Critical 1 — API save/update validates one points model but stores a different client-provided points model

Evidence:

- `web/routes/api_rosters.py` builds `units_list = [(u.unit_name, u.squad_size) for u in data.units]`.
- It calls `validate_roster(units_list, wiki.units, pts_limit=data.pts_limit)`.
- It then stores `json.dumps([u.model_dump() for u in data.units])`, including client-provided `pts`, `loadout`, `nob_option`, and `weapons`.
- `validate_roster()` recalculates only base wiki points from `unit.points / minSquad * squad_size`.
- It does not validate that `sum(data.units[*].pts)` is within `pts_limit`.
- It does not validate that client-provided `pts` equals the canonical backend calculation.

Probe result:

- A roster with `pts_limit=200` and stored unit `pts` totaling `3000` was accepted with HTTP 200.

Impact:

- Saved rosters can exceed their declared limit while passing backend validation.
- Team Builder and backend can disagree about legality.
- Replay/scenario consumers that trust stored roster `pts` or UI metadata can operate on an invalid army.
- A direct API caller can bypass the UI points gate.

Expected:

- Backend should be authoritative for final unit cost.
- Either recompute and overwrite stored `pts`, or reject if submitted `pts` does not match backend canonical calculation.
- Validation should use the same formula as UI, including selected loadout and Nob option when those options carry points.

### Critical 2 — Generated roster endpoint can return HTTP 200 with an empty/no-Warlord roster

Evidence:

- `generate_roster()` returns a successful response for every selected list, even if it is empty.
- If the points limit is below the cheapest legal Warlord, the force-add path cannot add a Warlord.
- There is no final `validate_roster()` or exactly-one-Warlord check before returning.

Probe result:

```text
limit 1 status 200 units 0 warlords 0 total 0 first []
```

Impact:

- Generated opponent can be invalid and not directly saveable/runnable.
- This violates CR-12 step 5: generated roster exactly-one-Warlord.
- It violates the task acceptance that save/play rosters are valid.

Expected:

- If no legal roster can fit within `pts_limit`, return a 4xx validation error instead of a success body.
- Before returning, run the same final validation path used by save/update plus an exactly-one explicit Warlord assertion.

### Critical 3 — Core roster validator cannot validate explicit Warlord selection or exactly-one Warlord

Evidence:

- `validate_roster()` accepts only `list[tuple[str, int]]`.
- It has no input field for `is_warlord`.
- It only tracks whether any unit has `unit.can_be_warlord`.
- The API adds `_warlord_validation_errors()` separately for multiple Character choices, but the core validator itself still approves ambiguous multi-character rosters.

Probe result:

```text
core_valid True errors [] total 115
```

for a roster containing `Warboss` and `Big Mek` with no explicit Warlord information.

Impact:

- Callers that rely on `validate_roster()` directly cannot enforce explicit Warlord rules.
- The generator currently returns explicit `is_warlord` metadata but does not feed it into the core validator.
- Validation logic is split between backend state and API route code, which makes future callers easy to get wrong.

Expected:

- Use a validation input object that includes at least `unit_name`, `squad_size`, `is_warlord`, `loadout`, `nob_option`, and final/canonical points inputs.
- Put exactly-one explicit Warlord validation in `backend/state/roster.py`, not only in route helpers.
- API route helpers can translate request models into that canonical validator input, but should not be the only place where Warlord correctness exists.

### Important 1 — `validate_squad_size()` still uses `model_count`, not YAML `squad_size`

Evidence:

- `validate_roster()` uses `unit.squad_size`, which matches the project rule.
- `validate_squad_size()` still reads `min_size, max_size = unit.model_count`.

Probe result:

```text
validate_squad_size 5: None
validate_roster errors: [('squad_too_small', 'YAMLSizeUnit: min 10 models, got 5')]
```

Impact:

- The helper can approve squad sizes that the real validator rejects.
- Any future UI/API call that uses `validate_squad_size()` will regress the already-fixed `squad_size` source rule.

Expected:

- Update `validate_squad_size()` to use `unit.squad_size` and honor `min`, `max`, and `step`.
- Add a regression test where `model_count` and `squad_size` intentionally differ.

### Important 2 — `total_models` is calculated as `squad_size * unit.model_count[1]`

Evidence:

- `validate_roster()` increments `total_models += squad_size * unit.model_count[1]`.
- In this codebase, `squad_size` is already the selected number of models.

Probe result:

```text
total_models expected 5 actual 50 errors []
```

for a unit selected at `squad_size=5` with `model_count=(5,10)`.

Impact:

- Roster metadata exaggerates model count for multi-model units.
- Any future model-count caps, transport checks, or analytics built on `total_models` will be wrong.

Expected:

- Increment `total_models += squad_size` unless a future model explicitly distinguishes `number_of_squads` from `models_per_squad`.

### Important 3 — Generator copy-cap logic does not match validator Battleline policy and is not actually exercising duplicate copies

Evidence:

- `validate_roster()` allows 6 copies for Battleline and 3 copies for non-Battleline.
- `generate_roster()` has a comment `# Respect 3x cap` and checks `if counts.get(name, 0) >= 3` for every unit.
- The candidates list contains each unit name only once, so the count cap is mostly dead code in the current implementation.

Impact:

- Generator policy is not aligned with validator policy.
- If the generator later starts allowing duplicate units, Battleline units will be incorrectly capped at 3 unless this logic is fixed.
- Current tests only assert generated total points and one Warlord, not copy-cap policy.

Expected:

- Share a helper for max copies by unit tags/keywords/category.
- If generated rosters should use duplicates, generate and test Battleline up to 6 and non-Battleline up to 3.
- If generated rosters should not use duplicates, remove dead `counts` logic and document that decision.

### Important 4 — Focused tests pass but do not assert the integration failures

Evidence:

- `tests/test_roster.py` validates base `validate_roster()` behavior, but not selected `is_warlord`, final stored `pts`, loadout/Nob points, or differing `model_count` vs `squad_size` in `validate_squad_size()`.
- `tests/test_rosters.py` checks multiple-character Warlord selection for create, but not API points spoofing/mismatch.
- `tests/test_generate_roster.py` checks exactly-one generated Warlord for a normal 500-point Ork roster, but not low-limit or final validation rejection.

Impact:

- The existing suite gives a false sense of safety for CR-12 acceptance.
- All 45 focused tests pass while direct probes reproduce invalid behavior.

Expected regression tests:

- API rejects a roster when submitted `pts` total exceeds `pts_limit`, even if base wiki points fit.
- API recomputes or rejects mismatched final unit points.
- Generator returns 4xx when no legal Warlord roster can fit.
- Core validator rejects multiple Warlord candidates without exactly one `is_warlord=True` once canonical input supports it.
- `validate_squad_size()` uses YAML `squad_size`, including step.
- `total_models` equals selected model count.

## Positive notes

- `validate_roster()` already uses YAML `unit.squad_size` for its main min/max points calculation.
- `web/static/team_builder.js` uses the expected UI-side formula shape for current modal cost:
  - `points / minSquad`
  - plus loadout points per model
  - plus Nob option points once per unit
- Create/update route paths both call validation before writing.
- Battleline detection in `validate_roster()` checks both tags and keywords.

## Recommendation

Fix in this order:

1. Introduce a canonical `RosterUnitSelection` input model in `backend/state/roster.py` that includes selected Warlord, squad size, loadout/Nob option, and submitted/canonical points fields.
2. Move explicit Warlord validation into the canonical validator.
3. Make API create/update use canonical backend point calculation and reject or overwrite mismatched submitted `pts`.
4. Make generator call canonical validation before returning; return 4xx if no legal roster can be generated for the requested limit/faction.
5. Update `validate_squad_size()` and `total_models` calculation.
6. Add the regression tests listed above.

## Final status

- Verdict: `request-changes`
- Critical findings: 3
- Important findings: 4
- Suggestions: 0
- Production code changed: no
