---
title: "CR-05 — Database and persistence review"
status: request-changes
review_task: CR-05
date: 2026-05-09
source: ../../requirements/code-review/cr-05-database-and-persistence-review.md
---

# CR-05 — Database and persistence review

## Verdict

**REQUEST CHANGES / PERSISTENCE FIXES REQUIRED**

SQL injection scan is clean for reviewed backend/web code, and the simple SQLite wrapper is readable. However, `Database.migrate()` drops the `replays` table on every app startup, which is data loss. There are also important persistence risks around disabled foreign-key enforcement, no rollback abstraction, a global `check_same_thread=False` connection, replay ownership not persisted from API calls, and missing replay indexes.

## Scope reviewed

- `backend/db/database.py`
- DB usage in `web/routes/api_rosters.py`
- DB usage in `web/routes/api_replays.py`
- DB usage in `web/routes/auth.py`
- DB usage in `backend/auth/__init__.py`
- DB usage in `backend/auth/providers/routes.py`
- DB usage in `backend/engine/replay.py`
- `tests/test_rosters.py`
- `tests/test_generate_roster.py`
- `tests/test_replay.py`

## Tests / verification

Targeted tests run:

```text
uv run python -m pytest tests/test_rosters.py tests/test_generate_roster.py tests/test_replay.py -q
41 passed, 33 warnings in 6.09s
```

Static DB scan:

```text
SQL_CALLS 41
SQL_INTERPOLATION_RISKS []
SQL_CALLS_BY_FILE
web/routes/api_rosters.py 13
backend/db/database.py 10
backend/engine/replay.py 7
backend/auth/__init__.py 5
web/routes/api_replays.py 3
backend/auth/providers/routes.py 2
web/routes/pages.py 1
HAS_DROP_REPLAYS True
HAS_FOREIGN_KEYS_PRAGMA False
HAS_USER_ID_REPLAY_INDEX False
HAS_ROLLBACK_METHOD False
CHECK_SAME_THREAD_FALSE True
```

## Critical findings

### Critical 1 — `migrate()` drops the `replays` table on every startup

Evidence:

```text
backend/db/database.py:118-130
DROP TABLE IF EXISTS replays;
CREATE TABLE IF NOT EXISTS replays (...)
```

`main.py` calls `db.migrate()` during app creation:

```text
main.py:119-120
# DB init
db.migrate()
```

Impact:

- Every app startup destroys all saved replays.
- This contradicts replay/result persistence requirements.
- It can erase user-visible battle history in production.

Required fix:

- Remove `DROP TABLE IF EXISTS replays` from normal migration path.
- Implement additive migrations only.
- If replay schema changed, use `ALTER TABLE` / copy-forward migration guarded by schema version.
- Add regression test: create replay, call `db.migrate()`, replay still exists.

## Important findings

### Important 1 — SQLite foreign keys are defined but not enforced

Evidence:

- Schema declares foreign keys for `rosters.user_id` and `scenarios.user_id`.
- `connect()` sets `PRAGMA journal_mode=WAL`, but does not set `PRAGMA foreign_keys=ON`.

Impact:

- SQLite does not enforce foreign keys unless explicitly enabled per connection.
- Orphaned rosters/scenarios can exist if users are deleted or data is corrupted.

Required fix:

```python
self._conn.execute("PRAGMA foreign_keys=ON")
```

Add tests if user deletion/data cleanup is supported.

### Important 2 — No rollback method / transaction boundary abstraction

Evidence:

```text
backend/db/database.py
execute/fetch/commit helpers exist, no rollback helper/context manager
```

Impact:

- Multi-step writes can leave partial state if later steps fail after earlier commits.
- Route code commits manually and inconsistently.

Required fix:

- Add transaction context manager:
  ```python
  with db.transaction():
      ...
  ```
- Roll back on exception.
- Use it for multi-step operations such as OAuth account linking, replay save, and future billing updates.

### Important 3 — Global SQLite connection uses `check_same_thread=False`

Evidence:

```text
backend/db/database.py:23
sqlite3.connect(self.db_path, check_same_thread=False)
```

Impact:

- Allows one connection across FastAPI threads.
- SQLite can handle serialized writes, but the app wrapper has no explicit lock.
- Under concurrent requests, this can create write contention or subtle shared-connection behavior.

