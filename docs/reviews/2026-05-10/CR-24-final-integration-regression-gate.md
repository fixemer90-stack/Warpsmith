---
title: "CR-24 — Final integration regression gate"
date: 2026-05-10
status: completed
verdict: request-changes
critical: 1
important: 1
suggestions: 1
source: docs/requirements/code-review/cr-24-final-integration-regression-gate.md
---

# CR-24 — Final integration regression gate

## Verdict

Request Changes.

The executable regression gate is healthy: lint, format check, JS syntax checks, full pytest suite, local server health check, and browser smoke pages passed.

Release readiness is not approved because the full-code-review tracker still has unresolved blocking debt: 37 Critical and 111 Important findings remain open, no triage summary exists, and no accepted-debt register was found. The final gate also reproduced a result-page VP consistency issue: the generated smoke replay's runtime game state had Battle Ready VP included, but the stored replay/result page displayed the last per-round snapshot without that final bonus.

## Scope

Whole repository final integration gate, as requested by CR-24:

- Static quality gates: Ruff check and Ruff format check.
- Frontend syntax gates: Team Builder, Scenario Setup, Battlefield Map JS.
- Full pytest regression suite.
- Local server startup without reload and `/api/health` curl.
- Browser smoke for `/`, `/team-builder`, `/scenario-setup`, `/my-rosters`, `/result/<generated_game_id>`.
- Release-readiness tracker consistency.

## Findings

### Critical

1. `docs/requirements/code-review/code-review.md:18-26` — Release gate cannot approve while prior CR debt is still unresolved and untriaged.

   Evidence:
   - Status index before CR-24 final update reported:
     - Request Changes: 23
     - Critical open: 37
     - Important open: 111
   - `docs/reviews/**/triage-summary.md` search returned 0 files.
   - `docs/requirements/code-review/code-review.md:70-73` says CR-24 runs only after triage/fixes or an explicit decision to accept debt.
   - `docs/requirements/code-review-plan.md:770-780` defines done as: CR-00..CR-24 reports exist, every Critical fixed/re-reviewed, every Important fixed or accepted as debt, full regression gate passes or baseline failures documented, and `triage-summary.md` exists.

   Risk:
   - A passing test/lint/browser smoke gate would give a false release-ready signal even though the review program still has known Critical blockers.

   Recommended fix:
   - Create `docs/reviews/2026-05-10/triage-summary.md`.
   - Link every Critical/Important finding from CR-00..CR-24.
   - For each Critical: fix and re-review before release.
   - For each Important: fix or explicitly accept as debt with owner/date.
   - Re-run CR-24 after triage/remediation.

### Important

1. `backend/engine/ai/autoplay.py:486-501`, `web/routes/api_replays.py:422-435`, result smoke `/result/auto_242424` — Result/replay smoke shows final Battle Ready VP is not represented in the stored replay snapshot/result page.

   Evidence:
   - Generated CR-24 smoke replay:
     - `uv run python /tmp/cr24_generate_replay.py`
     - Output: `game_id=auto_242424 rounds=2 duration_ms=362.16 vp={'1': 38, '2': 14}`
   - Browser smoke `/result/auto_242424` displayed:
     - VP — ORKS: 28
     - VP — TAU: 4
   - API result probe:
     - `summary_vp= None`
     - `last_round_end_vp= {'1': 28, '2': 4}`
     - `summary_winner= 1`
   - Cause pattern: `run_auto_game()` adds Battle Ready VP after round logs/end-state snapshots are already collected; replay save persists those round snapshots, and the result page derives displayed VP from the replay data, not a post-bonus final snapshot.

   Risk:
   - Users see stale final VP on the result page. Winner may remain correct in this sample, but final score is wrong by 10 VP per player and can affect draw/winner presentation in edge cases.

   Recommended fix:
   - After Battle Ready VP is applied, update the final replay/end-state snapshot or append a final summary snapshot/event before saving replay.
   - Add regression coverage that `/api/results/{game_id}` and `/result/{game_id}` expose final VP including Battle Ready.

### Suggestions

1. Add a scripted CR-24 smoke command to the repo so the final gate is repeatable without ad-hoc `/tmp` scripts.

   Recommended shape:
   - `scripts/smoke_final_gate.py` or `scripts/generate_smoke_replay.py`.
   - Generate a tiny deterministic replay.
   - Assert `/api/results/{game_id}` and `/result/{game_id}` final VP/state consistency.
   - Clean up temporary DB rows or use an isolated test DB.

## Verification Story

### Static gates

Command:

```bash
uv run ruff check .
uv run ruff format --check .
node -c web/static/team_builder.js
node -c web/static/scenario_setup.js
node -c web/static/battlefield_map.js
```

Result:

```text
## ruff check
All checks passed!

## ruff format --check
98 files already formatted

## node syntax
```

Exit code: 0.

### Full pytest regression

Command:

```bash
rm -f *.db-shm *.db-wal && uv run python -m pytest tests/ -q
```

Result:

```text
collected 457 items
454 passed, 3 skipped, 33 warnings in 31.15s
```

Warnings:

- `backend/engine/replay.py:77`: `datetime.utcnow()` deprecation.
- `backend/auth/__init__.py:76-77`: `datetime.utcnow()` deprecation.

### Local server and health check

Server command:

```bash
uv run python3 -c "import uvicorn; uvicorn.run('main:app', host='127.0.0.1', port=8000, reload=False)"
```

Health command:

```bash
curl -i -sS http://127.0.0.1:8000/api/health
```

Result:

```text
HTTP/1.1 200 OK
content-type: application/json
x-content-type-options: nosniff
x-frame-options: DENY
referrer-policy: strict-origin-when-cross-origin
permissions-policy: camera=(), microphone=(), geolocation=()

{"status":"ok","version":"0.7.7"}
```

### Browser smoke

Pages checked with browser automation:

- `/` — loaded, no console messages/errors.
- `/team-builder` — loaded, faction/game-size controls visible, no console messages/errors.
- `/scenario-setup` — loaded, mission cards/map/start button area visible, no console messages/errors.
- `/my-rosters` — loaded guest/free-tier state, no console messages/errors.
- `/result/auto_242424` — loaded generated smoke result, no console messages/errors.

Generated replay command:

```bash
uv run python /tmp/cr24_generate_replay.py
```

Result:

```text
game_id=auto_242424 rounds=2 duration_ms=362.16 vp={'1': 38, '2': 14}
```

Result API consistency probe:

```text
summary_vp= None
last_round_end_vp= {'1': 28, '2': 4}
summary_winner= 1
```

### Release readiness tracker check

Command:

```bash
search_files target=files path=docs/reviews pattern=triage-summary.md
```

Result:

```text
total_count: 0
```

Tracker state observed before CR-24 final update:

```text
Request Changes: 23
Critical open: 37
Important open: 111
Pending: 0 after CR-24 start
```

## What is done well

- Python lint and format gates are clean.
- Full pytest suite passes: 454 passed, 3 skipped.
- Key unauthenticated browser pages load without JavaScript console errors.
- Local no-reload server starts and `/api/health` returns versioned 200 OK with security headers.
- Deterministic result smoke can generate and display a real replay/result path.

## Release readiness

Not release-ready.

Gate status:

- Code regression gate: pass.
- Browser smoke gate: pass.
- Release/debt gate: fail.
- Result VP consistency: fail.

Required before approving release readiness:

1. Triage/fix/accept all CR-00..CR-24 Critical/Important findings.
2. Create and link `docs/reviews/2026-05-10/triage-summary.md`.
3. Fix/re-review result final VP snapshot consistency.
4. Re-run CR-24 final gate.
