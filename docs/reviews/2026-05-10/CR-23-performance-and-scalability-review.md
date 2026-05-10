---
title: "CR-23 — Performance and scalability review"
date: 2026-05-10
artifact: ../../requirements/code-review/cr-23-performance-and-scalability-review.md
verdict: request-changes
critical: 0
important: 7
suggestions: 3
status: completed
---

# CR-23 — Performance and scalability review

## Verdict

Request Changes.

No Critical performance/scalability blockers were found for the current small dataset, but the commercialization path has several Important scalability risks: unbounded list endpoints, missing list indexes, frontend N+1 detail calls, repeated faction markdown parsing, synchronous CPU-bound auto-play in the request handler, and non-monotonic timing telemetry.

## Scope inspected

- Loader/cache: `backend/loader/registry.py`
- DB schema/query wrapper: `backend/db/database.py`
- Replay persistence/list helpers: `backend/engine/replay.py`
- Auto-play runtime: `backend/engine/ai/autoplay.py`
- API list/detail routes: `web/routes/api.py`, `web/routes/api_rosters.py`, `web/routes/api_replays.py`
- Page route data preload: `web/routes/pages.py`
- Frontend rendering/data loading loops: `web/static/team_builder.js`, `web/static/scenario_setup.js`
- Tests: `tests/test_replay.py`, `tests/test_rosters.py`

## Commands and evidence

```bash
# Date for report path
$ date +%F
2026-05-10

# Scoped regression tests for replay/roster surfaces
$ rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_replay.py tests/test_rosters.py -q
33 passed, 33 warnings in 6.12s

# Codex CLI availability check
$ command -v codex || true
# no output — Codex CLI unavailable in this environment

# Lightweight CR-23 timing probe
$ uv run python /tmp/cr23_perf_probe.py
registry cold load no cache: min=1129.63ms median=1129.63ms max=1129.63ms
registry counts: units=160 detachments=23 mtimes=183 cache_size=138729
registry warm load from cache: min=710.19ms median=710.19ms max=710.19ms
registry already-loaded no-op load x1000: min=0.09ms median=0.09ms max=0.09ms
GET /api/factions x5: min=102.96ms median=106.26ms max=823.03ms status=200 bytes=127
GET /api/units x5: min=9.25ms median=10.75ms max=14.30ms status=200 bytes=64765 units=160
GET /api/units/browse?page=1&per_page=50 x5: min=3.64ms median=4.05ms max=6.25ms status=200 bytes=13979 items=50 total=160 pages=4
sqlite replays unbounded SELECT over 5000 rows: min=7.21ms median=8.65ms max=9.26ms rows=5000
sqlite replays bounded SELECT LIMIT 20 over 5000 rows: min=0.36ms median=0.40ms max=0.70ms rows=20

# Auto-play runtime smoke using real wiki units
$ uv run python - <<'PY'
# constructed small RosterState objects from registry and ran run_auto_game(...)
PY
run_auto_game 3v3 max_rounds=3 wall=445.62ms reported=445.60 error=None rounds=3 units=6
run_auto_game 8v8 max_rounds=3 wall=922.77ms reported=-1302.90 error=None rounds=3 units=16
run_auto_game 15v15 max_rounds=3 wall=1858.12ms reported=1858.04 error=None rounds=3 units=30
```

## Findings

### Important 1 — `/api/replays` is unbounded and bypasses the existing limited helper

Evidence:
- `web/routes/api_replays.py:461-479` executes:
  `SELECT game_id, created_at, mission, deployment, seed, summary FROM replays ORDER BY created_at DESC`
  with no `LIMIT`, no `OFFSET`, no cursor, and no user filter.
- `backend/engine/replay.py:394-424` already has `list_replays(db, user_id=None, limit=20)`, but the route does not use it.
- `backend/db/database.py:118-135` creates `replays` without `created_at` or `(user_id, created_at)` indexes.
- Probe over 5,000 rows: unbounded list median 8.65ms/5,000 rows vs bounded `LIMIT 20` median 0.40ms/20 rows. Query time is already 20x higher; response size/JSON parsing will scale worse.

Risk:
- Replay history grows naturally with commercialization. The endpoint will return every replay metadata row and parse every summary on every `/replays` refresh.

