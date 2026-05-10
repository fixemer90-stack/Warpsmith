---
title: "Full code review triage summary"
date: 2026-05-10
status: open
verdict: not-release-ready
source: docs/requirements/code-review/code-review.md
scope: CR-00..CR-24
---

# Full code review triage summary

## Verdict

Not release-ready.

CR-24 executable gates passed, but release readiness is blocked by unresolved code-review debt and one reproduced integration regression:

- Official tracker state after CR-24: 25 CR artifacts, 1 Approved, 24 Request Changes, 38 Critical open, 112 Important open.
- No Critical finding is accepted debt for release. Critical findings require fix + re-review.
- Important findings require either fix + re-review or an explicit accepted-debt entry with owner, due date, and release impact.
- CR-24 reproduced stale final VP in result/replay output: Battle Ready VP is included in runtime state but missing from the stored final round snapshot/result page.

## Count reconciliation note

The canonical release tracker is `docs/requirements/code-review/code-review.md` and currently reports 38 Critical / 112 Important open.

A quick scan of per-CR artifacts found a mismatch against the tracker because some artifacts/reports use different count formats and several older reports do not expose machine-readable frontmatter. Before closing the review program, reconcile counts by normalizing every CR report with explicit `critical`, `important`, and `suggestions` frontmatter or by updating the execution index from the report artifacts in one scripted pass.

## Release gates

| Gate | Status | Evidence |
|---|---:|---|
| Ruff lint | Pass | `uv run ruff check .` -> All checks passed |
| Ruff format check | Pass | `uv run ruff format --check .` -> 98 files already formatted |
| JS syntax | Pass | `node -c web/static/team_builder.js`, `scenario_setup.js`, `battlefield_map.js` |
| Full pytest | Pass | 454 passed, 3 skipped, 33 warnings |
| Local server health | Pass | `/api/health` -> 200, `{"status":"ok","version":"0.7.7"}` |
| Browser smoke | Pass | `/`, `/team-builder`, `/scenario-setup`, `/my-rosters`, `/result/auto_242424` load without console errors |
| Review debt gate | Fail | 38 Critical / 112 Important still open |
| Result VP consistency | Fail | `/result/auto_242424` showed 28/4 while runtime result was 38/14 |

## Immediate P0 blockers

These must be fixed before any release-ready verdict.

| Area | CRs | Why it blocks release | Required action |
|---|---|---|---|
| Secrets / auth / ownership | CR-02, CR-03, CR-04, CR-20 | Secret handling, session/auth boundaries, ownership bypass risk, hardcoded JWT fallback. | Remove/rotate secrets as needed, enforce auth/ownership, fail closed in production, add regression tests. |
| Data loss / persistence | CR-05, CR-14, CR-20 | Replay overwrite/data loss risks and startup migration deleting replay data. | Make replay identity immutable/unique, remove destructive migrations, add persistence regression tests. |
| Billing / monetization gates | CR-19 | Subscription model is not enforceable: unsigned webhook, stub checkout/portal, unauthenticated/ungated auto-play, roster-limit bypasses. | Implement fail-closed billing boundaries or explicitly disable paid claims until complete. |
| Core rules correctness | CR-07, CR-08, CR-09, CR-10, CR-11, CR-12 | Combat, game phase, movement/charge/melee, VP, terrain/cover/LoS, and roster validation findings affect simulator correctness. | Fix rule regressions in small batches with focused probes plus full tests. |
| Replay/result correctness | CR-14, CR-24 | Result page can show stale VP and unreliable summary attribution. | Fix final snapshot/result source of truth, duplicate-name attribution, and result regression coverage. |
| Test confidence | CR-22 | Test suite passes but misses key commercialization/auth/production/regression paths. | Add regression tests for every P0 fix; remove placeholder/status-only assertions where blocking. |

## Recommended remediation order

1. P0 security/auth/production fail-closed batch:
   - CR-02, CR-03, CR-04, CR-20.
   - Goal: no committed/local secret exposure, no hardcoded production JWT fallback, no ownership bypass, no destructive startup migration.

2. P0 monetization boundary batch:
   - CR-19.
   - Goal: product claims match enforced gates: Free/Premium roster limits, auto-play quota/auth, checkout/portal/webhook behavior, `/api/me` feature exposure.

