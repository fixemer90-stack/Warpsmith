---
title: "CR-13 — API route surface review"
status: request-changes
reviewed_at: 2026-05-09T22:58:10+03:00
reviewer: Hermes Agent
scope: api-route-surface
source_task: ../../requirements/code-review/cr-13-api-route-surface-review.md
verdict: request-changes
critical_findings: 3
important_findings: 5
suggestions: 0
---

# CR-13 — API route surface review

## Verdict

REQUEST CHANGES.

The route surface is not yet safe or consistent enough to approve. The app has working happy-path API coverage, but route ownership, frontend/API alignment, auth boundaries, and error response contracts have blocking gaps.

No production code was changed during this review.

## Scope reviewed

Task file:

- `docs/requirements/code-review/cr-13-api-route-surface-review.md`

Primary route files:

- `web/routes/api.py`
- `web/routes/api_detachments.py`
- `web/routes/api_rosters.py`
- `web/routes/api_replays.py`
- `web/routes/pages.py`
- `main.py`

Additional route module discovered from live app inventory:

- `backend/billing/webhooks.py`

Frontend/API callers sampled:

- `web/static/detachment_picker.js`
- `web/static/faction_browser.js`
- `web/static/my_rosters.js`
- `web/static/replay_viewer.js`
- `web/static/result_chart.js`
- `web/static/scenario_setup.js`
- `web/static/synergy_hints.js`
- `web/static/team_builder.js`
- `web/static/unit_modal.js`
- `web/templates/pmf_chart.html`
- `web/templates/replays.html`
- `web/templates/pricing.html`
- `web/templates/base.html`

## Verification executed

### Focused API/page tests

Command:

```bash
rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_rosters.py tests/test_generate_roster.py tests/test_canvas_map.py tests/test_round_viewer.py tests/test_result_screen.py tests/test_faction_browser.py tests/test_detachment_picker.py tests/test_unit_modal.py tests/test_pmf_chart.py -q
```

Result:

```text
91 passed, 26 warnings in 11.97s
```

Warnings were auth-token datetime deprecation warnings from `backend/auth/__init__.py`.

### Route inventory

Command:

```bash
python3 - <<'PY'
from collections import defaultdict
from main import app
routes=[]
for r in app.routes:
    methods=','.join(sorted(getattr(r,'methods',[]) or []))
    path=getattr(r,'path','')
    name=getattr(r,'name','')
    endpoint=getattr(r,'endpoint',None)
    mod=getattr(endpoint,'__module__','') if endpoint else ''
    if path.startswith('/api') or mod.startswith('web.routes'):
        routes.append((path,methods,name,mod))
for row in sorted(routes):
    print('|'.join(row))
print('--- duplicates ---')
b=defaultdict(list)
for path,methods,name,mod in routes:
    b[(path,methods)].append((name,mod))
for k,v in sorted(b.items()):
    if len(v)>1:
        print(k,v)
PY
```

Key output:

```text
/api/detachments|GET|list_detachments|web.routes.api
/api/detachments|GET|list_detachments|web.routes.api_detachments
/api/detachments/{detachment_name}|GET|detachment_detail|web.routes.api
/api/detachments/{detachment_name}|GET|detachment_detail|web.routes.api_detachments
--- duplicates ---
('/api/detachments', 'GET') [('list_detachments', 'web.routes.api'), ('list_detachments', 'web.routes.api_detachments')]
('/api/detachments/{detachment_name}', 'GET') [('detachment_detail', 'web.routes.api'), ('detachment_detail', 'web.routes.api_detachments')]
```

### Auth dependency inventory

Command:

```bash
python3 - <<'PY'
from main import app
for r in app.routes:
    path=getattr(r,'path','')
    if path.startswith('/api'):
        methods=','.join(sorted(getattr(r,'methods',[]) or []))
        endpoint=getattr(r,'endpoint',None)
        mod=getattr(endpoint,'__module__','') if endpoint else ''
        deps=[]
        dependant=getattr(r,'dependant',None)
        if dependant:
            deps=[getattr(d.call,'__name__',str(d.call)) for d in dependant.dependencies]
        print(f'{methods:15} {path:35} {mod} deps={deps}')
PY
```