Recommendation:
- Add `page/per_page` or cursor pagination to `GET /api/replays`; default to 20 or 50 rows.
- Reuse `backend.engine.replay.list_replays()` or delete the duplicate route-side list implementation.
- Add indexes:
  - `CREATE INDEX IF NOT EXISTS idx_replays_created_at ON replays(created_at DESC);`
  - `CREATE INDEX IF NOT EXISTS idx_replays_user_created ON replays(user_id, created_at DESC);`

### Important 2 — roster list endpoints are unpaginated and `SELECT *` pulls large units JSON

Evidence:
- `web/routes/api_rosters.py:140-152` returns all current-user rosters or all public rosters.
- Both paths use `SELECT *`, then `_parse_roster_row()` parses the `units` JSON for every returned row.
- `backend/db/database.py:132-133` indexes `user_id` and `faction`, but has no index supporting `WHERE is_public = 1 ORDER BY updated_at DESC`.

Risk:
- The current Free tier caps personal rosters, but public rosters can become a commercial gallery/community surface. Returning full `units` blobs for list cards is unnecessary bandwidth and CPU.

Recommendation:
- Add `page/per_page` to `GET /api/rosters`.
- Return lightweight list metadata by default: `id`, `name`, `faction`, `pts_limit`, `detachment`, `is_public`, `updated_at`, and optionally `unit_count`.
- Keep full `units` JSON for `GET /api/rosters/{id}`.
- Add `CREATE INDEX IF NOT EXISTS idx_rosters_public_updated ON rosters(is_public, updated_at DESC);`.

### Important 3 — Scenario Setup creates frontend N+1 detail requests for roster units

Evidence:
- `web/static/scenario_setup.js:139-145` calls `Promise.all(rawUnits.map(u => this.loadUnitDetails(u.unit_name)))` for every selected roster unit.
- `web/static/scenario_setup.js:167-170` repeats the same pattern for generated opponents.
- `web/static/scenario_setup.js:189-192` issues one `GET /api/units/{unit}/detail` per unit.

Risk:
- A 15v15 setup can trigger about 30 concurrent unit-detail requests just to draw map markers. This multiplies registry access, JSON serialization, browser scheduling overhead, and API concurrency for one page interaction.

Recommendation:
- Add a batch endpoint such as `POST /api/units/details` accepting unit names.
- Or include required map display metadata (`icon_url`, `color`, `category`) in roster responses.
- Add a client-side detail cache by unit name so the same unit is never fetched twice in one page session.

### Important 4 — registry warm cache still has high O(files) startup cost and does not detect newly added wiki files

Evidence:
- `backend/loader/registry.py:196-220` loads the pickle cache, then stats every cached path to validate mtimes.
- It only validates paths present in the cache. A newly added unit/detachment markdown file is not in `mtimes`, so the cache can still be considered valid and the new content is missed until cache invalidation.
- Probe: cold load 1129.63ms; warm cache load still 710.19ms for 183 tracked files.

Risk:
- Wiki growth increases startup/first-request latency. Content additions can be invisible in production if the cache survives deploys or volume reuse.

Recommendation:
- Store and compare a full manifest: directory snapshot, file count, path list hash, or git/content revision.
- Consider directory mtimes plus file count/hash to avoid statting every file on each warm load.
- Expose explicit cache invalidation/refresh for admin/deploy flows.
- Initialize registry at app startup so first user request does not pay cold-load latency.

### Important 5 — `/api/factions` and page routes parse faction markdown on every request

Evidence:
- `web/routes/api.py:632-669` loads faction labels by reading `wiki/factions/*.md` through `frontmatter.load()` on each request; filename fallback scans the directory for case-insensitive matches.
- `web/routes/pages.py:44-61` repeats similar parsing for `/team-builder`.
- `web/routes/pages.py:84-96` repeats similar parsing for `/scenario-setup`.
- Probe: `/api/factions` median 106.26ms and first request 823.03ms, much slower than `/api/units` median 10.75ms.

Risk:
- Faction metadata is static between wiki updates but pays disk IO and markdown parsing on common page/API requests.

Recommendation:
- Load faction metadata once in `WikiRegistry.load()` as `list_faction_metadata()` or equivalent.
- Reuse the same helper in API and page routes.
- Remove per-request case-insensitive directory scans.

### Important 6 — auto-play simulation is synchronous inside an async route and `max_rounds` is unbounded