3. P0 replay/result data integrity batch:
   - CR-14, CR-24.
   - Goal: unique replay IDs, no overwrite, final VP source of truth includes Battle Ready, same-name armies attribute events correctly.

4. P1 rules engine correctness batch:
   - CR-07, CR-08, CR-09, CR-10, CR-11, CR-12, CR-15.
   - Goal: 10e phase/rules correctness and faction AI integration verified by deterministic probes, not only helper tests.

5. P1 API/frontend integration batch:
   - CR-13, CR-16, CR-17, CR-18.
   - Goal: route contracts, Scenario Setup, Team Builder, navigation, and browser-visible behavior match specs.

6. P2 docs/tests/performance hardening batch:
   - CR-01, CR-21, CR-22, CR-23 plus CR-00 suggestions.
   - Goal: docs match code, test suite catches real regressions, performance/scalability risks are either fixed or explicitly accepted.

7. Re-run CR-24 final gate:
   - Full lint/format/JS syntax/pytest/server/browser smoke.
   - Add a deterministic final-result smoke that asserts API and page VP include Battle Ready.

## Per-CR triage register

Status values below are triage status, not implementation status. Each CR heading is a stable link target from the execution index and from the CR artifact. All Request Changes items remain open until fixed/re-reviewed or explicitly accepted as debt.

### CR-00 — Inventory and baseline

- **Counts:** C0 / I0 / S4
- **Priority:** P2
- **Triage status:** Accepted as baseline notes
- **Report:** [docs/reviews/2026-05-09/CR-00-inventory-and-baseline.md](../2026-05-09/CR-00-inventory-and-baseline.md)
- **Next action:** Baseline captured. Keep suggestions as follow-up hygiene while fixing later CRs.

### CR-01 — Requirements and spec alignment map

- **Counts:** C0 / I5 / S4
- **Priority:** P2
- **Triage status:** Open
- **Report:** [docs/reviews/2026-05-09/CR-01-requirements-and-spec-alignment-map.md](../2026-05-09/CR-01-requirements-and-spec-alignment-map.md)
- **Next action:** Fix spec/docs alignment after code fixes; do not let stale specs define release readiness.

### CR-02 — Static security and secrets scan

- **Counts:** C2 / I7 / S4
- **Priority:** P0
- **Triage status:** Open
- **Report:** [docs/reviews/2026-05-09/CR-02-static-security-and-secrets-scan.md](../2026-05-09/CR-02-static-security-and-secrets-scan.md)
- **Next action:** Resolve secret/security findings first; rotate anything that may be real.

### CR-03 — Auth and session review

- **Counts:** C1 / I5 / S3
- **Priority:** P0
- **Triage status:** Open
- **Report:** [docs/reviews/2026-05-09/CR-03-auth-and-session-review.md](../2026-05-09/CR-03-auth-and-session-review.md)
- **Next action:** Fix auth/session blockers and add regression tests around login/logout/JWT cookie behavior.

### CR-04 — Authorization and ownership review

- **Counts:** C2 / I3 / S3
- **Priority:** P0
- **Triage status:** Open
- **Report:** [docs/reviews/2026-05-09/CR-04-authorization-and-ownership-review.md](../2026-05-09/CR-04-authorization-and-ownership-review.md)
- **Next action:** Fix roster/replay/subscription ownership boundaries.

### CR-05 — Database and persistence review

- **Counts:** C1 / I6 / S4
- **Priority:** P0
- **Triage status:** Open
- **Report:** [docs/reviews/2026-05-09/CR-05-database-and-persistence-review.md](../2026-05-09/CR-05-database-and-persistence-review.md)
- **Next action:** Fix persistence/data-loss risks before production deploy.

### CR-06 — Wiki loader and parser review

- **Counts:** C1 / I4 / S1
- **Priority:** P1
- **Triage status:** Open
- **Report:** [docs/reviews/2026-05-09/CR-06-wiki-loader-and-parser-review.md](../2026-05-09/CR-06-wiki-loader-and-parser-review.md)
- **Next action:** Fix unsafe cache/content validation gaps; reconcile unit files vs loaded units and zero/no-weapon data quality findings.

### CR-07 — Combat engine review

