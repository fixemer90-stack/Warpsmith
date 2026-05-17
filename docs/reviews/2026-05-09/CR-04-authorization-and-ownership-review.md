---
title: "CR-04 — Authorization and ownership review"
status: request-changes
review_task: CR-04
date: 2026-05-09
source: ../../requirements/code-review/cr-04-authorization-and-ownership-review.md
---

# CR-04 — Authorization and ownership review

## Verdict

**REQUEST CHANGES / OWNERSHIP BYPASS FIXES REQUIRED**

Roster CRUD ownership checks are mostly correct for private/public rosters, but simulation/replay endpoints bypass ownership entirely. An unauthenticated caller can run `/api/auto-play` using private roster IDs and then read/list resulting replays publicly. This is an IDOR/data exposure class issue and must be fixed before production.

## Scope reviewed

- `web/routes/api_rosters.py`
- `web/routes/api_replays.py`
- `backend/engine/replay.py`
- `backend/billing/webhooks.py`
- `backend/db/database.py`
- `tests/test_rosters.py`
- `tests/test_replay.py`

## Tests / verification

Targeted tests run:

```text
uv run python -m pytest tests/test_rosters.py tests/test_replay.py -q
33 passed, 33 warnings in 6.18s
```

Broader related test run:

```text
uv run python -m pytest tests/test_rosters.py tests/test_generate_roster.py tests/test_replay.py -q
41 passed, 33 warnings in 6.09s
```

Manual owner-isolation smoke test with two users:

```text
CREATE_PRIVATE 200
OTHER_GET_PRIVATE 403
OTHER_PUT_PRIVATE 403
OTHER_DELETE_PRIVATE 403
OTHER_DUP_PRIVATE 404
OTHER_GET_PUBLIC 200
OTHER_DUP_PUBLIC 200
OTHER_PUT_PUBLIC 403
OTHER_DELETE_PUBLIC 403
UNAUTH_AUTOPLAY_PRIVATE_IDS 200
REPLAYS_LIST_UNAUTH 200
```

## Critical findings

### Critical 1 — `/api/auto-play` is unauthenticated and can use private roster IDs

Evidence:

```text
web/routes/api_replays.py:310-318
@router.post("/auto-play")
async def auto_play_simulation(roster_a_id: int, roster_b_id: int, ...):
```

No `Depends(get_current_user)` or owner/public authorization is applied.

DB load:

```text
web/routes/api_replays.py:327-328
roster_a_row = db.fetchone("SELECT * FROM rosters WHERE id = ?", (roster_a_id,))
roster_b_row = db.fetchone("SELECT * FROM rosters WHERE id = ?", (roster_b_id,))
```

Runtime evidence:

```text
UNAUTH_AUTOPLAY_PRIVATE_IDS 200
```

Impact:

- Any caller who guesses/knows roster IDs can simulate using private rosters.
- The replay stores roster names/factions and derived game output, making private data observable via replay endpoints.
- This bypasses the ownership checks that `GET /api/rosters/{id}` correctly enforces.

Required fix:

- Require auth for `/api/auto-play` when using stored roster IDs.
- Enforce each roster is either owned by current user or explicitly public.
- Save replay with `user_id=user.id`.
- Add tests: unauthenticated auto-play denied; other user's private roster denied; public opponent allowed.

### Critical 2 — Replay/result endpoints expose all replays without owner filtering

Evidence:

```text
web/routes/api_replays.py:452-458
GET /replays/{game_id} -> load_replay(db.conn, game_id)

web/routes/api_replays.py:461-479
GET /replays -> SELECT ... FROM replays ORDER BY created_at DESC

web/routes/api_replays.py:485-503
GET /results/{game_id} -> load_replay(db.conn, game_id)
```

No auth dependency and no `user_id` filter.

Runtime evidence:

```text
REPLAYS_LIST_UNAUTH 200
```

Impact:

- All replay metadata is public by default.
- Any replay can be fetched by `game_id` regardless of owner.
- Since `/api/auto-play` saves replay output from private rosters, this compounds Critical 1.

Required fix:

- Define replay visibility contract: private by default, public only if explicitly shared.
- Add `user_id` filtering to list/load result endpoints.
- For public result sharing, add a separate explicit share token/public flag.
- Add owner-isolation tests for list/get/result.

## Important findings

### Important 1 — Roster owner isolation works in manual smoke test but lacks explicit cross-user regression tests

Evidence from smoke test:

```text
OTHER_GET_PRIVATE 403
OTHER_PUT_PRIVATE 403
OTHER_DELETE_PRIVATE 403
OTHER_DUP_PRIVATE 404
OTHER_GET_PUBLIC 200
OTHER_DUP_PUBLIC 200
OTHER_PUT_PUBLIC 403
OTHER_DELETE_PUBLIC 403
```

Existing `tests/test_rosters.py` tests own CRUD and unauthenticated post, but does not explicitly create two users and assert cross-owner denial.

Required fix:

- Add tests for private roster access/update/delete/duplicate by another authenticated user.
- Add tests for public roster read/duplicate semantics.

### Important 2 — `GET /api/rosters?public_only=true` requires auth despite being public-only

Evidence:

```text
web/routes/api_rosters.py:140-145
async def list_rosters(user: User = Depends(get_current_user), public_only: bool = False):
    if public_only:
        rows = db.fetchall("SELECT * FROM rosters WHERE is_public = 1 ...")
```

Because `get_current_user` is always required, unauthenticated users cannot list public rosters through this route.

Impact:

- This is not an ownership vulnerability, but it is inconsistent API design.
- If public rosters are intended discoverable, route should use optional auth or a separate public endpoint.

Required fix:

- Decide public contract.
- Either document auth-required public listing, or change to optional auth and test it.

### Important 3 — Billing/subscription endpoints lack owner/auth enforcement but are stubs

Evidence:

```text
backend/billing/webhooks.py
POST /api/subscribe
GET /api/billing/portal
```

No auth dependency yet. Current implementation is a redirect stub, so immediate impact is limited, but it must not ship as production subscription management.

Required fix:

- Require current user for subscribe/portal.
- Tie Stripe customer/subscription records to `user_id`.
- Verify webhook signature and update only matching users.

## Suggestions

### Suggestion 1 — Normalize error semantics for private resources

`GET` other private roster returns `403`, while duplicate private roster returns `404`. Either is defensible, but choose and document a consistent pattern for resource existence privacy.

### Suggestion 2 — Add explicit ownership helpers

Repeated owner/public logic appears in route functions. Consider helper functions:

- `get_owned_roster_or_404(roster_id, user)`
- `get_readable_roster_or_404(roster_id, user)`
- `assert_owned_roster(roster_id, user)`

This reduces future endpoint drift.

### Suggestion 3 — Add route-level authorization matrix docs

For each API route, document:

- unauthenticated
- authenticated owner
- authenticated non-owner
- public resource allowed/denied

This should be part of CR-13 and final docs sync.

## Five-axis review notes

### Correctness

- Roster CRUD mostly behaves as intended for owner/private/public semantics.
- Simulation/replay path is not aligned with ownership model.

### Readability / simplicity

- Roster route ownership checks are straightforward.
- Replay routes are simple but too permissive.

### Architecture

- Ownership enforcement is endpoint-local rather than centralized.
- Replay persistence has `user_id`, but it is not used by `auto_play_simulation` or API replay readers.

### Security

- Critical IDOR exists via `/api/auto-play` and replay/result routes.
- Roster CRUD itself is much safer than replay routes.

### Performance

- No performance blocker found in authorization checks.
- Adding indexed `replays.user_id` filtering would improve scalability; see CR-05.

## What is done well

- Private roster get/update/delete by another authenticated user is denied in smoke test.
- Public roster read and duplicate are allowed while update/delete remain owner-only.
- SQL queries use parameters.
- Duplicate of public roster becomes private copy owned by requester.

## Completion

- Completed at: `2026-05-09`
- Verdict: `REQUEST CHANGES / OWNERSHIP BYPASS FIXES REQUIRED`
- Critical: `2`
- Important: `3`
- Suggestions: `3`