Evidence:
- `web/routes/api_replays.py:310-318` exposes `max_rounds: int = 5` with no FastAPI `Query(..., ge=1, le=5)` bound.
- `web/routes/api_replays.py:399-400` calls CPU-bound `run_auto_game()` directly inside the async request handler.
- `backend/engine/ai/autoplay.py:456-484` loops over `range(config.max_rounds)` and only checks the 30s timeout at the start of each round.
- Runtime smoke: 15v15, 3 rounds completed in 1858.12ms now, under the 30s NFR; however concurrent requests will block the FastAPI event loop/worker during simulation.

Risk:
- Commercial traffic can starve the event loop. A large `max_rounds` value can hold a worker until the timeout guard fires.

Recommendation:
- Validate `max_rounds` with bounds, e.g. `max_rounds: int = Query(5, ge=1, le=5)`.
- Offload simulations to a worker/thread/process queue in production and return a job id.
- Enforce per-user/IP concurrency and quota gates for `/api/auto-play`.

### Important 7 — elapsed timing uses wall-clock `time.time()`, producing unreliable/negative telemetry

Evidence:
- `backend/engine/ai/autoplay.py:374`, `:458`, `:500`, `:510`, `:519` use `time.time()` for elapsed/duration measurements.
- `backend/engine/replay.py:90` and `:110` use `time.time()` for replay elapsed timestamps.
- Runtime smoke observed one `AutoPlayResult.total_duration_ms = -1302.90` while wall time was 922.77ms.

Risk:
- Wall-clock adjustments make runtime telemetry negative or inconsistent, undermining performance monitoring and the `< 30 sec` guard semantics.

Recommendation:
- Use `time.perf_counter()` or `time.monotonic()` for elapsed durations and timeout checks.
- Keep `datetime`/UTC only for user-visible timestamps such as `created_at`.

### Suggestion 1 — `/api/units` remains an unpaginated full-list endpoint while `/api/units/browse` is smaller and paginated

Evidence:
- `web/routes/api.py:66-117` serializes all units for a faction or all factions, including abilities and weapon summaries.
- Probe: `/api/units` returns 64,765 bytes for 160 units.
- `web/routes/api.py:265-378` implements `/api/units/browse` with `page` and `per_page`; probe showed 13,979 bytes for `per_page=50` and median 4.05ms.
- `web/static/team_builder.js:252-267` still uses `/api/units?faction=...`.

Recommendation:
- Keep `/api/units` for compatibility, but treat it as legacy/internal.
- Switch Team Builder to `/api/units/browse` with filters or add a slim faction-units endpoint.
- Add HTTP caching/ETag for static wiki-derived unit data.

### Suggestion 2 — `/scenario-setup` selects roster `units` but drops them before rendering

Evidence:
- `web/routes/pages.py:107-109` selects `id, name, faction, pts_limit, detachment, units`.
- `web/routes/pages.py:111-119` appends only `id`, `name`, `faction`, and `pts_limit` to the template data.

Risk:
- Pulls potentially large `units` JSON during page render without using it.

Recommendation:
- Drop `units` from this SQL query.
- Load full roster details only when a roster is selected, preferably through a compact/batch API path.

### Suggestion 3 — replay JSON is pretty-printed in SQLite storage

Evidence:
- `backend/engine/replay.py:323` stores replay JSON using `json.dumps(..., indent=2)`.
- `backend/engine/replay.py:360-380` saves the full replay JSON blob to SQLite.

Risk:
- Pretty-printed JSON increases DB size and IO for every replay. Current games are small, but this grows with event volume and replay count.

Recommendation:
- Store compact JSON with `separators=(",", ":")`.
- Keep pretty formatting only for exports/debug output.
- Consider future round-level lazy loading: `/api/replays/{game_id}/rounds/{round}`.

## Positive observations

- `WikiRegistry.load()` is effectively a no-op after `_loaded=True`; 1000 repeated calls took 0.09ms.
- `/api/units/browse` already has a paginated shape and should be reused more broadly.
- Current auto-play runtime smoke is well under the 30s NFR for 3-round 30-unit scenarios.
- Replay helper `list_replays(limit=20)` already exists; the fix can reuse it rather than introduce new logic from scratch.

## Acceptance result

Accepted as completed for CR-23: performance risks are separated into Critical/Important/Suggestion and include measured evidence where possible.

Blocking outcome: Request Changes until Important issues are triaged or accepted as explicit technical debt.
