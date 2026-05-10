---
title: "CR-00 — Inventory and baseline"
status: approved
review_task: CR-00
date: 2026-05-09
source: ../../requirements/code-review/cr-00-inventory-and-baseline.md
---

# CR-00 — Inventory and baseline

## Verdict

**APPROVE / BASELINE CAPTURED**

CR-00 completed successfully. The goal was not to approve production behavior, but to freeze the live project baseline before domain reviews CR-01–CR-24. The baseline is usable: branch, dirty workspace, file inventory, test collection count, lint/format status, JS syntax status, and route count are recorded.

## Executive summary

- Branch: `feat/0.7.7`
- Date: `2026-05-09`
- Git HEAD: `d381bac`
- Project: `warpsmith`
- Version: `0.7.7`
- Python requirement: `>=3.12`
- Dependency count from `pyproject.toml`: `17`
- FastAPI route count: `53` total routes
- API route-method count: `27` unique `/api` route+method entries
- API unique path count: `24`
- Pytest collect-only: `457 tests collected`
- Ruff check: passed
- Ruff format check: passed
- JS syntax check: passed for all `12` files in `web/static/*.js`

## Critical findings

None for CR-00.

## Important findings

None blocking for CR-00.

## Suggestions / risks to carry into later CR tasks

1. The workspace is heavily dirty: `486` modified tracked files before this review execution. Later CR tasks must treat `git status` as baseline context and avoid assuming every modified file was changed by the current review pass.
2. `.test-credentials` is modified. CR-00 did not read it to avoid exposing secrets. CR-02 must handle secrets scanning carefully and redact any credential values as `[REDACTED]`.
3. `wiki/` accounts for most modified files (`370`). CR-06 should separate wiki data-quality review from production-code review to avoid drowning code findings in content edits.
4. FastAPI registers duplicate detachment paths internally, already documented in `docs/api/endpoints.md`; CR-13 should decide whether route ownership should be consolidated.

## Scope inventory

### Files by extension/type

| Type | Count |
|---|---:|
| Markdown | 575 |
| Python | 98 |
| SVG | 24 |
| HTML | 20 |
| JavaScript | 12 |
| No extension | 10 |
| JSON | 7 |
| YAML | 4 |
| SQLite DB files | 5 |
| Text | 2 |
| TOML | 1 |
| Lock | 1 |
| CSS | 1 |
| Other singletons | 8 |
| **Total files scanned** | **767** |

### Selected directories

| Directory | Inventory |
|---|---|
| `backend/` | 43 Python files |
| `web/routes/` | 7 Python route files |
| `web/static/` | 12 JavaScript files, 24 SVG, 1 CSS |
| `web/templates/` | 19 HTML templates |
| `tests/` | 41 `test_*.py` files, 43 Python files total |
| `docs/` | 100 Markdown files |
| `wiki/` | 467 Markdown files |
| `scripts/` | 3 Python files |
| `.github/` | 2 YAML workflow files |

## Dirty workspace baseline

Command:

```bash
git status --short
```

Summary:

| Status code | Count |
|---|---:|
| ` M` | 486 |

Top-level distribution:

| Top-level path | Modified files |
|---|---:|
| `wiki/` | 370 |
| `tests/` | 34 |
| `backend/` | 26 |
| `web/` | 25 |
| `docs/` | 14 |
| `scripts/` | 3 |
| `.github/` | 2 |
| `.dockerignore` | 1 |
| `.env.example` | 1 |
| `.gitignore` | 1 |
| `.test-credentials` | 1 |
| `Dockerfile` | 1 |
| `backups/` | 1 |
| `docker-compose.yml` | 1 |
| `main.py` | 1 |
| `pyproject.toml` | 1 |
| `railway.json` | 1 |
| `requirements.txt` | 1 |
| `uv.lock` | 1 |

Security note: `.test-credentials` was observed as modified by path only. Its contents were not read or printed.

