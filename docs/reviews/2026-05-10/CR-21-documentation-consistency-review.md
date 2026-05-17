---
title: "CR-21 — Documentation consistency review"
status: request-changes
date: 2026-05-10
review: CR-21
scope:
  - README.md
  - DEV_INDEX.md
  - AGENTS.md
  - CHANGELOG.md
  - ROADMAP.md
  - ROADMAP.html
  - docs/architecture/C4.md
  - docs/features/*.md
  - docs/api/endpoints.md
verdict: request-changes
summary:
  critical: 0
  important: 8
  suggestions: 2
---

# CR-21 — Documentation consistency review

## Verdict

Request Changes.

The documentation set does not consistently describe the current repository state. Several top-level docs and feature specs have drifted from the live code, current route surface, database schema, test suite, wiki inventory, and production/security behavior.

No source-code fixes were applied. This was a review-only pass; only CR tracking/report files were updated.

## Scope reviewed

- `README.md`
- `DEV_INDEX.md`
- `AGENTS.md`
- `CHANGELOG.md`
- `ROADMAP.md`
- `ROADMAP.html`
- `docs/architecture/C4.md`
- `docs/features/*.md`
- `docs/api/endpoints.md`
- Current code/test reality used for comparison:
  - FastAPI route introspection from `main.app`
  - pytest collection
  - wiki file count from `wiki/**/*.md`
  - DB schema introspection from SQLite
  - targeted stale-claim scans for phase count, Morale, old maps, missing paths, stale counts

## Findings

### Critical

None.

### Important

#### I1 — Top-level test counts are stale

Evidence:

- Runtime verification: `uv run python -m pytest --collect-only -q` reports `457 tests collected`.
- Stale docs still claim 454 tests:
  - `README.md:84` — `# → 454 теста (41 файл), 3 skipped`
  - `README.md:114` — `tests/ 41 файл, 454 теста`
  - `README.md:137` — `**Тестов:** 454 (41 файл), 3 skipped`
  - `DEV_INDEX.md:120` — `41 файл, 454 теста`
  - `DEV_INDEX.md:161` — `# Тесты (454 шт.)`
  - `AGENTS.md:182` — `pytest tests/ -q — 454 теста, 41 файл, 3 skipped`
  - `CHANGELOG.md:32` — `454 passed, 3 skipped`
  - `docs/features/f4.9-generate-opponent.md:117` and `docs/features/f4.12-my-rosters.md:534` — stale full-suite counts.

Why it matters:

- The project explicitly uses docs as review/development guidance. Stale test counts make verification evidence ambiguous and can hide missing/new tests.

Recommendation:

- Update top-level current-state docs to `457 tests collected` or remove exact counts where they churn.
- Keep historical counts only in dated changelog entries where clearly framed as historical.

---

#### I2 — Wiki inventory counts are inconsistent with the repository

Evidence:

- Runtime/file verification: `wiki/**/*.md` count is `467`.
- Docs claim multiple different values:
  - `README.md:7`, `README.md:19`, `README.md:94`, `README.md:139` — `~490 .md`
  - `AGENTS.md:33` — `~490 .md`
  - `CHANGELOG.md:156` — `489 files`
  - `ROADMAP.md:23` — `~490 страниц`
  - `ROADMAP.html:119`, `ROADMAP.html:368` — `490 pages/files`
  - `docs/architecture/C4.md:25`, `docs/architecture/C4.md:62`, `docs/architecture/C4.md:256` — `~490 .md`
  - `DEV_INDEX.md:129` — `480 .md`

Additional verified inventory:

- `wiki/units`: 168 `.md` files; loader currently loads 160 units.
- `wiki/detachments`: 23 `.md` files.
- `wiki/enhancements`: 89 `.md` files.
- `wiki/stratagems`: 116 `.md` files.
- `wiki/rules`: 23 `.md` files.

Why it matters:

- This project is wiki-driven; stale inventory numbers make content coverage and loader expectations harder to verify.

Recommendation:

- Pick one wording for current docs, e.g. `467 wiki markdown files; 160 loadable units; 23 detachments`.
- Keep old `489` only inside historical changelog entries if explicitly historical.

---

#### I3 — C4 DB model documents tables that do not exist, while other docs under-document existing tables

Evidence:

- Actual DB tables from SQLite introspection: `users`, `rosters`, `scenarios`, `replays`, `sqlite_sequence`.
- `docs/architecture/C4.md` overstates DB schema:
  - `C4.md:26` — `users, rosters, scenarios, replays, subscriptions, payments`
  - `C4.md:72`, `C4.md:76`, `C4.md:77`, `C4.md:166-168` — `oauth_accounts`, `subscriptions`, `payments`
