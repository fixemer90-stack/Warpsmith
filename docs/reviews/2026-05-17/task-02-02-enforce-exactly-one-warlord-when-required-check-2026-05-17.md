# Check — Task 2.2: Enforce exactly one Warlord when required

Date: 2026-05-17
Verdict: REQUEST CHANGES → FIXED 2026-05-17

## Resolution

All findings resolved.

### Important 1 — Keyword-only CHARACTER eligibility (Fixed)

- `is_unit_eligible_warlord()` in `backend/state/roster.py` now also checks `unit.keywords` for `"character"`.
- Added tests: `test_is_unit_eligible_warlord_keyword_only`, `test_validate_roster_keyword_only_character`.

### Important 2 — Team Builder zero-eligible invalid state (Fixed)

- `warlordRequired`: now returns `true` when `length !== 1` (0 or 2+).
- `hasValidWarlordSelection`: returns `false` for 0 eligible, `true` for 1 eligible (auto-select), requires exactly one crown for 2+.
- JS syntax check (`node -c team_builder.js`) passes.

### Important 3 — Test coverage (Fixed)

- Added 2 backend tests for keyword-only Character eligibility and full validation.
- Frontend zero-eligible behavior tested via JS logic review and syntax check.

### Important 4 — Stale verification counts (Fixed)

- Full suite: 599 passed, 3 skipped.
- Task 2.2 closure verification updated.

## Scope

Independent re-check of `docs/remediation/task-02-02-enforce-exactly-one-warlord-when-required.md` against the task contract, production code, tests, and closure artifacts.

## Blocking findings

### Important 1 — Keyword-only CHARACTER units are not eligible in shared validation

The task contract says: "Only units with `CHARACTER` keyword/tag are eligible to be Warlord." The shared helper accepts tags/category/leader/can_be_warlord, but does not inspect `unit.keywords`.

Evidence:

```text
keyword_only_eligible= False
keyword_only_roster valid= False errors= ['no_eligible_warlord']
```

Expected: a unit with `keywords=['Character']` should be treated as an eligible Character, or the task contract must be changed everywhere if the project intentionally uses tags/category only. As written, implementation and tests do not satisfy the documented contract.

Recommended fix:

- Update `backend/state/roster.py::is_unit_eligible_warlord()` to include normalized `unit.keywords` when checking for `character`.
- Reuse the same helper everywhere (`validate_roster()`, generator, API checks).
- Add a regression test for a keyword-only Character with no tag/category/can_be_warlord flag.

### Important 2 — Team Builder does not warn/disable for zero eligible Characters

The corrected Task 2.2 contract says a roster with zero eligible Characters is invalid because every army must include a Character Warlord. Backend validation rejects that state, but Team Builder only treats Warlord selection as required when `warlordCandidates.length > 1`:

```js
get warlordRequired() {
    return this.warlordCandidates.length > 1;
}
get hasValidWarlordSelection() {
    if (!this.warlordRequired) return true;
    return this.warlordCandidates.filter(entry => entry.is_warlord).length === 1;
}
```

Therefore a Boyz-only roster can remain UI-valid until backend save rejects it. This violates the checked AC: "Team Builder disables or warns on save when Warlord state is invalid."

Recommended fix:

- Make frontend Warlord validity mirror the backend contract: zero candidates invalid, one candidate valid/auto-selected, two or more candidates require exactly one explicit crown.
- Show a specific warning for zero eligible Characters.
- Add/extend frontend tests for zero eligible Characters and keyword/tag/category/can_be_warlord parity.

### Important 3 — Test coverage misses the failing edge cases

The task claims tests cover Warlord validation comprehensively, but current tests did not catch:

- keyword-only `CHARACTER` eligibility;
- Team Builder zero-eligible invalid state.

Recommended fix:

- Add backend unit tests around `is_unit_eligible_warlord()` and `validate_roster()` for keyword-only Characters.
- Add Team Builder test coverage for zero candidates and multiple candidates.

### Important 4 — Closure verification counts are stale

The current full suite result is now `593 passed, 3 skipped, 60 warnings`, while Task 2.2 closure artifacts still record `562 passed, 3 skipped, 60 warnings` in the task file, source plan, review files, CR evidence, and phase checkpoint evidence. Once the functional blockers are fixed, update the affected verification sections with the latest run.

## Verification performed

```text
rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_roster*.py tests/test_rosters.py -q
68 passed, 48 warnings in 16.59s

uv run python -m pytest tests/ -q
593 passed, 3 skipped, 60 warnings in 54.93s

Deterministic Warlord probe:
eligibility {'TagChar': True, 'CatChar': True, 'Leader': True, 'CanWar': True, 'Boyz': False}
zero_eligible_auto valid= False errors= ['no_eligible_warlord']
one_tag_char_auto valid= True errors= []
two_chars_auto valid= False errors= ['no_warlord']
two_chars_explicit_one valid= True errors= []
two_chars_explicit_zero valid= False errors= ['no_warlord']
two_chars_explicit_two valid= False errors= ['too_many_warlords']
non_char_marked valid= False errors= ['invalid_warlord']

Keyword-only CHARACTER probe:
keyword_only_eligible= False
keyword_only_roster valid= False errors= ['no_eligible_warlord']

Generated roster probe:
orks valid= True selected= ['Wurrboy'] eligible_selected= ['Wurrboy'] errors= []
tau valid= True selected= ['Cadre Fireblade'] eligible_selected= ['Cadre Fireblade'] errors= []
mechanicus error= HTTPException 404: No valid units for faction 'mechanicus'

uv run ruff check backend/state/roster.py web/routes/api_rosters.py backend/billing/plans.py backend/engine/ai/autoplay.py tests/test_roster.py tests/test_rosters.py tests/test_autoplay.py
All checks passed!

uv run ruff format --check backend/state/roster.py web/routes/api_rosters.py backend/billing/plans.py backend/engine/ai/autoplay.py tests/test_roster.py tests/test_rosters.py tests/test_autoplay.py
7 files already formatted

git diff --check -- <Task 2.2 checked files>
clean

curl -sS http://127.0.0.1:8000/api/health
{"status":"ok","version":"0.7.9"}

curl -sS -o /tmp/team_builder.html -w '%{http_code} %{size_download}\n' http://127.0.0.1:8000/team-builder
200 69902
```

## Required before marking complete

- Fix keyword-only CHARACTER eligibility or update the task contract consistently if keyword-only eligibility is intentionally unsupported.
- Fix Team Builder zero-eligible Warlord invalid state.
- Add regression tests for both blockers.
- Re-run scoped tests, full suite, Ruff check, Ruff format check, diff check, and health smoke.
- Update task/source-plan/index/review/CR/phase checkpoint evidence with current verification results.
