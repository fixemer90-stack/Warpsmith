---
title: "CR-17 — Scenario Setup and battlefield map frontend review"
status: request-changes
date: 2026-05-10
review: CR-17
scope:
  - web/templates/scenario_setup.html
  - web/static/scenario_setup.js
  - web/static/battlefield_map.js
  - web/templates/partials/battlefield_map.html
  - tests/test_canvas_map.py
  - web/routes/api_replays.py
  - backend/engine/ai/deployment.py
---

# CR-17 — Scenario Setup and battlefield map frontend review

## Verdict

**Status:** Request Changes

The Scenario Setup page renders and the happy path can start a simulation, but several visible setup controls are not honored by the launch contract. The strategic map is also misleading for mission-specific deployment: it always previews left/right deployment zones, while mission cards advertise different deployment types and the backend has separate deployment implementations.

## Summary

- Critical findings: 0
- Important findings: 4
- Suggestions: 1

## Findings

### Important — CR17-01 — Mission deployment is not sent to `/api/auto-play`

**Files:**

- `web/templates/scenario_setup.html:106`
- `web/templates/scenario_setup.html:118`
- `web/templates/scenario_setup.html:130`
- `web/static/scenario_setup.js:289-294`
- `web/routes/api_replays.py:310-318`
- `backend/engine/ai/deployment.py:25-29`

**Evidence:**

The UI mission cards describe mission-specific deployments:

- Only War: `Dawn of War deployment.`
- Purge the Foe: `Search & Destroy deployment.`
- Take and Hold: `Crucible of Battle deployment.`

`startSimulation()` sends only these params:

```js
const params = new URLSearchParams({
    roster_a_id: rosterAId, roster_b_id: rosterBId,
    mission: this.mission, max_rounds: '5',
    seed: String(Math.floor(Math.random() * 100000)),
});
```

The backend endpoint defaults `deployment` to `standard`:

```py
async def auto_play_simulation(
    roster_a_id: int,
    roster_b_id: int,
    mission: str = "only_war",
    deployment: str = "standard",
    max_rounds: int = 5,
    seed: int | None = None,
):
```

Browser smoke confirmed the result page after a Scenario Setup launch showed:

```text
Mission: only-war · Deployment: standard
```

**Impact:**

Users can select missions that promise Dawn of War/Search & Destroy/Crucible deployment, but the launched simulation uses `standard` unless the request is manually altered outside the UI. This makes Scenario Setup materially misrepresent the battle it starts.

**Recommendation:**

Map mission to a backend deployment value in `scenario_setup.js` and send `deployment` to `/api/auto-play`. If `Crucible of Battle` is intended, add a matching backend `DeploymentType` or change the UI copy to a supported deployment type.

---

### Important — CR17-02 — Battlefield preview deployment zones are mission-agnostic

**Files:**

- `web/static/battlefield_map.js:27`
- `web/static/battlefield_map.js:63-68`
- `web/static/battlefield_map.js:117-126`
- `web/static/scenario_setup.js:197-213`
- `backend/engine/ai/deployment.py:61-79`

**Evidence:**

`battlefieldMap().initMap()` stores `deployZones`, but `drawDeployZones()` ignores `this.deployZones` and recomputes the same left/right 20% zones every time:

```js
drawDeployZones() {
    const zone = this.getDefaultDeployZones(this.mapWidth, this.mapHeight);
    ...
}
```

`getDefaultDeployZones()` is always:

```js
p1: { x: 0, y: 0, width: zoneWidth, height },
p2: { x: width - zoneWidth, y: 0, width: zoneWidth, height },
```

`scenario_setup.js` places roster units with the same left/right 20% logic regardless of selected mission.

The backend deployment code supports different layouts for `STANDARD`, `SEARCH_AND_DESTROY`, and `DAWN_OF_WAR`.

**Impact:**

The strategic map is not a reliable preview for missions with non-standard deployment. It can show units in left/right strips while the actual deployment should be corners or long-edge zones.

**Recommendation:**

Derive preview deployment zones from the selected mission/deployment and pass them into `battlefieldMap().initMap(...)`. Make `drawDeployZones()` use `this.deployZones` rather than recomputing defaults.

---

### Important — CR17-03 — Game Format can diverge from actual simulation size

**Files:**

- `web/static/scenario_setup.js:21-31`
- `web/static/scenario_setup.js:67-78`
- `web/static/scenario_setup.js:235-241`
- `web/static/scenario_setup.js:289-294`