- **Counts:** C3 / I4 / S1
- **Priority:** P0
- **Triage status:** Open
- **Report:** [docs/reviews/2026-05-09/CR-07-combat-engine-review.md](../2026-05-09/CR-07-combat-engine-review.md)
- **Next action:** Fix combat rules: natural 6 auto-wounds without Lethal Hits, Devastating Wounds saves, AP double-apply, Sustained Hits resolution.

### CR-08 — Game state and phase machine review

- **Counts:** C3 / I4 / S1
- **Priority:** P0
- **Triage status:** Open
- **Report:** [docs/reviews/2026-05-09/CR-08-game-state-and-phase-machine-review.md](../2026-05-09/CR-08-game-state-and-phase-machine-review.md)
- **Next action:** Fix 10e phase/round/CP/battle-shock state-machine blockers with deterministic probes.

### CR-09 — Movement, charge and melee review

- **Counts:** C3 / I3 / S0
- **Priority:** P0
- **Triage status:** Open
- **Report:** [docs/reviews/2026-05-09/CR-09-movement-charge-and-melee-review.md](../2026-05-09/CR-09-movement-charge-and-melee-review.md)
- **Next action:** Fix melee movement/charge/melee damage integration so units can reliably engage and log damage.

### CR-10 — Mission, objectives and VP review

- **Counts:** C2 / I4 / S0
- **Priority:** P0
- **Triage status:** Open
- **Report:** [docs/reviews/2026-05-09/CR-10-mission-objectives-and-vp-review.md](../2026-05-09/CR-10-mission-objectives-and-vp-review.md)
- **Next action:** Fix scoring/objective/Battle Ready/winner consistency issues.

### CR-11 — Terrain, cover and LoS review

- **Counts:** C3 / I4 / S0
- **Priority:** P0
- **Triage status:** Open
- **Report:** [docs/reviews/2026-05-09/CR-11-terrain-cover-and-los-review.md](../2026-05-09/CR-11-terrain-cover-and-los-review.md)
- **Next action:** Fix cover argument order, AP0 cover cap, documented LoS blocking, LoS cache invalidation, and terrain integration tests.

### CR-12 — Roster validation and points review

- **Counts:** C3 / I4 / S0
- **Priority:** P0
- **Triage status:** Open
- **Report:** [docs/reviews/2026-05-09/CR-12-roster-validation-and-points-review.md](../2026-05-09/CR-12-roster-validation-and-points-review.md)
- **Next action:** Fix PTS/Warlord/squad size/battleline/generated roster validation gaps.

### CR-13 — API route surface review

- **Counts:** C3 / I5 / S0
- **Priority:** P1
- **Triage status:** Open
- **Report:** [docs/reviews/2026-05-09/CR-13-api-route-surface-review.md](../2026-05-09/CR-13-api-route-surface-review.md)
- **Next action:** Fix route/auth/frontend fetch/status-code contract issues after ownership/auth batch.

### CR-14 — Autoplay, replay and result review

- **Counts:** C3 / I4 / S0
- **Priority:** P0
- **Triage status:** Open
- **Report:** [docs/reviews/2026-05-09/CR-14-autoplay-replay-and-result-review.md](../2026-05-09/CR-14-autoplay-replay-and-result-review.md)
- **Next action:** Fix non-unique replay IDs, final VP snapshots, duplicate-name attribution, VP event parsing, result-card charge counts.

### CR-15 — AI decision engine and faction profile review

- **Counts:** C3 / I4 / S0
- **Priority:** P1
- **Triage status:** Open
- **Report:** [docs/reviews/2026-05-09/CR-15-ai-decision-engine-and-faction-profile-review.md](../2026-05-09/CR-15-ai-decision-engine-and-faction-profile-review.md)
- **Next action:** Wire F3.1/F3.2 decision engine into live phases; verify faction behavior overrides, target priorities, deployment objectives.

### CR-16 — Team Builder frontend review

- **Counts:** C0 / I2 / S2
- **Priority:** P1
- **Triage status:** Open
- **Report:** [docs/reviews/2026-05-10/CR-16-team-builder-frontend-review.md](CR-16-team-builder-frontend-review.md)
- **Next action:** Remove stale duplicate modal risk and replace placeholder modal tests with browser-visible assertions.

### CR-17 — Scenario Setup and battlefield map frontend review

