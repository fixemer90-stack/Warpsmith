---
title: "CR-19 — Billing, feature gate and subscription review"
status: request-changes
date: 2026-05-10
review: CR-19
scope:
  - backend/billing/
  - backend/auth/
  - web/routes/auth.py
  - web/routes/api_rosters.py
  - web/routes/api_replays.py
  - web/templates/pricing.html
  - billing/feature-gate related tests
verdict: request-changes
critical: 3
important: 8
suggestions: 1
---

# CR-19 — Billing, feature gate and subscription review

## Verdict

Request Changes.

Subscription and feature-gate boundaries are not safe enough for commercialization. The active billing endpoints are stubs, the Stripe webhook accepts unsigned events and performs no subscription state transition, several feature gates are bypassable by direct API calls, and the highest-cost simulation route is unauthenticated/ungated.

## Summary

- Critical: 3
- Important: 8
- Suggestions: 1
- Source-code changes made by this review: none
- Review/tracker docs updated: yes

## Scope reviewed

- `backend/billing/plans.py`
- `backend/billing/webhooks.py`
- `backend/billing/stripe_stub.py`
- `backend/auth/__init__.py`
- `backend/db/database.py`
- `web/routes/auth.py`
- `web/routes/api_rosters.py`
- `web/routes/api_replays.py`
- `web/templates/pricing.html`
- `web/templates/base.html`
- related docs/specs: `docs/features/f6.7-premium-trial.md`, `docs/features/f4.12-my-rosters.md`, `docs/architecture/ADR.md`, `docs/requirements/UX.md`
- focused tests around auth/rosters/rate limits

## Findings

### CR-19-C1 — Critical — Stripe webhook accepts unsigned events and does not update subscription state

Evidence:
- `backend/billing/webhooks.py:9-20`
- Runtime probe: `POST /api/webhooks/stripe` with arbitrary JSON returned `200 {"status":"ok","mode":"stub"}`.

Problem:
The webhook route is live but has only TODO comments for signature validation and event handling. It accepts arbitrary POST bodies, does not validate `Stripe-Signature`, and does not persist upgrade/downgrade state.

Impact:
This cannot be used as a production billing boundary. If later code starts trusting webhook payloads without signature verification, this becomes a trivial subscription escalation path. In its current form, legitimate Stripe events also cannot upgrade/downgrade users.

Recommendation:
Fail closed until billing is configured. Require Stripe signature verification before parsing event data, handle `checkout.session.completed` and `customer.subscription.deleted`, and add tests for unsigned, malformed, valid upgrade, valid downgrade, replay/idempotency cases.

### CR-19-C2 — Critical — Checkout/portal endpoints are stubs not bound to authenticated users

Evidence:
- `backend/billing/webhooks.py:23-33`: `/api/subscribe` has no `Depends(get_current_user)` and only redirects to `/pricing`.
- `backend/billing/webhooks.py:42-46`: `/api/billing/portal` has no auth and redirects to `/account/billing`.
- `web/templates/pricing.html:55-58`: Premium CTA points at `/api/subscribe`.
- Runtime probe: unauthenticated `POST /api/subscribe` returned `302 /pricing`; `GET /api/billing/portal` returned `302 /account/billing`.

Problem:
There is no authenticated checkout session creation, no `client_reference_id`, no customer/subscription linkage, no portal session creation, and no way for a paying user to become Premium through the app.

Impact:
The subscription model is functionally incomplete. Users cannot reliably upgrade, and the app has no trusted payment-to-user mapping.

Recommendation:
Make subscribe/portal authenticated, create real Stripe checkout/portal sessions with user IDs/customer IDs, persist subscription metadata, and return/redirect to the provider session URL. Keep stubs local-only or behind explicit test settings.

### CR-19-C3 — Critical — Full AI auto-play simulation is unauthenticated and ungated

Evidence:
- `backend/billing/plans.py:16,22,28,34` defines basic/full simulation and daily simulation limits.
- `web/routes/api_replays.py:310-318` defines `/api/auto-play` without an auth dependency.
- `web/routes/api_replays.py:327-328` loads rosters by raw ID only.
- `web/routes/api_replays.py:399-435` runs full simulation and persists replay without tier/quota checks.

Problem:
The highest-cost simulation path does not require login, does not check Free/Premium tier, does not enforce `max_simulations_per_day`, and does not check roster ownership/public visibility.

Impact:
Free/Premium simulation limits are bypassable by direct API calls. Any caller who knows roster IDs can run simulations with private rosters and generate replay records.

