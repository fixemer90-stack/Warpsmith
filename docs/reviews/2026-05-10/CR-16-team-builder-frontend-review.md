---
title: "CR-16 — Team Builder frontend review"
review_id: CR-16
status: request-changes
date: 2026-05-10
source: ../../requirements/code-review/cr-16-team-builder-frontend-review.md
tags: [code-review, frontend, team-builder, alpine]
---

# CR-16 — Team Builder frontend review

## Verdict

Request Changes.

Live Team Builder smoke checks passed for the current inline implementation: JS syntax is valid, the page loads without initial console errors, Warlord selection blocks save when two Character candidates are present, and the current PTS formula matches the backend formula for the checked Boyz scenario.

Blocking risk is in drift and false confidence: the shipped scope contains stale duplicate modal code that is not used by the live page, and the modal tests include placeholder `assert True` tests for the exact behavior this CR needs to protect.

## Severity counters

- Critical: 0
- Important: 2
- Suggestions: 2

## Scope inspected

- `web/templates/team_builder.html`
- `web/static/team_builder.js`
- `web/static/unit_modal.js`
- `web/templates/partials/unit_modal.html`
- `tests/test_team_builder.py`
- `tests/test_unit_modal.py`
- `tests/test_roster.py`
- `web/routes/api_rosters.py` roster payload contract

## Verification commands and probes

### JS syntax + focused tests

```bash
node -c web/static/team_builder.js && \
node -c web/static/unit_modal.js && \
uv run python -m pytest tests/test_team_builder.py tests/test_unit_modal.py tests/test_roster.py -q
```

Result: passed, `36 passed in 2.52s`.

### Template conflict / null-safety scan

```bash
python3 - <<'PY'
from pathlib import Path
for p in ['web/templates/team_builder.html','web/templates/partials/unit_modal.html','web/templates/partials/unit_card.html']:
    path=Path(p)
    if path.exists():
        text=path.read_text(encoding='utf-8')
        print(f'## {p}')
        print('raw_blocks', text.count('{% raw %}'), 'endraw', text.count('{% endraw %}'))
        for token in ['{{ unit.', '{{ entry.', '{{ total', '{{ current', '{{ unitDetail']:
            if token in text:
                print('POTENTIAL_CONFLICT', token)
        for needle in ['x-show="unitDetail.', 'x-show="currentWeapons', 'x-for="ability in unitDetail.abilities"', 'x-for="option in unitDetail.wargear_options"']:
            print(needle, needle in text)
PY
```

Observed:
- `web/templates/team_builder.html`: 2 raw blocks / 2 endraw blocks; dynamic Alpine stat snippets are protected.
- `web/templates/partials/unit_modal.html`: modal expressions exist, but the partial is not included by the live Team Builder page.
- `web/templates/partials/unit_card.html`: `{{ unit... }}` tokens are server-side Jinja partial usage, not the Team Builder Alpine list.

### Roster API contract probe

```bash
uv run python - <<'PY'
from fastapi.testclient import TestClient
from main import app
c=TestClient(app)
for url in ['/api/units?faction=orks','/api/units/Boyz/detail']:
    r=c.get(url)
    print(url, r.status_code)
    data=r.json()
    u=data['units'][0] if 'units' in data else data
    print({k:u.get(k) for k in ['name','category','icon','icon_tags','can_be_warlord','is_leader','squad_size','points']})
PY
```

Observed:
- Unit list endpoint includes `category`, `icon`, `can_be_warlord`, `is_leader`, `squad_size`, `points`.
- Unit detail endpoint includes `icon_tags`, `can_be_warlord`, `is_leader`, `squad_size`, `points`.
- This supports edit-mode metadata hydration in `team_builder.js`.

### Warlord and PTS JS probe

```bash
node - <<'NODE'
const fs=require('fs'), vm=require('vm');
const code=fs.readFileSync('web/static/team_builder.js','utf8');
const sandbox={window:{},document:{addEventListener(){},dispatchEvent(){}},CustomEvent:function(){},fetch(){},alert(){},console};
vm.createContext(sandbox); vm.runInContext(code,sandbox);
const tb=sandbox.teamBuilder();
function unit(name, pts, min, category='Character') { return {name, points:pts, squad_size:{min,max:min,step:1}, wargear_options:[], nob_options:[], weapons:[], category, icon_tags:['character'], can_be_warlord:true}; }
tb.unitDetail=unit('A',80,10); tb.squadSize=10; tb.addUnitToRoster();
console.log('one_candidate_valid', tb.warlordCandidates.length, tb.roster[0].is_warlord, tb.isValid);
tb.unitDetail=unit('B',90,5); tb.squadSize=5; tb.addUnitToRoster();
console.log('two_candidates_valid', tb.warlordCandidates.length, tb.roster.map(u=>u.is_warlord).join(','), tb.hasValidWarlordSelection, tb.validationErrors[0]?.code, tb.isValid);
tb.setWarlord(1); console.log('after_set', tb.roster.map(u=>u.is_warlord).join(','), tb.hasValidWarlordSelection, tb.validationErrors.length, tb.isValid);
tb.unitDetail={name:'Boyz', points:80, squad_size:{min:10,max:20,step:10}, wargear_options:[{name:'default',points:0,weapons:[]}], nob_options:[{name:'klaw',points:10,weapons:[]}], weapons:[], category:'Battleline', icon_tags:['infantry']}; tb.squadSize=20; tb.selectedLoadout='default'; tb.selectedNobOption='klaw'; console.log('pts_formula', tb.totalCost);
NODE
```

