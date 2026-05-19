# Task 6.3 Check — repeatable final gate smoke script

Task: `docs/remediation/task-06-03-add-repeatable-final-gate-smoke-script.md`
Date: 2026-05-19
Reviewer: Hermes

## Verdict

APPROVED 2026-05-19.

## Findings

No blockers found.

Implemented and verified:
- `scripts/smoke_final_gate.py` creates isolated temporary DB via `DB_PATH`, seeds deterministic rosters, runs `/api/auto-play` with fixed seed, and validates VP parity across runtime/replay/results surfaces.
- Smoke checks include `/result/{game_id}` shell + result chart wiring hooks (`final_victory_points` usage), replacing ad-hoc `/tmp` probes with repo-owned executable gate.
- Regression test `tests/test_final_gate_smoke.py` executes the smoke script as a subprocess and asserts success.

## Verification

```bash
rm -f *.db-shm *.db-wal && uv run python scripts/smoke_final_gate.py
# exit 0

rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_final_gate_smoke.py tests/test_result_screen.py tests/test_replay.py -q
# 46 passed, 0 failed

rm -f *.db-shm *.db-wal && uv run python -m pytest tests/ -q
# 633 passed, 3 skipped, 0 failed

uv run ruff check scripts/smoke_final_gate.py tests/test_final_gate_smoke.py
# All checks passed

uv run ruff format --check scripts/smoke_final_gate.py tests/test_final_gate_smoke.py
# 2 files already formatted
```