Recommendation:
Require auth on `/api/auto-play`, enforce ownership/public visibility for both rosters, record simulation usage, enforce quota for Free users, and differentiate basic/full AI by feature flags.

### CR-19-I1 — Important — Free roster limit is bypassable through duplicate endpoint

Evidence:
- `web/routes/api_rosters.py:89-95` checks `features["max_rosters"]` only in `create_roster`.
- `web/routes/api_rosters.py:337-350` duplicates a roster and inserts directly without checking limits.
- Runtime probe: a forced Free user reached 3 rosters, the fourth create returned 403, but `POST /api/rosters/{id}/duplicate` still returned 200 and created a fourth roster.

Problem:
The limit is enforced only on create, not on duplicate.

Impact:
Free users can exceed their roster cap with a simple API call.

Recommendation:
Apply the same limit check to every endpoint that creates a roster, including duplicate and future import endpoints.

### CR-19-I2 — Important — Free plan limit is inconsistent with product requirement and UI

Evidence:
- User/product model: Free = ads + 1 roster.
- `web/templates/pricing.html:15-17` advertises `1 saved roster`.
- `web/templates/my_rosters.html:13-18` shows `Free tier: rosters.length/1 roster`.
- `backend/billing/plans.py:14-15` sets `FREE["max_rosters"] = 3`.
- Runtime probe: forced Free user successfully created three rosters; fourth returned 403.

Problem:
Backend allows three rosters while UI/product copy says one.

Impact:
The monetization boundary is weaker than advertised and tests/specs become ambiguous.

Recommendation:
Use a single source of truth for plan limits and align backend, UI, docs, and tests. If the intended Free tier is 1 roster, set `max_rosters` to 1 and add regression tests.

### CR-19-I3 — Important — Free users can create public rosters despite `public_rosters_create=False`

Evidence:
- `backend/billing/plans.py:18` sets Free `public_rosters_create` to false.
- `web/routes/api_rosters.py:114-125` stores `is_public=int(data.is_public)` directly.
- Runtime probe: forced Free user created a roster with `is_public=True`; database row had `is_public=1`.

Problem:
The feature flag exists but is not enforced.

Impact:
Premium-only public roster creation is bypassable by direct API call.

Recommendation:
Reject `is_public=True` unless `features["public_rosters_create"]` is true, and add tests for create/update/duplicate/public transitions.

### CR-19-I4 — Important — `/api/me` does not expose feature flags or trial state

Evidence:
- `web/routes/auth.py:136-141` returns `user.to_dict()` only.
- `backend/auth/__init__.py:104-110` includes `id`, `email`, `display_name`, `tier` only.
- `web/templates/base.html` and UX docs expect client-visible `user.features` for ads/export/gates.
- Runtime probe: `/api/me` returned only `{id,email,display_name,tier}`.
- `docs/features/f6.7-premium-trial.md:106-119` expects `trial_ends_at` in API response.

Problem:
The backend has `UserFeatures`, but clients cannot consume the effective features or trial state from `/api/me`.

Impact:
Frontend cannot reliably hide ads, show Premium/trial state, disable Premium-only actions, or display accurate limits.

Recommendation:
Return `features: UserFeatures.for_user(user)` and `trial_ends_at`/effective tier from `/api/me`, with tests for anonymous, Free, Premium, active trial, and expired trial.

### CR-19-I5 — Important — `require_tier()` is an unimplemented placeholder

Evidence:
- `backend/billing/plans.py:55-61` returns a checker with `user=...` and `...` body.

Problem:
The intended FastAPI dependency for Premium-only routes is not usable.

Impact:
Future code may believe it has a central tier guard while the helper does not enforce anything. Current premium-only enforcement is therefore fragmented and easy to miss.

Recommendation:
Implement a real dependency factory that depends on `get_current_user`, resolves effective features, and raises 402/403 for insufficient tier. Add direct unit tests.

### CR-19-I6 — Important — Downgrade/subscription persistence semantics are absent

Evidence:
- `backend/db/database.py` has `users.tier`, but no customer/subscription IDs, subscription status, expiry, or webhook idempotency table.
- `backend/billing/webhooks.py:11-20` lists `customer.subscription.deleted` as a TODO but does not process it.
- `docs/architecture/ADR.md` describes subscription tables and downgrade flows that are not implemented.

Problem:
There is no durable model for payment provider state or downgrade events.

Impact:
Canceled subscriptions cannot reliably downgrade users; duplicate/out-of-order webhook delivery cannot be handled safely.