- Top-level docs understate DB schema:
  - `README.md:18` — `SQLite: users, rosters, replays` omits `scenarios`.
  - `DEV_INDEX.md:104` — `SQLite (users, rosters, replays)` omits `scenarios`.

Why it matters:

- CR-19 already found billing/subscription persistence is not implemented. C4 currently represents planned billing tables as if they exist, which can mislead future implementation and review work.

Recommendation:

- Split C4 DB model into `implemented tables` and `planned billing/OAuth tables`.
- Update README/DEV_INDEX to include `scenarios` if describing actual current schema.

---

#### I4 — Security/CSP docs claim production CSP is active, but code disables CSP middleware

Evidence:

- Current code: `main.py` has `CSPMiddleware` commented out/disabled.
- Runtime/browser probes in CR-20 showed no `Content-Security-Policy` header.
- Docs still claim active CSP/security header coverage:
  - `README.md:67` — `Security: CORS hardening + 6 security headers (CSP, HSTS, etc.)`
  - `docs/features/Features_index.md:117` — `CORS hardening + CSP security headers`
  - `docs/features/f5.4-cors-csp-security.md` describes CSP as implemented/accepted.
  - `ROADMAP.md` / `ROADMAP.html` production security entries imply the same production-ready state.

Why it matters:

- Security docs are not just historical; they are used for production readiness review. Claiming CSP is active when it is disabled creates a false security baseline.

Recommendation:

- Update current-state docs to say CSP middleware exists but is disabled pending frontend compatibility fixes, or re-enable/fix CSP in code and tests.

---

#### I5 — C4 still contains stale 6-phase Game Loop and old test baseline

Evidence:

- Current code verification:
  - `GamePhase` has 5 current phase members: Command, Movement, Shooting, Charge, Fight.
  - `backend/engine/scenario.py` uses `max_phases_per_round = 5`.
  - No current `MORALE` enum member.
- Stale docs:
  - `docs/architecture/C4.md:289` — `scenario.py ← Game Loop (6 фаз)`.
  - `docs/architecture/C4.md:367` — `tests/ ← ~30 файлов, ~340 тестов`.
  - Current collection is 457 tests, and top-level docs say 41 test files.

Why it matters:

- C4 is the architecture reference. It conflicts with the current 10th Edition 5-phase design and with the project's own current test baseline.

Recommendation:

- Update C4 line 289 to 5 phases and refresh the test baseline in the project tree section.

---

#### I6 — Older feature specs still describe removed 6-phase/Morale behavior as current implementation

Evidence from stale scan:

- `docs/features/f2.1-game-state.md` still includes `MORALE = "morale"`, Morale-to-Command transition text, and states `6 фазами`.
- `docs/features/f2.5-game-loop.md` still starts with `все 6 фаз реализованы`, includes `Command -> Movement -> Shooting -> Charge -> Fight -> Morale`, code samples with `GamePhase.MORALE`, and a `morale_phase()` section.
- `docs/features/f2.7-battle-shock-cp-stratagems.md` still has stale `phase="morale"` examples.

Why it matters:

- Feature specs are used as implementation references. These files contradict current 10th Edition behavior and newer docs that correctly say Battle-shock happens in Command Phase.

Recommendation:

- Update the feature specs to either:
  - describe the current 5-phase implementation, or
  - clearly label old 6-phase/Morale blocks as historical superseded design.

---

#### I7 — C4 and feature mapping mark completed work as pending/stale

Evidence:

- `docs/architecture/C4.md:381` marks `F1.13 Weapon Keywords Phase 2` as pending, while `docs/features/Features_index.md:28` marks it done and tests exist.
- `docs/architecture/C4.md:386` marks `F2.13 Cover & Terrain` as pending, while `Features_index.md:52` marks it done.
- `docs/architecture/C4.md:395` marks `F4.12 My Rosters` as pending, while `Features_index.md:100` marks it done and implementation exists.
- `docs/architecture/C4.md:367` still says `~30 files, ~340 tests`, showing this C4 section is stale as a whole.

Why it matters:

- The architecture map is currently not reliable for planning/review sequencing.

Recommendation:

- Refresh the C4 Feature Spec → Module Mapping section from `docs/features/Features_index.md` and live code, or remove duplicated status data from C4.

---

#### I8 — Documented paths include missing/stale implementation files

Evidence from scoped path scan:

- Missing/stale references include:
  - `CHANGELOG.md:82` — `docs/features/f2.14-primary-missions.md` (actual indexed file is `docs/features/f2.15-primary-missions.md`).
  - `docs/features/f1.10-pmf-chart.md:12-13` — `web/templates/partials/sim_chart.html`, `web/static/sim_chart.js` (current implementation uses PMF chart page/static names, not these files).
  - `docs/features/f1.9-api-simulate.md:13` — `backend/api/simulate.py` (current route lives under `web/routes/api.py`).
  - `docs/features/f2.17-secondary-missions.md:11` — `backend/state/secondary.py` (missing).
  - `docs/features/f4.1-faction-browser.md:10` — `web/templates/partials/faction_browser.html` (missing; current page is `web/templates/faction_browser.html`).
  - `docs/features/f4.10-leaflet-map.md:15-16` — `web/templates/partials/map_view.html`, `web/static/map_view.js` (missing/superseded).
  - `docs/features/f4.14-strategic-battlefield-map.md:40-43` — old `canvas_map`/`map_view` cleanup references are intentionally historical but should be clearly marked superseded.
  - `docs/features/f4.5-canvas-map.md:13-14` — old `canvas_map` files are missing/superseded.

Why it matters:

- Broken file references slow down future code changes and can send agents to implement against non-existent modules.

Recommendation:

- Update current specs to current paths.
- For superseded specs, add an explicit `Superseded by F4.14` notice at the top and avoid presenting missing files as current implementation targets.

---

### Suggestions

#### S1 — Progressive Disclosure docs still mention three modes in at least one roadmap location

Evidence:

- Current code and memory/feature docs: two modes only — Beginner and Expert.
- `ROADMAP.md` still has a line mentioning `Beginner / Intermediate / Expert`.

Recommendation:

- Normalize to Beginner/Expert everywhere.

---

#### S2 — Feature/spec totals are internally inconsistent

Evidence:

- `README.md` / `DEV_INDEX.md`: 62 feature specs.
- `AGENTS.md`: `Phase 1–7, 77 фич`.
- `ROADMAP.md`: `82 фичи` / `~82`.
- `docs/features/Features_index.md`: summary says `~78`.
- Actual `docs/features/*.md` count includes 65 markdown files, with 62 indexed feature specs plus index/gap docs.

Recommendation:

- Decide whether docs report:
  - indexed specs only,
  - roadmap feature rows,
  - or all markdown files under `docs/features/`.
- State the category explicitly to avoid comparing incompatible counts.

## Verification performed

### Test inventory

```bash
uv run python -m pytest --collect-only -q
# ...
# ========================= 457 tests collected in 1.37s =========================
```

### FastAPI route inventory

```bash
uv run python - <<'PY'
from fastapi.routing import APIRoute
from main import app
routes=[]
for r in app.routes:
    if isinstance(r, APIRoute):
        methods=','.join(sorted(m for m in r.methods if m not in {'HEAD','OPTIONS'}))
        routes.append((r.path,methods,r.name))
print('raw_routes', len(routes))
print('unique_path_method', len(set((p,m) for p,m,_ in routes)))
print('api_raw', sum(1 for p,_,_ in routes if p.startswith('/api')))
print('api_unique', len(set((p,m) for p,m,_ in routes if p.startswith('/api'))))
PY
```

Observed:

```text
raw_routes 53
unique_path_method 51
api_raw 29
api_unique 27
```

### Code facts used for doc comparison

```text
version_pyproject 0.7.7
max_phases_per_round = 5
has_morale_enum False
feature_docs f*.md count 62
wiki_all 467
tests_py 41
db_tables ['replays', 'rosters', 'scenarios', 'sqlite_sequence', 'users']
registry_units 160
registry_detachments 23
```

### Missing path scan

The scoped markdown backtick-path scan found 14 missing/stale path references across the reviewed docs/features set. Representative examples are listed in finding I8.

### Corruption scan

Checked scoped docs for common tool-corruption patterns:

- `^\s*\d+\|` line-number prefixes
- rows starting with `||`

Observed:

```text
corruption_count 0
```

### Codex independent review attempt

Attempted, but unavailable in environment:

```text
/usr/bin/bash: line 3: codex: command not found
```

### Independent subagent review

A separate `delegate_task` review independently confirmed the same main classes of findings:

- DB schema docs mismatch.
- CSP/security docs mismatch.
- Stale test counts.
- Stale wiki counts.
- Deployment/faction AI and C4 status drift.
- Progressive Disclosure mode inconsistency.
- Feature/spec total inconsistency.

## Recommended remediation order

1. Update top-level current-state docs first:
   - `README.md`
   - `DEV_INDEX.md`
   - `AGENTS.md`
   - `docs/architecture/C4.md`
2. Normalize live facts:
   - tests: `457 collected`
   - wiki: `467 markdown files`, `160 loadable units`, `23 detachments`
   - routes: `53 raw FastAPI routes`, `51 unique path/method`, `27 unique /api path/method`
   - phases: 5-phase 10th Edition loop.
3. Split implemented vs planned billing/OAuth persistence in C4.
4. Fix stale 6-phase/Morale feature specs or mark historical/superseded sections explicitly.
5. Update missing/stale path references in feature specs.
6. Re-run doc corruption scan and `git diff --check` after doc edits.