Observed:
- First Warlord candidate is auto-selected.
- Adding a second Warlord candidate clears implicit selection and sets `warlord_required`.
- `setWarlord()` restores valid selection.
- PTS formula probe returns `170`, matching `(80 / 10 + 0) * 20 + 10`.

### Browser smoke

Server restarted without reload:

```bash
kill -9 $(lsof -ti:8000)
uv run python3 -c "import uvicorn; uvicorn.run('main:app', host='127.0.0.1', port=8000, reload=False)"
curl http://127.0.0.1:8000/api/health
```

Health result: `{"status":"ok","version":"0.7.7"}`.

Browser checks:
- Navigated to `http://127.0.0.1:8000/team-builder`.
- Initial console: no messages and no JS errors before custom DevTools probes.
- Selected Orks; categories, detachments, and units populated.
- Opened Warboss modal; unit detail loaded with `can_be_warlord: true`.
- Added Warboss + Big Mek; UI showed `Multiple Characters detected`, crown button visible, `Set as Warlord` title present, and Save disabled until a Warlord is selected.

### Codex CLI attempt

The user invoked the Codex skill, so a Codex review was attempted:

```bash
codex exec "Review CR-16 Team Builder frontend scope ..."
```

Result: `codex: command not found`. Codex CLI is not installed in this environment, so the review continued with direct probes plus an independent reviewer subagent.

## Findings

### Important — CR16-01: Stale duplicate Unit Modal implementation can reintroduce invalid roster/Warlord behavior

Evidence:
- `web/templates/team_builder.html` contains the live inline modal implementation.
- `web/static/team_builder.js` contains the live modal methods and stores Warlord metadata: `tags`, `can_be_warlord`, `is_warlord`.
- `web/static/unit_modal.js` defines a separate `unitModalMixin`, but no code references `unitModalMixin`.
- `web/templates/partials/unit_modal.html` is not included by any live template.
- The stale mixin's `addUnitToRoster()` only stores `name`, `squad_size`, `pts`, `loadout`, `nob_option`, `weapons`, and `category`; it does not store `tags`, `can_be_warlord`, or `is_warlord`.
- The stale mixin initializes `squadSize: 5`, unlike the current `team_builder.js` default and detail-load logic.

Impact:
If a future refactor switches the page back to `unitModalMixin` or the partial, Team Builder can silently lose Warlord eligibility/selection metadata and diverge from the currently verified Warlord flow. This is exactly the kind of stale duplicate frontend code that makes CR-16 regressions likely.

Required change:
Consolidate to a single Unit Modal implementation. Either delete the unused static mixin and unused partial, or make Team Builder actually use a shared implementation that includes the current Warlord metadata, PTS formula, tag badges, and null-safety.

### Important — CR16-02: Unit modal tests are placeholders for the core behavior CR-16 needs to protect

Evidence:
- `tests/test_unit_modal.py::TestSquadSizeLogic::test_squad_size_validation_placeholder` only asserts `True`.
- `tests/test_unit_modal.py::TestLoadoutLogic::test_loadout_selection_placeholder` only asserts `True`.
- `tests/test_unit_modal.py::TestCostCalculation::test_cost_calculation_placeholder` only asserts `True`.
- Focused tests pass (`36 passed`), but they do not exercise actual Alpine cost calculation, Warlord UI state, save payload shape, or edit-mode hydration.

Impact:
CI can stay green while the Team Builder breaks the exact acceptance criteria in this artifact: PTS UI parity, Warlord UI, roster save/edit, and modal behavior.

Required change:
Replace placeholder tests with real smoke/contract tests. Minimum coverage:
- Team Builder HTML contains crown UI, `Set as Warlord`, and `Multiple Characters detected` text.
- Static JS contains the accepted PTS formula pattern (`points / minSquad`, sum stored `pts`).
- Save payload includes `is_warlord` and no duplicate keys.
- Edit-mode hydration recomputes `can_be_warlord` from `/api/units` metadata.
- Optional browser/Playwright-style probe for adding two Character units and confirming Save is disabled until one crown is selected.

### Suggestion — CR16-03: Duplicate `pts` key in `saveRoster()` payload is harmless today but should be removed

Evidence:
`web/static/team_builder.js` maps units with `pts: u.pts` twice in the same object literal.

Impact:
JavaScript keeps the later value, so current runtime behavior is likely unchanged. It is still noisy and can hide future divergence if one occurrence is edited and the other is not.

Suggested change:
Remove the duplicate `pts` entry from the save payload.

### Suggestion — CR16-04: `x-model` for squad size should use numeric coercion

Evidence:
The live inline Team Builder modal uses:

```html
<input type="number" x-model="squadSize" ...>
```

The unused partial uses `x-model.number="squadSize"`.

Impact:
Arithmetic currently works through JavaScript coercion, but strict comparisons for quick preset styling (`squadSize === size`) can fail after manual typing because `squadSize` becomes a string.

Suggested change:
Use `x-model.number="squadSize"` in the live inline modal as well.

## Positives

- Current `team_builder.js` PTS formula matches the accepted formula: `points / minSquad`, then `(ptsPerModel + loadoutPts) * squadSize + nobPts`.
- Current live Warlord flow behaves correctly in both JS and browser probes.
- Unit list/detail API includes enough metadata for edit-mode hydration.
- No initial `/team-builder` browser console errors were observed.
- Jinja2/Alpine conflict risk in the live Team Builder stat snippets is mitigated by raw/endraw blocks.

## Completion

Completed at: 2026-05-10