Key output:

```text
POST            /api/auto-play                      web.routes.api_replays deps=[]
GET             /api/replays/{game_id}              web.routes.api_replays deps=[]
GET             /api/replays                        web.routes.api_replays deps=[]
GET             /api/results/{game_id}              web.routes.api_replays deps=[]
POST            /api/rosters                        web.routes.api_rosters deps=['get_current_user']
GET             /api/rosters                        web.routes.api_rosters deps=['get_current_user']
POST            /api/rosters/generate               web.routes.api_rosters deps=[]
POST            /api/rosters/synergies              web.routes.api_rosters deps=[]
GET             /api/billing/portal                 backend.billing.webhooks deps=[]
```

### Endpoint smoke probes

Command:

```bash
python3 - <<'PY'
from fastapi.testclient import TestClient
from main import app
c=TestClient(app)
for path in ['/api/rosters/synergies','/api/rosters/generate']:
    for method in ['get','post','put','delete']:
        r=getattr(c, method)(path, json={'units':[]}) if method in ['post','put'] else getattr(c, method)(path)
        print(method.upper(), path, r.status_code, r.text[:120].replace('\n',' '))
for path in ['/api/units/orks','/api/units/orks/Boyz/weapons','/api/units/Boyz/detail']:
    r=c.get(path)
    print('GET', path, r.status_code, r.text[:160].replace('\n',' '))
PY
```

Key output:

```text
GET /api/rosters/synergies 401 {"detail":"Authentication required — please log in"}
POST /api/rosters/synergies 200 {"checks":[],"score":0}
GET /api/rosters/generate 401 {"detail":"Authentication required — please log in"}
POST /api/rosters/generate 200 {"roster":{...}}
GET /api/units/orks 404 {"detail":"Not Found"}
GET /api/units/orks/Boyz/weapons 404 {"detail":"Not Found"}
GET /api/units/Boyz/detail 200 {"name":"Boyz",...}
```

### Auto-play error contract probes

Command:

```bash
python3 - <<'PY'
from fastapi.testclient import TestClient
from main import app
c=TestClient(app)
for qs in ['roster_a_id=999999&roster_b_id=999998','roster_a_id=x&roster_b_id=1','roster_a_id=1&roster_b_id=2&deployment=bad']:
    r=c.post('/api/auto-play?'+qs)
    print(qs, r.status_code, r.text[:220].replace('\n',' '))
PY
```

Output:

```text
roster_a_id=999999&roster_b_id=999998 500 {"detail":"404: Roster A not found: 999999"}
roster_a_id=x&roster_b_id=1 422 {"detail":[...]}
roster_a_id=1&roster_b_id=2&deployment=bad 500 {"detail":"400: Unknown deployment type: bad"}
```

### Curl smoke for `/api/health`

A local server was already bound to `127.0.0.1:8000`. Starting a new no-reload server failed with address already in use, then the required curl smoke was run against the active local server.

Command:

```bash
curl -sS -i http://127.0.0.1:8000/api/health | head -20
```

Output:

```text
HTTP/1.1 200 OK
content-type: application/json
x-content-type-options: nosniff
x-frame-options: DENY
referrer-policy: strict-origin-when-cross-origin
permissions-policy: camera=(), microphone=(), geolocation=()

{"status":"ok","version":"0.7.7"}
```

## Route surface inventory summary

Main API routes discovered:

- `GET /api/health`
- `GET /api/factions`
- `GET /api/units`
- `GET /api/units/browse`
- `GET /api/units/{unit_name}/detail`
- `POST /api/simulate`
- `POST /api/simulate-unit`
- `GET /api/map/tiles`
- `GET /api/detachments`
- `GET /api/detachments/{detachment_name}`
- `POST /api/rosters`
- `GET /api/rosters`
- `POST /api/rosters/generate`
- `GET /api/rosters/{roster_id}`
- `PUT /api/rosters/{roster_id}`
- `POST /api/rosters/{roster_id}/duplicate`
- `DELETE /api/rosters/{roster_id}`
- `POST /api/rosters/synergies`
- `POST /api/auto-play`
- `GET /api/replays`
- `GET /api/replays/{game_id}`
- `GET /api/results/{game_id}`
- `GET /api/me`
- `POST /api/subscribe`
- `GET /api/subscribe/success`
- `GET /api/billing/portal`
- `POST /api/webhooks/stripe`