Required fix:

- Use per-request/per-thread connection or add a lock around writes.
- At minimum document concurrency constraints and add stress tests for concurrent roster creates/saves.

### Important 4 — Replay ownership column exists but API save path does not populate it

Evidence:

```text
backend/engine/replay.py:360
save_replay(db, replay, user_id: int | None = None)

web/routes/api_replays.py:435
save_replay(db.conn, replay)
```

Impact:

- `replays.user_id` remains `NULL` for API-created simulations.
- CR-04 owner filtering cannot work until `auto_play_simulation` passes current user id.

Required fix:

- Require/resolve current user for auto-play or explicitly define public anonymous simulations.
- Pass `user_id=user.id` when saving private replay.

### Important 5 — Missing indexes for replay owner and created_at queries

Evidence:

```text
CREATE TABLE IF NOT EXISTS replays (... user_id INTEGER)
```

Indexes present:

```text
idx_rosters_user
idx_rosters_faction
idx_scenarios_user
```

No replay indexes found.

Impact:

- `WHERE user_id = ? ORDER BY created_at DESC LIMIT ?` in `backend/engine/replay.py:list_replays` will scan as data grows.
- `/api/replays` orders by `created_at` without index.

Required fix:

- Add indexes:
  ```sql
  CREATE INDEX IF NOT EXISTS idx_replays_user_created ON replays(user_id, created_at DESC);
  CREATE INDEX IF NOT EXISTS idx_replays_created ON replays(created_at DESC);
  ```

### Important 6 — JSON parsing paths assume valid stored JSON and may 500 on corrupt data

Evidence examples:

```text
web/routes/api_rosters.py:136 json.loads(data["units"])
web/routes/api_replays.py:476 json.loads(r["summary"])
backend/engine/replay.py:328 json.loads(data)
```

Impact:

- Corrupt/manual DB rows can crash endpoints with 500.
- Not an injection issue, but a resilience issue.

Required fix:

- Validate JSON on write and handle parse errors on read with controlled 500/repair path.
- Add tests for corrupt roster units/replay summary rows if direct DB corruption is in scope.

## Suggestions

### Suggestion 1 — Add schema versioning

Current migration is a single `executescript` plus suppressed `ALTER TABLE`. Add a `schema_migrations` table or `PRAGMA user_version` to track applied changes.

### Suggestion 2 — Type DB row boundaries explicitly

Route functions frequently convert `sqlite3.Row` to dict ad hoc. A small persistence mapper for `RosterRow`, `ReplayRow`, `UserRow` would clarify JSON fields and ownership.

### Suggestion 3 — Avoid broad migration exception suppression

Evidence:

```text
with contextlib.suppress(Exception):
    self.execute("ALTER TABLE users ADD COLUMN tier TEXT DEFAULT 'free'")
```

Suppressing all exceptions hides unexpected migration failures. Catch the specific duplicate-column condition instead.

### Suggestion 4 — Add DB reset/test isolation helpers

Tests currently write through the app singleton. A documented test DB fixture would reduce cross-test state and make ownership tests more deterministic.

## Five-axis review notes

### Correctness

- Roster/user basic writes work in existing tests.
- Replay persistence is undermined by startup data loss due to `DROP TABLE`.

### Readability / simplicity

- The DB wrapper is small and easy to understand.
- Migration logic is too implicit for production because destructive schema operations live inside normal startup.

### Architecture

- Singleton DB is simple but risky for concurrent FastAPI workloads.
- Persistence schema and route ownership model are not fully aligned: replay `user_id` exists but is not populated/used.

### Security

- SQL calls reviewed show no interpolation risks.
- Foreign key enforcement and owner persistence gaps affect data integrity/security.

### Performance

- Missing replay indexes will become a bottleneck after real usage.
- Global shared connection may bottleneck concurrent writes.

## What is done well

- SQL queries in reviewed code are parameterized.
- Roster `units` and replay JSON are serialized with `json.dumps`, not eval/pickle.
- DB directory is created before connecting.
- WAL mode is attempted for better SQLite write behavior.

## Completion

- Completed at: `2026-05-09`
- Verdict: `REQUEST CHANGES / PERSISTENCE FIXES REQUIRED`
- Critical: `1`
- Important: `6`
- Suggestions: `4`
