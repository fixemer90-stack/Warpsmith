---
title: "CR-18 — Pages/templates/navigation review"
status: request-changes
date: 2026-05-10
review: CR-18
scope:
  - web/templates/
  - web/routes/pages.py
  - web/routes/auth.py
  - main.py favicon/static handling
  - web/static/progressive_disclosure.js
  - web/static/tooltips.js
verdict: request-changes
critical: 0
important: 4
suggestions: 1
---

# CR-18 — Pages/templates/navigation review

## Verdict

Request Changes.

The common app shell mostly renders and the main page routes/static assets are reachable, but the review found stale/broken navigation and app-shell regressions that can affect monetization and common UI behavior.

Severity summary:

- Critical: 0
- Important: 4
- Suggestions: 1

## Scope inspected

- `web/templates/base.html`
- `web/templates/index.html`
- `web/templates/pricing.html`
- `web/templates/auth/login.html`
- `web/templates/auth/register.html`
- Common templates under `web/templates/`
- `web/routes/pages.py`
- `web/routes/auth.py`
- `main.py` favicon/static setup
- `backend/billing/webhooks.py` for pricing link target contract
- `web/static/progressive_disclosure.js`
- `web/static/tooltips.js`
- Focused tests around progressive disclosure, tooltips, security headers, faction browser, and PMF page

## Verification performed

### Static / syntax checks

```bash
node -c web/static/progressive_disclosure.js
node -c web/static/tooltips.js
node -c web/static/faction_browser.js
node -c web/static/my_rosters.js
node -c web/static/result_chart.js
```

Result: passed.

### Focused pytest

Initial stale command included non-existent files and failed as expected:

```bash
uv run python -m pytest tests/test_progressive_disclosure.py tests/test_favicon.py tests/test_auth_pages.py tests/test_monetization.py -q
```

Result: `ERROR: file or directory not found: tests/test_favicon.py`.

Corrected focused command:

```bash
uv run python -m pytest \
  tests/test_progressive_disclosure.py \
  tests/test_tooltips.py \
  tests/test_security_headers.py \
  tests/test_faction_browser.py \
  tests/test_pmf_chart.py \
  -q
```

Result: `40 passed`.

### Route/static smoke with TestClient

Custom route/static probe checked common pages and static assets:

- `/` → 200
- `/team-builder` → 200
- `/my-rosters` → 200
- `/faction-browser` → 200
- `/scenario-setup` → 200
- `/pricing` → 200
- `/account/billing` → 200
- `/replays` → 200
- `/pmf-chart` → 200
- `/auth/login` → 200
- `/auth/register` → 200
- `/favicon.ico` → 307 `/static/favicon.svg`
- `/static/favicon.svg` → 200
- `/static/progressive_disclosure.js` → 200
- `/static/tooltips.js` → 200
- `/static/faction_browser.js` → 200
- `/static/my_rosters.js` → 200
- `/static/result_chart.js` → 200

Pricing CTA target probe:

- `/api/subscribe` with GET → 405, `Allow: POST`
- `/api/billing/portal` with GET → 302 `/account/billing`

### Live browser smoke

Against `http://127.0.0.1:8000`:

- `/` loaded with nav links for Warpsmith, Team Builder, Rosters, Browser, Scenario, Login, Register.
- Base scripts loaded once for Tailwind, Chart.js, HTMX, Alpine, `progressive_disclosure.js`, and `tooltips.js`.
- Favicon link resolved to `/static/favicon.svg`.
- Body defaulted to `mode-expert`.
- Beginner/Expert toggle changed body classes and persisted `warpsmith_display_mode` in `localStorage`.
- Browser fetch smoke confirmed common pages returned 200 and `/api/subscribe` returned 405 for the pricing GET path.

### Deterministic probes

#### Shared CSS helper classes

On `/pricing`, CSSOM showed the runtime CSS rules generated from `@apply` are empty:

```text
.card { }
.btn { }
```

Observed computed styles:

```text
.card background-color: rgba(0, 0, 0, 0)
.card padding: 0px
.btn padding: 0px
```

#### Progressive disclosure localStorage failure path

Node VM probe with `localStorage.getItem()` throwing:

```text
loadMode threw: blocked getItem
setMode ok
```

This confirms `loadMode()` is not protected while `setMode()` only protects `setItem()`.

### Codex attempt

Required Codex review was attempted but unavailable in this environment:

```bash
codex exec "Review CR-18 Pages/templates/navigation scope ..."
```

Result:

```text
/usr/bin/bash: line 3: codex: command not found
```

Independent review was performed with a delegated reviewer instead.

## Findings

### Important — CR18-01 — Premium upgrade CTA is a stale/broken navigation link

Files:

- `web/templates/pricing.html:55-58`
- `backend/billing/webhooks.py:23-33`

Evidence:

`pricing.html` renders the Premium CTA as a normal anchor:

```html
<a href="/api/subscribe" class="btn w-full text-center block bg-yellow-500 hover:bg-yellow-400 text-black">
    🔥 Upgrade to Premium
</a>
```

The target route is POST-only:

```python
@router.post("/subscribe")
async def create_checkout():
    return RedirectResponse(url="/pricing", status_code=302)
```

Verification:

```text
/api/subscribe GET 405 POST
BROKEN /pricing -> /api/subscribe: 405 allow=POST
```

Impact:

The Pricing page advertises an Upgrade action, but clicking it performs a GET request and receives 405 Method Not Allowed. This directly breaks the monetization entry point and violates the CR-18 “no stale navigation links” acceptance criterion.