- **Counts:** C0 / I4 / S1
- **Priority:** P1
- **Triage status:** Open
- **Report:** [docs/reviews/2026-05-10/CR-17-scenario-setup-and-battlefield-map-frontend-review.md](CR-17-scenario-setup-and-battlefield-map-frontend-review.md)
- **Next action:** Fix Scenario Setup/map/generated-opponent contracts beyond happy-path launch.

### CR-18 — Pages/templates/navigation review

- **Counts:** C0 / I4 / S1
- **Priority:** P1
- **Triage status:** Open
- **Report:** [docs/reviews/2026-05-10/CR-18-pages-templates-navigation-review.md](CR-18-pages-templates-navigation-review.md)
- **Next action:** Fix broken pricing CTA, shared helper CSS under Tailwind CDN, Progressive Disclosure localStorage failure path, and tests.

### CR-19 — Billing, feature gate and subscription review

- **Counts:** C3 / I8 / S1
- **Priority:** P0
- **Triage status:** Open
- **Report:** [docs/reviews/2026-05-10/CR-19-billing-feature-gate-and-subscription-review.md](CR-19-billing-feature-gate-and-subscription-review.md)
- **Next action:** Implement or explicitly disable commercialization promises: webhook signature, user-bound checkout/portal, auto-play gating, roster limits, tier features.

### CR-20 — Deployment, config and production readiness review

- **Counts:** C2 / I7 / S1
- **Priority:** P0
- **Triage status:** Open
- **Report:** [docs/reviews/2026-05-10/CR-20-deployment-config-and-production-readiness-review.md](CR-20-deployment-config-and-production-readiness-review.md)
- **Next action:** Fix replay-deleting migration, hardcoded JWT fallback, CSP/sentry/rate-limit/branch deployment risks.

### CR-21 — Documentation consistency review

- **Counts:** C0 / I8 / S2
- **Priority:** P2
- **Triage status:** Open
- **Report:** [docs/reviews/2026-05-10/CR-21-documentation-consistency-review.md](CR-21-documentation-consistency-review.md)
- **Next action:** Sync docs after fixes: feature specs, C4, indexes, ROADMAP, AGENTS, CHANGELOG.

### CR-22 — Test suite quality review

- **Counts:** C2 / I9 / S2
- **Priority:** P0
- **Triage status:** Open
- **Report:** [docs/reviews/2026-05-10/CR-22-test-suite-quality-review.md](CR-22-test-suite-quality-review.md)
- **Next action:** Add tests for blocking security/auth/billing/persistence/result regressions; remove weak/placeholder coverage.

### CR-23 — Performance and scalability review

- **Counts:** C0 / I7 / S3
- **Priority:** P2
- **Triage status:** Open
- **Report:** [docs/reviews/2026-05-10/CR-23-performance-and-scalability-review.md](CR-23-performance-and-scalability-review.md)
- **Next action:** Fix or accept pagination/indexing/cache/sync-autoplay/telemetry risks before commercialization scale-up.

### CR-24 — Final integration regression gate

- **Counts:** C1 / I1 / S1
- **Priority:** P0
- **Triage status:** Open
- **Report:** [docs/reviews/2026-05-10/CR-24-final-integration-regression-gate.md](CR-24-final-integration-regression-gate.md)
- **Next action:** Re-run after triage/remediation; current blocker is unresolved CR debt plus stale result VP smoke.


## Accepted debt register

No Critical or Important finding is accepted as debt yet.

Use this table only after an explicit decision to defer a non-Critical item:

| Finding / CR | Severity | Owner | Accepted until | Justification | Required guardrail |
|---|---|---|---|---|---|
| _none_ | — | — | — | — | — |

## Re-review checklist

For each remediation batch:

1. Fix only the findings in that batch; avoid mixing unrelated refactors.
2. Add focused regression tests/probes that would have caught the original finding.
3. Run scoped tests first, then full project gates:
   - `uv run ruff check .`
   - `uv run ruff format --check .`
   - `node -c web/static/team_builder.js`
   - `node -c web/static/scenario_setup.js`
   - `node -c web/static/battlefield_map.js`
   - `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/ -q`
4. Update the relevant CR report/artifact with fixed/re-reviewed status.
5. Update this triage summary and `docs/requirements/code-review/code-review.md` counts.
6. After all P0/P1 release blockers are closed or explicitly accepted where allowed, re-run CR-24.