**Evidence:**

The frontend preview uses `gameFormat` to render 44×30, 44×44, 44×60, or 44×90. However, `startSimulation()` does not send `gameFormat`, map dimensions, or pts format to `/api/auto-play`.

Opponent generation also uses Player 1 roster points instead of the selected format:

```js
const p1 = this.rosters.find(r => r.id == this.player1Roster);
const pts = p1 ? p1.pts_limit : 2000;
...
body: JSON.stringify({ faction, pts_limit: pts }),
```

**Impact:**

A user can select a game format and see one table size in the preview, but launch a battle whose generated opponent and simulation setup are driven by roster points/backend defaults instead of the selected format. The control appears authoritative but is not part of the simulation contract.

**Recommendation:**

Either make Game Format authoritative by sending the selected format/map size to backend launch and generation, or remove/disable formats that cannot affect simulation.

---

### Important — CR17-04 — First Turn selector is dead UI state

**Files:**

- `web/templates/scenario_setup.html:155-160`
- `web/static/scenario_setup.js:11`
- `web/static/scenario_setup.js:289-294`
- `web/routes/api_replays.py:310-318`

**Evidence:**

The page exposes a `First Turn` select with `roll-off`, `player1`, and `player2`, and the Alpine component stores `firstTurn`. `startSimulation()` never sends it to the backend, and `/api/auto-play` has no corresponding parameter.

**Impact:**

Changing the First Turn control has no effect. This is misleading and can invalidate user expectations when comparing repeated simulations.

**Recommendation:**

Implement a first-turn/initiative parameter end-to-end or remove the selector until the engine supports it.

---

### Suggestion — CR17-05 — Current tests are mostly static and miss launch-contract regressions

**Files:**

- `tests/test_canvas_map.py:63-132`

**Evidence:**

Current tests verify that Scenario Setup includes `battlefield-map-svg`, `battlefield_map.js`, static JS symbols, and dynamic `/api/map/tiles` dimensions. They do not assert:

- mission-specific deployment is sent to `/api/auto-play`;
- First Turn affects launch;
- selected Game Format affects launch/generation;
- map preview deployment zones change by mission;
- browser-level `startSimulation()` builds the expected query string.

**Impact:**

The selected test set can pass while key setup controls remain disconnected from the simulation.

**Recommendation:**

Add frontend contract tests or browser tests for generated launch URL/query parameters and mission-specific map deployment behavior.

## Verification Performed

### Static/code inspection

Reviewed:

- `web/templates/scenario_setup.html`
- `web/static/scenario_setup.js`
- `web/static/battlefield_map.js`
- `web/templates/partials/battlefield_map.html`
- `tests/test_canvas_map.py`
- `tests/test_scenario.py`
- `web/routes/pages.py`
- `web/routes/api_rosters.py`
- `web/routes/api_replays.py`
- `backend/state/mission.py`
- `backend/engine/ai/deployment.py`
- `docs/features/f4.14-strategic-battlefield-map.md`

### Automated checks

```bash
node -c web/static/scenario_setup.js
node -c web/static/battlefield_map.js
uv run python -m pytest tests/test_canvas_map.py tests/test_scenario.py tests/test_autoplay.py -q
```

Result:

```text
33 passed
```

### Codex delegation attempt

Required Codex command was attempted but the CLI is not available in this environment:

```text
/usr/bin/bash: line 3: codex: command not found
```

Review continued with direct inspection, browser smoke checks, and an independent delegated reviewer.

### Browser smoke checks

Local server health:

```text
GET /api/health -> 200 {"status":"ok","version":"0.7.7"}
```

`/scenario-setup` smoke:

- page rendered without JS errors;
- initial map: `44×60″ · Only War · 3 objectives · 0 units`;
- changing format/mission to Combat Patrol + Take and Hold updated map to `44×30″ · Take And Hold · 5 objectives · 0 units`;
- generated Orks opponent loaded and map unit markers appeared;
- with an authenticated temp user and saved Player 1 roster, generated opponent launch redirected to `/result/auto_83385`;
- result page showed `Mission: only-war · Deployment: standard`, confirming CR17-01.

## Final Recommendation

Request changes before closing CR-17. The page is usable on the happy path, but the setup controls must either be wired into simulation launch or removed/renamed so the UI no longer promises configuration that the engine ignores.