Required change:

Make the CTA match the route contract. Either render a POST form/button for `/api/subscribe`, or expose a safe GET checkout/start route if the intended UX is a link.

### Important — CR18-02 — Shared `.card`, `.btn`, and `.input` classes do not apply in browser

File:

- `web/templates/base.html:14-23`

Evidence:

The base template defines common helper classes with Tailwind `@apply` inside a runtime `<style>` block:

```css
.card {
    @apply bg-gray-800 border border-gray-700 rounded-lg p-6;
}

.btn {
    @apply bg-yellow-600 hover:bg-yellow-500 font-bold py-2 px-4 rounded transition;
}

.input {
    @apply w-full bg-gray-700 border border-gray-600 rounded px-3 py-2;
}
```

Tailwind CDN in the browser does not process `@apply` in arbitrary runtime style blocks. Browser CSSOM confirmed:

```text
.card { }
.btn { }
```

Computed style on `/pricing` confirmed the helpers are effectively missing:

```text
.card background-color: rgba(0, 0, 0, 0)
.card padding: 0px
.btn padding: 0px
```

Impact:

Common page shell components relying on `.card`, `.btn`, or `.input` lose intended styling and layout. This affects Pricing cards/buttons and shared navigation/register controls. It is not a backend 500, but it breaks common template presentation in a way static tests do not catch.

Required change:

Replace these helper classes with literal Tailwind classes in templates, compile Tailwind properly, or move the resolved CSS declarations into plain CSS without `@apply`.

### Important — CR18-03 — Progressive Disclosure can fail during page initialization when `localStorage.getItem` is blocked

File:

- `web/static/progressive_disclosure.js:9-14`

Evidence:

`loadMode()` reads `localStorage` without a try/catch:

```javascript
loadMode() {
    const saved = localStorage.getItem('warpsmith_display_mode');
    if (saved && ['beginner', 'expert'].includes(saved)) {
        this.mode = saved;
    }
    this.applyMode();
},
```

Only `setItem()` is protected in `setMode()`.

Deterministic VM probe:

```text
loadMode threw: blocked getItem
setMode ok
```

Impact:

In browsers or privacy contexts where `localStorage.getItem()` throws, the Alpine component in `base.html` can fail in `x-init="loadMode()"`. That breaks the shared Beginner/Expert mode toggle and can leave `mode-beginner`/`mode-expert` classes unapplied.

Required change:

Wrap the `getItem()` path in try/catch and fall back to expert mode before calling `applyMode()`.

### Important — CR18-04 — Test coverage misses the actual CR-18 navigation/template failure modes

Files:

- `tests/test_progressive_disclosure.py`
- `tests/test_tooltips.py`
- Missing focused tests for pricing CTA, favicon route, auth/index titles, common route matrix, and CSS helper behavior

Evidence:

The focused existing tests pass:

```text
40 passed
```

But they do not catch:

- `/pricing` CTA GET `/api/subscribe` returning 405.
- Runtime CSS helper rules being empty because `@apply` is not compiled by the CDN path.
- `localStorage.getItem()` throwing in `progressiveDisclosure.loadMode()`.
- Empty `<title>` on `/`, `/auth/login`, and `/auth/register`.

The first attempted CR-18 test command also referenced non-existent test files:

```text
ERROR: file or directory not found: tests/test_favicon.py
```

Impact:

CR-18 acceptance is about navigation/common templates/static shell behavior, but the test suite mostly checks static strings and misses the real shell contract regressions. Future changes can keep CI green while breaking monetization/navigation/UI shell behavior.

Required change:

Add focused tests/probes for:

- all common page routes;
- all internal anchors rendered by base/pricing/auth/index pages;
- `/favicon.ico` redirect and `/static/favicon.svg` reachability;
- pricing checkout CTA method/route contract;
- progressive disclosure fallback when storage is unavailable;
- browser/CSS smoke or a build-time check preventing raw `@apply` in runtime templates.

### Suggestion — CR18-05 — Index and auth pages render blank document titles

Files:

- `web/templates/base.html:7`
- `main.py:114-117`
- `web/routes/auth.py:44-53`

Evidence:

The base template renders:

```html
<title>{{ title }}</title>
```

But index/login/register do not pass `title`.

Probe output:

```text
/ 200 ''
/auth/login 200 ''
/auth/register 200 ''
/team-builder 200 'Team Builder'
/pricing 200 'Pricing — Warpsmith'
```

Impact:

This does not break routing, but it degrades browser tabs, accessibility context, and page identity for the main entry/auth pages.

Recommended change:

Pass explicit titles from index/login/register routes or use a safe default in `base.html`, for example `{{ title|default('Warpsmith') }}`.

## Positives

- Common page routes reviewed returned 200.
- `/favicon.ico` is wired and redirects to `/static/favicon.svg`.
- Static JS files in scope are reachable and syntax-valid.
- Progressive disclosure works in the normal browser path: default Expert mode applies, toggle switches body classes, and selected mode persists.
- No Jinja/Alpine template conflict caused 500s on the common pages smoked in this review.

## Required follow-up

Before CR-18 can be approved:

1. Fix the `/pricing` Premium CTA method/route mismatch.
2. Remove runtime Tailwind `@apply` usage from `base.html` or introduce a real Tailwind build step.
3. Harden `progressiveDisclosure.loadMode()` against blocked `localStorage.getItem()`.
4. Add tests/probes covering real navigation/template/static contracts, not only static strings.

## Final status

Request Changes.