## Verification commands and results

### Branch and status

```bash
date +%F && git branch --show-current && git status --short
```

Result:

- Date: `2026-05-09`
- Branch: `feat/0.7.7`
- Modified tracked files: `486`

### File inventory

```bash
python3 - <<'PY'
from pathlib import Path
from collections import Counter, defaultdict
# counted files by suffix and top-level directory, excluding .git/.venv/cache dirs
PY
```

Result: inventory tables above.

### Pytest collect-only

```bash
uv run python -m pytest --collect-only -q
```

Result:

```text
457 tests collected in 1.43s
```

No test execution was required for CR-00; this task captures collection baseline only. Full regression remains for CR-24 or targeted domain CR tasks.

### Ruff lint

```bash
uv run ruff check .
```

Result:

```text
All checks passed!
```

### Ruff format check

```bash
uv run ruff format --check .
```

Result:

```text
98 files already formatted
```

### JavaScript syntax

```bash
node -c web/static/*.js
```

Executed file-by-file for all JS files under `web/static/`.

Result:

| File | Status |
|---|---|
| `web/static/battlefield_map.js` | OK |
| `web/static/detachment_picker.js` | OK |
| `web/static/faction_browser.js` | OK |
| `web/static/my_rosters.js` | OK |
| `web/static/progressive_disclosure.js` | OK |
| `web/static/replay_viewer.js` | OK |
| `web/static/result_chart.js` | OK |
| `web/static/scenario_setup.js` | OK |
| `web/static/synergy_hints.js` | OK |
| `web/static/team_builder.js` | OK |
| `web/static/tooltips.js` | OK |
| `web/static/unit_modal.js` | OK |

Summary: `12/12` passed.

### FastAPI route inventory

```bash
python3 - <<'PY'
from fastapi.routing import APIRoute
from main import app
# count total routes and /api route-method entries
PY
```

Result:

```text
FASTAPI_ROUTES 53
UNIQUE_API_ROUTE_METHODS 27
UNIQUE_API_PATHS 24
```

Runtime warning observed during import:

```text
SENTRY_DSN not set — Sentry disabled
```

This is expected in local baseline when Sentry is not configured.

## Five-axis baseline notes

### Correctness

- Test discovery works: `457` tests collect successfully.
- Lint and format gates pass.
- JS syntax gate passes for all static JS files.

### Readability / simplicity

- Project is large enough that monolithic review is not appropriate.
- Atomized CR package is required and already exists under `docs/requirements/code-review/`.

### Architecture

- Route surface is split across `web/routes/api.py`, `api_rosters.py`, `api_replays.py`, `api_detachments.py`, plus auth/billing routers.
- API inventory confirms `53` FastAPI routes and `27` unique `/api` route-method entries.

### Security

- No secrets were read.
- `.test-credentials` is modified and must be handled only by redacted scanning in CR-02.
- Auth/security-specific review remains for CR-02, CR-03, CR-04, CR-19, and CR-20.

### Performance

- CR-00 did not profile runtime paths.
- Inventory identifies likely performance review targets: wiki loader/parser, API list endpoints, autoplay/replay pipeline, and frontend map rendering.

## What is done well

- The project has a clear test baseline and all static gates used by CR-00 pass.
- The code review workload has already been decomposed into atomic artifacts, preventing a monolithic review.
- API documentation now has a Swagger-backed endpoint index, useful for CR-13.

## Verification story

Commands executed and persisted in this report:

- `date +%F`
- `git branch --show-current`
- `git status --short`
- Python file inventory script
- `uv run python -m pytest --collect-only -q`
- `uv run ruff check .`
- `uv run ruff format --check .`
- `node -c` for all `web/static/*.js`
- FastAPI route inventory script via `main:app`

## Completion

- Completed at: `2026-05-09`
- Verdict: `APPROVE / BASELINE CAPTURED`
- Critical: `0`
- Important: `0`
- Suggestions: `4`
