# Task 6.2 Check — event parsing and summary attribution

Task: `docs/remediation/task-06-02-fix-event-parsing-and-summary-attribution.md`
Date: 2026-05-19
Reviewer: Hermes

## Verdict

APPROVED AFTER FIXES 2026-05-19.

## Findings

### Fixed during review

1. **Important — actual VP logs with totals/Battle Ready wording parsed as `info`.**
   - Probe: `_parse_log_events(["orks roster gained 3 VP (total: 3)", "tau roster gains 10 Battle Ready VP (total: 10)"])` returned `info` events.
   - Fix: broadened the VP parser in `web/routes/api_replays.py` to accept `gained`/`gains`, optional `Battle Ready`, and optional `(total: N)` suffix.
   - Regression: `tests/test_parse_log_events.py::test_parses_vp_logs_with_totals_and_battle_ready_wording`.

2. **Important — result charge cards still used `actor_id.startsWith('player2')`.**
   - Problem: runtime IDs are `p1:...` / `p2:...`, so Player 2 normal charge events could show as zero or be misattributed.
   - Fix: added `chargeCount(index)` in `web/static/result_chart.js`, backed by `_actorPlayerId()` owner lookup, and changed `web/templates/result.html` to use `chargeCount(0)` / `chargeCount(1)`.
   - Hardening: `_actorPlayerId()` now checks explicit `runtime_unit_id` / `display_name` fields as well as legacy `id` / `name`.
   - Regression: `tests/test_result_screen.py::test_result_page_charge_cards_use_owner_lookup_not_player2_prefix` plus JS owner-lookup probe.

No remaining blockers found after fixes.

## Verification

```bash
rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_parse_log_events.py tests/test_result_screen.py tests/test_replay.py tests/test_round_viewer.py -q
# 61 passed, 0 failed

rm -f *.db-shm *.db-wal && uv run python -m pytest tests/ -q
# 633 passed, 3 skipped, 0 failed

node -c web/static/result_chart.js
# passed

node - <<'NODE'
# chargeCount owner lookup probe
NODE
# chargeCount OK

uv run ruff check .
# All checks passed!

uv run ruff format --check .
# 108 files already formatted
```

## Resolution

- [x] VP parser handles actual Command/Battle Ready log strings with totals.
- [x] Result charge cards use owner lookup instead of string-prefix heuristics.
- [x] Task file verification commands and counts updated to the re-run evidence.