Page routes discovered:

- `/faction-browser`
- `/team-builder`
- `/scenario-setup`
- `/pmf-chart`
- `/my-rosters`
- `/replays`
- `/round-viewer/{scenario_id}`
- `/replay/{game_id}`
- `/result/{game_id}`
- `/pricing`
- `/account/billing`

## Findings

### CRITICAL-1 — `/api/auto-play` has no auth or roster ownership boundary

Files:

- `web/routes/api_replays.py:310-446`
- `main.py:131`

Problem:

`POST /api/auto-play` accepts `roster_a_id` and `roster_b_id`, loads both rows directly from the database, and has no `Depends(get_current_user)` dependency or ownership/public check.

Evidence from route dependency inventory:

```text
POST /api/auto-play web.routes.api_replays deps=[]
```

Why this blocks approval:

Roster IDs are private user data. This route allows an anonymous caller to reference arbitrary roster IDs for simulation. Even if the full roster JSON is not returned directly, it causes private roster content to be loaded into simulation state and reflected through replay/result artifacts.

Expected:

- Require authenticated user for simulations involving saved rosters.
- Permit roster access only when `row.user_id == user.id` or roster is explicitly public.
- If anonymous AI/random simulation is needed, expose a separate endpoint that does not accept private roster IDs.

Recommendation:

Add user dependency to `auto_play_simulation()` and reuse the same ownership policy as `get_roster()`. Add tests for:

- anonymous caller blocked;
- user cannot simulate another user's private roster;
- user can simulate own roster;
- public roster policy if intended.

### CRITICAL-2 — `/api/auto-play` wraps intended 404/400 errors as 500

File:

- `web/routes/api_replays.py:321-446`

Problem:

`auto_play_simulation()` raises `HTTPException` inside a broad `try`, then catches `Exception` and re-raises `HTTPException(status_code=500, detail=str(e))`. That converts expected client errors into internal server errors.

Evidence:

```text
POST /api/auto-play?roster_a_id=999999&roster_b_id=999998
=> 500 {"detail":"404: Roster A not found: 999999"}

POST /api/auto-play?roster_a_id=1&roster_b_id=2&deployment=bad
=> 500 {"detail":"400: Unknown deployment type: bad"}
```

Why this blocks approval:

The route violates response contract expectations and makes clients unable to distinguish invalid inputs from server failures. It also makes monitoring noisy because normal 404/400 conditions become 500s.

Expected:

- Preserve `HTTPException` status codes.
- Only unexpected exceptions should become 500s.

Recommendation:

Add `except HTTPException: raise` before the broad `except Exception as e` block, or reduce the try scope. Add direct tests for missing roster and invalid deployment status codes.

### CRITICAL-3 — PMF chart frontend calls removed/nonexistent unit API endpoints

File:

- `web/templates/pmf_chart.html`

Problem:

The PMF chart template still calls old route shapes:

- `GET /api/units/{faction}`
- `GET /api/units/{faction}/{unit}/weapons`

The current route surface exposes:

- `GET /api/units?faction=...`
- `GET /api/units/{unit_name}/detail`

Evidence:

```text
GET /api/units/orks => 404 {"detail":"Not Found"}
GET /api/units/orks/Boyz/weapons => 404 {"detail":"Not Found"}
GET /api/units/Boyz/detail => 200 {"name":"Boyz",...}
```

Why this blocks approval:

`/pmf-chart` can render, and `tests/test_pmf_chart.py` passes, but the interactive unit/weapon selectors are broken at runtime. This is exactly the kind of frontend/API method and path drift CR-13 is meant to catch.

Expected:

- PMF chart should use `GET /api/units?faction=...` for unit selection.
- Weapon selection should either use `GET /api/units/{unit_name}/detail` or a restored documented weapons endpoint.
- Tests should exercise the actual JS/API route contract, not only page HTML presence.

Recommendation:

Update PMF chart fetch URLs and response parsing. Add an API smoke test that extracts or mirrors every frontend `/api/...` fetch and asserts the route exists with the expected method.

### IMPORTANT-1 — Detachment endpoints have duplicate route ownership

Files:

- `web/routes/api.py:452-520`
- `web/routes/api_detachments.py:12-88`
- `main.py:129-130`

Problem:

Both `api.py` and `api_detachments.py` register the same detachment endpoints:

- `GET /api/detachments`
- `GET /api/detachments/{detachment_name}`

Evidence:

```text
('/api/detachments', 'GET') [('list_detachments', 'web.routes.api'), ('list_detachments', 'web.routes.api_detachments')]
('/api/detachments/{detachment_name}', 'GET') [('detachment_detail', 'web.routes.api'), ('detachment_detail', 'web.routes.api_detachments')]
```

Why this matters:

The CR-13 acceptance criteria explicitly require no duplicate route ownership. In FastAPI/Starlette, the first matching route wins, so `api_detachments.py` is effectively shadowed by `api.py`. Future fixes to one module may not affect the live endpoint.

Expected:

- One canonical owner for detachment API routes.
- `api.py` should not duplicate routes that belong to `api_detachments.py`, or the split-module router should not be included separately.

Recommendation:

Move detachment endpoints fully into `api_detachments.py` and delete/stop registering the duplicates from `api.py`. Add a route inventory test that fails on duplicate `(path, methods)` pairs except intentionally mounted aliases.

### IMPORTANT-2 — Dynamic roster routes intercept static-like names for wrong methods and return misleading auth errors

Files:

- `web/routes/api_rosters.py:140-376`
- `main.py:132`

Problem:

`/api/rosters/{roster_id}` is registered before `/api/rosters/synergies`. For unsupported methods on static names, requests are matched by the dynamic authenticated route and return auth errors instead of clear method/path errors.

Evidence:

```text
GET /api/rosters/synergies => 401 {"detail":"Authentication required — please log in"}
PUT /api/rosters/synergies => 401 {"detail":"Authentication required — please log in"}
DELETE /api/rosters/synergies => 401 {"detail":"Authentication required — please log in"}

GET /api/rosters/generate => 401 {"detail":"Authentication required — please log in"}
PUT /api/rosters/generate => 401 {"detail":"Authentication required — please log in"}
DELETE /api/rosters/generate => 401 {"detail":"Authentication required — please log in"}
```

`POST /api/rosters/synergies` still works because its exact `POST` route is eventually matched, but wrong-method requests are misleading and order-sensitive.

Why this matters:

CR-13 explicitly checks route ordering: static paths before `{id}` paths. Current ordering creates confusing client behavior and makes diagnostics harder.

Expected:

- Static subroutes such as `/generate` and `/synergies` should be registered before `/{roster_id}` routes.
- Unsupported methods should return an appropriate 405/404/422 contract, not an authentication prompt for a fake roster ID.

Recommendation:

Move all static roster routes before dynamic `/{roster_id}` routes. Consider using stricter path names such as `/rosters/by-id/{roster_id}` or typed route tests to avoid accidental static-name capture.

### IMPORTANT-3 — `public_only` roster listing exists but still requires authentication

File:

- `web/routes/api_rosters.py:140-152`

Problem:

`list_rosters()` supports `public_only: bool = False`, but the endpoint always depends on `get_current_user`:

```python
@router.get("/rosters")
async def list_rosters(user: User = Depends(get_current_user), public_only: bool = False):
```

Therefore anonymous public roster browsing is impossible through this route, even though the code has a public-only branch.

Evidence:

```text
GET /api/rosters => 401 {"detail":"Authentication required — please log in"}
```

Why this matters:

The route contract is internally inconsistent. Either public roster listing is intended and should be anonymously accessible, or the `public_only` parameter is dead API surface that should be removed.

Expected:

- If public roster browsing is intended: use optional auth and branch safely.
- If not intended: remove `public_only` from the endpoint contract.

Recommendation:

Clarify product behavior, then test both anonymous and authenticated cases. Keep private roster listing authenticated.

### IMPORTANT-4 — Billing/subscription API routes lack auth boundaries in the live route surface

File:

- `backend/billing/webhooks.py:23-46`

Problem:

Route inventory shows the billing endpoints are part of the live `/api` surface and have no dependencies:

```text
POST /api/subscribe        backend.billing.webhooks deps=[]
GET  /api/billing/portal   backend.billing.webhooks deps=[]
```

The implementation comments also say user extraction is still TODO.

Why this matters:

CR-13 checks auth dependencies on private endpoints. Billing/portal operations are private user actions and should not be anonymous. Full monetization review is CR-19, but the route surface already exposes unauthenticated subscription/account-management endpoints.

Expected:

- `/api/subscribe` should require an authenticated user.
- `/api/billing/portal` should require an authenticated user and use that user's Stripe customer/subscription state.
- Stripe webhook may remain unauthenticated at the app-auth layer, but must verify Stripe signatures in production; that is primarily CR-19/security follow-up.

Recommendation:

Add auth dependencies to user-facing billing endpoints and reserve unauthenticated handling only for verified Stripe webhooks.

### IMPORTANT-5 — Existing tests pass but do not enforce frontend/API route contract or route uniqueness

Files:

- `tests/test_pmf_chart.py`
- `tests/test_canvas_map.py`
- `tests/test_rosters.py`
- `tests/test_round_viewer.py`
- `tests/test_result_screen.py`
- route modules under `web/routes/`

Problem:

The focused suite passes:

```text
91 passed, 26 warnings in 11.97s
```

But the suite did not catch:

- nonexistent PMF chart API fetches;
- duplicate detachment route ownership;
- `/api/auto-play` unauthenticated access;
- `/api/auto-play` 404/400 converted to 500;
- static/dynamic route ordering surprises.

Why this matters:

CR-13 acceptance is about route structure, method correctness, ordering, auth, and response contracts. The current tests mostly verify selected page loads and happy paths, not route-surface invariants.

Expected:

Add dedicated API route-surface tests that assert:

- no duplicate `(path, methods)` pairs;
- static routes appear before dynamic siblings;
- every frontend `fetch('/api/...')` target maps to a real route/method;
- private endpoints have auth dependencies;
- key error contracts return 400/401/403/404/405/422 as intended, not accidental 500.

## Positive observations

- Core static-before-dynamic route ordering is correct for `GET /api/units/browse` before `GET /api/units/{unit_name}/detail`.
- `POST /api/rosters/generate` is registered before `GET/PUT/DELETE /api/rosters/{roster_id}`, so the generator happy path is not shadowed.
- Main frontend API paths for team builder, unit modal, detachment picker, scenario setup, replay viewer, and result screen mostly match the current route surface.
- `/api/health` works through both TestClient and curl against the local server.
- Standard FastAPI validation correctly returns `422` for malformed typed query params, e.g. `roster_a_id=x`.

## Recommended fix order

1. Secure `/api/auto-play` with authentication and roster ownership checks.
2. Preserve `HTTPException` status codes in `/api/auto-play`.
3. Fix PMF chart to use current unit/detail endpoints, or restore documented weapons endpoints.
4. Remove duplicate detachment endpoints from one module and keep a single canonical owner.
5. Reorder static roster routes before dynamic `/{roster_id}` routes.
6. Decide and enforce `public_only` roster listing behavior.
7. Add route-surface regression tests.
8. Add auth to user-facing billing endpoints; leave webhook-specific security to CR-19 if desired.

## Acceptance status

CR-13 acceptance was not met.

- No 405/401/404 due to method/order/register bugs: FAILED.
  - PMF chart calls 404 routes.
  - Wrong-method static roster subpaths return misleading 401s through dynamic route matching.
- Clear module ownership: FAILED.
  - Detachments are registered by two modules.
- Auth dependencies on private endpoints: FAILED.
  - `/api/auto-play` and user-facing billing endpoints lack auth dependencies.
- Error status and JSON consistency: FAILED.
  - `/api/auto-play` converts expected 404/400 to 500.

## Integrity notes

- Review-only; no production code changed.
- No secrets or credentials were found/preserved in this review artifact.
- `read_file` line-number prefixes were not written into source files.
- Markdown table corruption check should be run after status/index updates.
