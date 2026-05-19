---
title: "CR-18 — Pages/templates/navigation review"
parent: code-review
status: request-changes
source: ../code-review-plan.md#cr-18
tags: [requirements, code-review, atomic-review]
---

# CR-18 — Pages/templates/navigation review

**Objective:** проверить base navigation, pricing/auth pages, static assets, favicon, mode toggles.

**Files:**
- Review: `web/templates/`
- Review: `web/routes/pages.py`
- Review: `web/static/`
- Output: `docs/reviews/2026-05-10/CR-18-pages-templates-navigation-review.md`

**Steps:**
1. Проверить all page routes return 200 or expected auth redirect.
2. Проверить base.html includes required assets once.
3. Проверить no stale navigation links.
4. Проверить favicon/static files reachable.
5. Проверить Progressive Disclosure body classes and toggle behavior.
6. Проверить no Alpine template runtime errors in common pages.
7. Browser/curl smoke for key pages.

**Acceptance:** navigation and common templates do not break app shell.

---

---

## Execution Status

**Status:** Request Changes

**Review report target:** `docs/reviews/2026-05-10/CR-18-pages-templates-navigation-review.md`

### Status checklist

- [x] Scope confirmed
- [x] Requirements/specs reviewed
- [x] Tests reviewed first
- [x] Production code reviewed
- [x] Correctness checked
- [x] Readability checked
- [x] Architecture checked
- [x] Security checked
- [x] Performance checked
- [x] Verification commands executed
- [x] Findings report written
- [x] Triage status updated in `docs/requirements/code-review/code-review.md`

### Result

- **Verdict:** Request Changes — common routes/static assets load, but pricing CTA is broken, shared CSS helper classes do not apply under Tailwind CDN, Progressive Disclosure has a localStorage failure path, and tests miss these CR-18 contracts.
- **Critical:** 0
- **Important:** 4
- **Suggestions:** 1
- **Blocked by:** Codex CLI unavailable (`codex: command not found`); review completed with direct inspection, probes, browser smoke, and delegated independent reviewer.
- **Completed at:** 2026-05-10

## Triage summary

- [CR-18 triage entry](../../reviews/2026-05-10/triage-summary.md#cr-18)
- Current release triage verdict: not-release-ready until open Critical/Important findings are fixed/re-reviewed or explicitly accepted where allowed.

## Regression evidence — Task 6.2 (2026-05-19)

- Result page/replay summary surfaces tied to CR-18 were re-verified against runtime-id-based attribution and non-zero Player 2 charge card behavior.
- Re-check found the charge cards still used `actor_id.startsWith('player2')`; this is now replaced with `chargeCount(0/1)` backed by owner lookup through runtime IDs.
- No template/navigation regressions introduced while validating Task 6.2 replay/result summary paths.

Verification:
- `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_parse_log_events.py tests/test_result_screen.py tests/test_replay.py tests/test_round_viewer.py -q` → 61 passed, 0 failed.
- `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/ -q` → 633 passed, 3 skipped, 0 failed.
- `node -c web/static/result_chart.js` → passed.
- JS `chargeCount()` owner-lookup probe → `chargeCount OK`.

## Regression evidence — Task 6.1 (result page authoritative VP source)

Date: 2026-05-19

The result page consumes `/api/results/{game_id}` and `result_chart.js` uses `summary.final_victory_points` / `final_state.victory_points` for stat cards and the final chart point. The API now overwrites stale summary VP/winner metadata from authoritative `final_state`, so `/result/{game_id}` and `/api/results/{game_id}` share the same final VP source.

Verification: `tests/test_result_screen.py` included in focused suite (`66 passed`) and full suite (`630 passed, 3 skipped`).

## Regression evidence — Task 6.3 (2026-05-19)

- Final-gate smoke now includes `/result/{game_id}` page shell and result-chart VP wiring checks as a repeatable repo script.
- This replaces ad-hoc probes and protects CR-18-facing replay/result page integration from silent drift.

Verification:
- `rm -f *.db-shm *.db-wal && uv run python scripts/smoke_final_gate.py` → exit 0.
- `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_final_gate_smoke.py tests/test_result_screen.py tests/test_replay.py -q` → 46 passed, 0 failed.
- `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/ -q` → 633 passed, 3 skipped, 0 failed.