Recommendation:
Add subscription/customer fields or a subscriptions table, idempotency by event ID, and explicit transition tests for active, past_due, canceled, and deleted subscriptions.

### CR-19-I7 — Important — Roster limit check is non-atomic and race-prone

Evidence:
- `web/routes/api_rosters.py:91-95` counts existing rosters.
- `web/routes/api_rosters.py:114-127` inserts afterward in a separate operation.

Problem:
Two concurrent requests can both observe room below the limit and both insert.

Impact:
Even after aligning the limit to 1, concurrent Free-tier creates can exceed the cap.

Recommendation:
Wrap the check/insert in a transaction or enforce the plan limit with a database-level mechanism suitable for SQLite. Add a concurrency regression test or design note documenting serialized writes.

### CR-19-I8 — Important — Production tier default depends on `HOSTING` being set exactly right

Evidence:
- `backend/auth/__init__.py:135-140`: local registrations become Premium unless `HOSTING` is `true`, `1`, or `yes`.
- Warpsmith local-premium skill documents the intended local convenience behavior.

Problem:
The local convenience default is safe for development, but a production deployment missing `HOSTING=true` grants Premium to all new users.

Impact:
A single env misconfiguration bypasses monetization globally.

Recommendation:
Prefer an explicit `LOCAL_PREMIUM=true` or `WARPSMITH_ENV=development` switch, default production-like in unknown environments, and add a startup warning/fail-fast check for public hosting without billing config.

### CR-19-I9 — Important — Billing/feature-gate tests do not cover bypass paths

Evidence:
- Focused pytest run passed `48 passed` for roster/rate-limit/generate tests.
- Search found no dedicated billing tests matching the CR-19 boundaries.
- Runtime probes exposed failures not caught by tests: duplicate limit bypass, public roster creation by Free user, unsigned webhook, unauthenticated subscribe/portal, missing `/api/me.features`.

Problem:
Existing tests prove basic roster behavior but do not validate the subscription model or feature-gate security properties.

Impact:
Billing regressions can ship unnoticed.

Recommendation:
Add tests for plan definitions, `/api/me` features, create/duplicate/import roster caps, public roster gate, auto-play quota/auth/ownership, checkout auth/session creation, webhook signature validation, upgrade/downgrade/idempotency, and pricing CTA method contract.

### CR-19-S1 — Suggestion — Local Premium behavior should be explicitly labelled in user-visible/debug output

Evidence:
- `backend/auth/__init__.py:135-140` silently grants Premium locally.

Problem:
Local Premium is useful, but it can confuse browser smoke tests and manual QA when `/api/me` says Premium for newly registered local accounts.

Recommendation:
Expose an environment/debug banner or log line explaining `LOCAL_DEV_PREMIUM` behavior so reviewers do not mistake local behavior for production billing state.

## Verification performed

Commands/checks:

```bash
uv run python -m pytest tests/test_rosters.py tests/test_roster.py tests/test_generate_roster.py tests/test_rate_limit.py -q
```

Result: `48 passed, 26 warnings`.

```bash
curl -sS -o /tmp/health19.txt -w '%{http_code}\n' http://127.0.0.1:8000/api/health && cat /tmp/health19.txt
```

Result: `200 {"status":"ok","version":"0.7.7"}`.

Runtime probes with `TestClient`:

- Forced Free user could create three rosters; fourth create returned 403.
- Forced Free user could duplicate after hitting limit and reach four rosters.
- Forced Free user could create `is_public=True`; DB stored `is_public=1`.
- `/api/me` returned no `features` and no `trial_ends_at`.
- Unsigned `POST /api/webhooks/stripe` returned 200.
- Unauthenticated `POST /api/subscribe` returned `302 /pricing`.
- `GET /api/billing/portal` returned `302 /account/billing`.

Browser smoke:

- `/pricing` loaded with title `Pricing — Warpsmith`.
- Premium CTA href was `/api/subscribe`.
- Page text advertised `1 saved roster`.
- Browser console had no app JS errors; Tailwind CDN production warning was present.

Independent review:

- `delegate_task` performed a second-pass review and independently confirmed the same major billing/gate failures.

Codex:

- Attempted, but unavailable: `/usr/bin/bash: line 3: codex: command not found`.

## Non-findings / notes

- No secrets were exposed in this report.
- Test users/rosters created by runtime probes were cleaned up from `simulator.db`.
- This review did not apply source-code fixes; it only updated review artifacts and tracker docs.
