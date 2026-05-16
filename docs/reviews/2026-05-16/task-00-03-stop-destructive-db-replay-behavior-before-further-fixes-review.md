---
title: "Code Review — Task 0.3 stop destructive DB/replay behavior"
date: 2026-05-16
reviewer: Hermes
verdict: request-changes
task: ../remediation/task-00-03-stop-destructive-db-replay-behavior-before-further-fixes.md
---

# Code Review — Task 0.3 stop destructive DB/replay behavior

Verdict: **REQUEST CHANGES**

Scope reviewed:
- `backend/db/database.py`
- `backend/engine/replay.py`
- `backend/engine/ai/autoplay.py`
- `web/routes/api_replays.py`
- `tests/test_replay.py`
- `docs/remediation/task-00-03-stop-destructive-db-replay-behavior-before-further-fixes.md`
- affected CR/triage docs touched by the implementation

## Summary

The core runtime fixes are directionally correct: `Database.migrate()` no longer drops the `replays` table, `save_replay()` defaults to plain `INSERT`, explicit overwrite requires `overwrite=True`, and autoplay `game_id` is UUID-based instead of seed-based.

However the task cannot be accepted yet because a completion gate fails and one required regression test does not actually exercise the product behavior it claims to cover.

## Findings

### Important 1 — `git diff --check` fails for touched file `web/routes/api_replays.py`

The task artifact marks `git diff --check` as complete, but the actual check fails:

```text
$ git diff --check -- backend/db/database.py backend/engine/replay.py backend/engine/ai/autoplay.py web/routes/api_replays.py tests/test_replay.py docs/remediation/task-00-03-stop-destructive-db-replay-behavior-before-further-fixes.md
web/routes/api_replays.py:1: trailing whitespace.
+"""Replay & Auto-play API — full game simulation, replay storage, result viewer."""\r
...
exit 2
```

This appears to be a line-ending/CRLF issue in a touched file, but it is still a failing repository quality gate and contradicts the task completion requirement.

Required fix: normalize the touched file or otherwise make `git diff --check -- ...` pass for the task diff before marking the task complete.

### Important 2 — Fixed-seed/distinct-replay-id regression test does not exercise autoplay or save behavior

Acceptance requires:

> Fixed seed produces repeatable simulation behavior but distinct durable replay ids across separate save attempts unless `replay_id` is explicitly provided.

The added test `tests/test_replay.py::test_same_seed_produces_different_replay_ids` only creates two local UUID strings:

```python
id1 = f"auto_{_uuid.uuid4().hex[:12]}"
id2 = f"auto_{_uuid.uuid4().hex[:12]}"
assert id1 != id2
```

It does not call `run_auto_game()`, does not verify two fixed-seed simulations, does not save durable replays, and does not prove repeatable simulation behavior. A broken implementation could keep using `f"auto_{seed}"` in production while this test still passes.

Required fix: add a product-level regression test/probe that calls the actual autoplay path with the same seed twice and verifies:
- simulation behavior remains repeatable for the deterministic parts under the same seed;
- generated durable `game_id` values are distinct;
- `Replay.seed` / DB metadata stores the provided seed separately;
- duplicate explicit `game_id` still fails unless `overwrite=True` is used.

### Suggestion 1 — Phase checkpoint docs say `code-review.md` was updated, but the index was not changed

The task completion checklist says the phase checkpoint should update `docs/requirements/code-review/code-review.md`. The diff updates CR-05, CR-14, and `docs/reviews/2026-05-10/triage-summary.md`, but no diff was present for `docs/requirements/code-review/code-review.md`.

If the index counts/status are intentionally unchanged, note that explicitly in the task artifact. Otherwise update the index to keep remediation/CR documentation synchronized.

## Positive checks

Confirmed in code review:
- `backend/db/database.py:migrate()` no longer contains `DROP TABLE IF EXISTS replays`.
- `backend/engine/replay.py:save_replay()` uses `INSERT INTO replays` by default and `INSERT OR REPLACE` only with `overwrite=True`.
- `backend/engine/ai/autoplay.py` creates `GameState.game_id` from UUID instead of seed.
- `/api/auto-play` persists the replay with the generated `result.game_state.game_id` and stores `seed` as replay metadata.

## Verification run

Passed:

```text
rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_replay.py -q
32 passed, 12 warnings

uv run ruff check backend/db/database.py backend/engine/replay.py backend/engine/ai/autoplay.py web/routes/api_replays.py tests/test_replay.py
All checks passed!

uv run ruff format --check backend/db/database.py backend/engine/replay.py backend/engine/ai/autoplay.py web/routes/api_replays.py tests/test_replay.py
5 files already formatted
```

Failed:

```text
git diff --check -- backend/db/database.py backend/engine/replay.py backend/engine/ai/autoplay.py web/routes/api_replays.py tests/test_replay.py docs/remediation/task-00-03-stop-destructive-db-replay-behavior-before-further-fixes.md
web/routes/api_replays.py:1: trailing whitespace.
...
exit 2
```

## Verdict

Request changes. The destructive replay deletion/overwrite implementation is mostly correct, but acceptance should wait until the failing diff gate is fixed and the fixed-seed replay-id test proves the real autoplay/save path rather than local UUID generation.
