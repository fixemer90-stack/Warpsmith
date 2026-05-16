---
title: "CR-05 — Database and persistence review"
parent: code-review
status: request-changes
source: ../code-review-plan.md#cr-05
tags: [requirements, code-review, atomic-review]
---

# CR-05 — Database and persistence review

**Objective:** проверить schema, migrations/init, JSON parsing, SQLite concurrency assumptions.

**Files:**
- Review: `backend/db/database.py`
- Review: DB usage in `web/routes/*.py`
- Review: tests touching rosters/replays/users
- Output: `docs/reviews/YYYY-MM-DD/CR-05-database-persistence.md`

**Steps:**
1. Проверить `connect()` и DB path creation.
2. Проверить parameterized SQL везде.
3. Проверить JSON columns parse/dump boundaries.
4. Проверить transaction/commit/rollback behavior.
5. Проверить SQLite WAL/shm cleanup assumptions in tests.
6. Проверить schema backward compatibility.
7. Запустить DB-related tests.

**Acceptance:** DB layer не содержит SQL injection, data loss, JSON string/list mismatch или ownership bypass.

---

---

## Execution Status

**Status:** Request Changes

**Review report:** `docs/reviews/2026-05-09/CR-05-database-and-persistence-review.md`

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

- **Verdict:** REQUEST CHANGES / PERSISTENCE FIXES REQUIRED
- **Critical:** 1
- **Important:** 6
- **Suggestions:** 4
- **Blocked by:** —
- **Report:** `docs/reviews/2026-05-09/CR-05-database-and-persistence-review.md`
- **Completed at:** 2026-05-09

## Triage summary

- [CR-05 triage entry](../../reviews/2026-05-10/triage-summary.md#cr-05)
- Current release triage verdict: not-release-ready until open Critical/Important findings are fixed/re-reviewed or explicitly accepted where allowed.

## Regression evidence — Task 0.1 (runtime unit identity)

**2026-05-16.** `RosterState.units` type changed from `dict[str, Unit]` to `list[tuple[str, Unit]]`
to support duplicate unit entries in a single roster (CR-12 roster-duplicate finding).
Persistence boundaries (`units_from_db` in `api_replays.py`) updated accordingly.
Database schema unchanged — runtime IDs are generated at conversion time.

Verification: `uv run python -m pytest tests/ -q` → 471 passed, 3 skipped, 0 failures.

## Regression evidence — Task 0.2 (canonical GameState serializer)

**2026-05-16.** Canonical `snapshot_game_state()` added to `backend/state/game_state.py`.
No schema changes; database boundaries unchanged. Persistence consumers (`replay.py`,
`autoplay.py`) now delegate to single canonical serializer. 478 tests pass.
