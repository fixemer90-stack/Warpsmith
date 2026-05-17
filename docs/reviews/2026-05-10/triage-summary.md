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

## Finding groups

Remediation plan: [docs/requirements/code-review/remediation-plan.md](remediation-plan.md)

All CR findings are triaged into exactly four groups. CR headings remain stable link targets from the execution index and CR artifacts.

| Group | CRs | Release meaning |
|---|---|---|
| P0 release blocker | CR-02, CR-03, CR-04, CR-05, CR-14, CR-19, CR-20, CR-22, CR-24 | Must be fixed before any release-ready verdict. These findings cover security/auth, ownership, data loss, paid-feature enforcement, production safety, result integrity, and tests for those blockers. |
| P1 core correctness | CR-06, CR-07, CR-08, CR-09, CR-10, CR-11, CR-12, CR-13, CR-15, CR-16, CR-17, CR-18 | Core product correctness and integration. These can be worked after P0 is stabilized, but they still block a high-confidence simulator release unless explicitly narrowed. |
| P2 important debt | CR-01, CR-21, CR-23 | Important debt that should be fixed before commercialization scale-up, or accepted with owner/date/guardrail if release scope is intentionally narrowed. |
| Accepted / postponed | CR-00 | Items not currently blocking release. No Critical or Important finding is accepted as release debt yet; only CR-00 baseline suggestions are postponed as hygiene notes. |

## P0 release blocker

Must be fixed before any release-ready verdict. Critical findings cannot be accepted as debt. Important findings in this group also block release because they protect auth, persistence, billing, production safety, final result integrity, or regression confidence.

### CR-02 — Static security and secrets scan

- **Group:** P0 release blocker
- **Counts:** C2 / I7 / S4
- **Triage status:** Open
- **Report:** [docs/reviews/2026-05-09/CR-02-static-security-and-secrets-scan.md](../2026-05-09/CR-02-static-security-and-secrets-scan.md)
- **Next action:** Resolve secret/security findings first; rotate anything that may be real.

### CR-03 — Auth and session review

- **Group:** P0 release blocker
- **Counts:** C1 / I5 / S3
- **Triage status:** Open
- **Report:** [docs/reviews/2026-05-09/CR-03-auth-and-session-review.md](../2026-05-09/CR-03-auth-and-session-review.md)
- **Next action:** Fix auth/session blockers and add regression tests around login/logout/JWT cookie behavior.

### CR-04 — Authorization and ownership review

- **Group:** P0 release blocker
- **Counts:** C2 / I3 / S3
- **Triage status:** Open
- **Report:** [docs/reviews/2026-05-09/CR-04-authorization-and-ownership-review.md](../2026-05-09/CR-04-authorization-and-ownership-review.md)
- **Next action:** Fix roster/replay/subscription ownership boundaries.

### CR-05 — Database and persistence review

- **Group:** P0 release blocker
- **Counts:** C1 / I6 / S4
- **Triage status:** Open
- **Report:** [docs/reviews/2026-05-09/CR-05-database-and-persistence-review.md](../2026-05-09/CR-05-database-and-persistence-review.md)
- **Next action:** Fix persistence/data-loss risks before production deploy.

### CR-14 — Autoplay, replay and result review

- **Group:** P0 release blocker
- **Counts:** C3 / I4 / S0
- **Triage status:** Open
- **Report:** [docs/reviews/2026-05-09/CR-14-autoplay-replay-and-result-review.md](../2026-05-09/CR-14-autoplay-replay-and-result-review.md)
- **Next action:** Fix non-unique replay IDs, final VP snapshots, duplicate-name attribution, VP event parsing, result-card charge counts.

### CR-19 — Billing, feature gate and subscription review

- **Group:** P0 release blocker
- **Counts:** C3 / I8 / S1
- **Triage status:** Open
- **Report:** [docs/reviews/2026-05-10/CR-19-billing-feature-gate-and-subscription-review.md](CR-19-billing-feature-gate-and-subscription-review.md)
- **Next action:** Implement or explicitly disable commercialization promises: webhook signature, user-bound checkout/portal, auto-play gating, roster limits, tier features.

### CR-20 — Deployment, config and production readiness review

- **Group:** P0 release blocker
- **Counts:** C2 / I7 / S1
- **Triage status:** Open
- **Report:** [docs/reviews/2026-05-10/CR-20-deployment-config-and-production-readiness-review.md](CR-20-deployment-config-and-production-readiness-review.md)
- **Next action:** Fix replay-deleting migration, hardcoded JWT fallback, CSP/sentry/rate-limit/branch deployment risks.

### CR-22 — Test suite quality review

- **Group:** P0 release blocker
- **Counts:** C2 / I9 / S2
- **Triage status:** Open
- **Report:** [docs/reviews/2026-05-10/CR-22-test-suite-quality-review.md](CR-22-test-suite-quality-review.md)
- **Next action:** Add tests for blocking security/auth/billing/persistence/result regressions; remove weak/placeholder coverage.

### CR-24 — Final integration regression gate

- **Group:** P0 release blocker
- **Counts:** C1 / I1 / S1
- **Triage status:** Open
- **Report:** [docs/reviews/2026-05-10/CR-24-final-integration-regression-gate.md](CR-24-final-integration-regression-gate.md)
- **Next action:** Re-run after triage/remediation; current blocker is unresolved CR debt plus stale result VP smoke.

## P1 core correctness

Core simulator and UI/API correctness. Fix after P0 batches, then run focused deterministic probes plus full regression.

### CR-06 — Wiki loader and parser review

- **Group:** P1 core correctness
- **Counts:** C1 / I4 / S1
- **Triage status:** Open
- **Report:** [docs/reviews/2026-05-09/CR-06-wiki-loader-and-parser-review.md](../2026-05-09/CR-06-wiki-loader-and-parser-review.md)
- **Next action:** Fix unsafe cache/content validation gaps; reconcile unit files vs loaded units and zero/no-weapon data quality findings.

### CR-07 — Combat engine review

- **Group:** P1 core correctness
- **Counts:** C3 / I4 / S1
- **Triage status:** Open
- **Report:** [docs/reviews/2026-05-09/CR-07-combat-engine-review.md](../2026-05-09/CR-07-combat-engine-review.md)
- **Next action:** Fix combat rules: natural 6 auto-wounds without Lethal Hits, Devastating Wounds saves, AP double-apply, Sustained Hits resolution.

### CR-08 — Game state and phase machine review

- **Group:** P1 core correctness
- **Counts:** C3 / I4 / S1
- **Triage status:** Open
- **Report:** [docs/reviews/2026-05-09/CR-08-game-state-and-phase-machine-review.md](../2026-05-09/CR-08-game-state-and-phase-machine-review.md)
- **Next action:** Fix 10e phase/round/CP/battle-shock state-machine blockers with deterministic probes.

### CR-09 — Movement, charge and melee review

- **Group:** P1 core correctness
- **Counts:** C3 / I3 / S0
- **Triage status:** Open
- **Report:** [docs/reviews/2026-05-09/CR-09-movement-charge-and-melee-review.md](../2026-05-09/CR-09-movement-charge-and-melee-review.md)
- **Next action:** Fix melee movement/charge/melee damage integration so units can reliably engage and log damage.

### CR-10 — Mission, objectives and VP review

- **Group:** P1 core correctness
- **Counts:** C2 / I4 / S0
- **Triage status:** Open
- **Report:** [docs/reviews/2026-05-09/CR-10-mission-objectives-and-vp-review.md](../2026-05-09/CR-10-mission-objectives-and-vp-review.md)
- **Next action:** Fix scoring/objective/Battle Ready/winner consistency issues.

### CR-11 — Terrain, cover and LoS review

- **Group:** P1 core correctness
- **Counts:** C3 / I4 / S0
- **Triage status:** Open
- **Report:** [docs/reviews/2026-05-09/CR-11-terrain-cover-and-los-review.md](../2026-05-09/CR-11-terrain-cover-and-los-review.md)
- **Next action:** Fix cover argument order, AP0 cover cap, documented LoS blocking, LoS cache invalidation, and terrain integration tests.

### CR-12 — Roster validation and points review

- **Group:** P1 core correctness
- **Counts:** C3 / I4 / S0
- **Triage status:** Open
- **Report:** [docs/reviews/2026-05-09/CR-12-roster-validation-and-points-review.md](../2026-05-09/CR-12-roster-validation-and-points-review.md)
- **Next action:** Fix PTS/Warlord/squad size/battleline/generated roster validation gaps.

### CR-13 — API route surface review

- **Group:** P1 core correctness
- **Counts:** C3 / I5 / S0
- **Triage status:** Open
- **Report:** [docs/reviews/2026-05-09/CR-13-api-route-surface-review.md](../2026-05-09/CR-13-api-route-surface-review.md)
- **Next action:** Fix route/auth/frontend fetch/status-code contract issues after ownership/auth batch.

### CR-15 — AI decision engine and faction profile review

- **Group:** P1 core correctness
- **Counts:** C3 / I4 / S0
- **Triage status:** Open
- **Report:** [docs/reviews/2026-05-09/CR-15-ai-decision-engine-and-faction-profile-review.md](../2026-05-09/CR-15-ai-decision-engine-and-faction-profile-review.md)
- **Next action:** Wire F3.1/F3.2 decision engine into live phases; verify faction behavior overrides, target priorities, deployment objectives.

### CR-16 — Team Builder frontend review

- **Group:** P1 core correctness
- **Counts:** C0 / I2 / S2
- **Triage status:** Open
- **Report:** [docs/reviews/2026-05-10/CR-16-team-builder-frontend-review.md](CR-16-team-builder-frontend-review.md)
- **Next action:** Remove stale duplicate modal risk and replace placeholder modal tests with browser-visible assertions.

### CR-17 — Scenario Setup and battlefield map frontend review

- **Group:** P1 core correctness
- **Counts:** C0 / I4 / S1
- **Triage status:** Open
- **Report:** [docs/reviews/2026-05-10/CR-17-scenario-setup-and-battlefield-map-frontend-review.md](CR-17-scenario-setup-and-battlefield-map-frontend-review.md)
- **Next action:** Fix Scenario Setup/map/generated-opponent contracts beyond happy-path launch.

### CR-18 — Pages/templates/navigation review

- **Group:** P1 core correctness
- **Counts:** C0 / I4 / S1
- **Triage status:** Open
- **Report:** [docs/reviews/2026-05-10/CR-18-pages-templates-navigation-review.md](CR-18-pages-templates-navigation-review.md)
- **Next action:** Fix broken pricing CTA, shared helper CSS under Tailwind CDN, Progressive Disclosure localStorage failure path, and tests.

## P2 important debt

Important but not the first release-stop batch. These items need fix or explicit accepted-debt entries before commercialization scale-up.

### CR-01 — Requirements and spec alignment map

- **Group:** P2 important debt
- **Counts:** C0 / I5 / S4
- **Triage status:** Open
- **Report:** [docs/reviews/2026-05-09/CR-01-requirements-and-spec-alignment-map.md](../2026-05-09/CR-01-requirements-and-spec-alignment-map.md)
- **Next action:** Fix spec/docs alignment after code fixes; do not let stale specs define release readiness.

### CR-21 — Documentation consistency review

- **Group:** P2 important debt
- **Counts:** C0 / I8 / S2
- **Triage status:** Open
- **Report:** [docs/reviews/2026-05-10/CR-21-documentation-consistency-review.md](CR-21-documentation-consistency-review.md)
- **Next action:** Sync docs after fixes: feature specs, C4, indexes, ROADMAP, AGENTS, CHANGELOG.

### CR-23 — Performance and scalability review

- **Group:** P2 important debt
- **Counts:** C0 / I7 / S3
- **Triage status:** Open
- **Report:** [docs/reviews/2026-05-10/CR-23-performance-and-scalability-review.md](CR-23-performance-and-scalability-review.md)
- **Next action:** Fix or accept pagination/indexing/cache/sync-autoplay/telemetry risks before commercialization scale-up.

## Accepted / postponed

No Critical or Important finding is accepted as release debt yet. Accepted/postponed currently contains only baseline notes and future hygiene.

### CR-00 — Inventory and baseline

- **Group:** Accepted / postponed
- **Counts:** C0 / I0 / S4
- **Triage status:** Accepted as baseline notes
- **Report:** [docs/reviews/2026-05-09/CR-00-inventory-and-baseline.md](../2026-05-09/CR-00-inventory-and-baseline.md)
- **Next action:** Baseline captured. Keep suggestions as follow-up hygiene while fixing later CRs.


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

## Phase 0 — Canonical Data + Runtime State Stabilization — COMPLETE

**2026-05-16.** All three Phase 0 remediation tasks done:

| Task | Status | Key change |
|------|--------|------------|
| 0.1 — Runtime unit identity contract | ✅ | `RosterState.units` list-based, `_build_summary`/`_parse_log_events` runtime-ID aware |
| 0.2 — Canonical GameState serializer | ✅ | Single `snapshot_game_state()` in `game_state.py`, autoplay+replay delegate |
| 0.3 — Stop destructive DB/replay | ✅ | No DROP TABLE, INSERT-not-REPLACE, UUID game_id |

Verification: 484 tests pass, lint/formatter clean. CR regression evidence in CR-05/06/12/14/20.

## Phase 1 — Content compiler / schemas — COMPLETE

All five Phase 1 remediation tasks done (1.1-1.5).

| Task | Status | Key result |
|------|--------|-----------|
| 1.1 — Content contract tests | ✅ | 23 tests, content.v1 Pydantic schema validation |
| 1.2 — Safe cache | ✅ | Pickle removed, JSON manifest pipeline |
| 1.3 — Squad/points metadata | ✅ | `squad_size` authoritative, `model_count` per-model |
| 1.4 — Canonical JSON artifacts | ✅ | 16 sharded artifacts, canonical IDs, strict schemas, deterministic rebuild |
| 1.5 — Frontmatter canonical IDs | ✅ | `source_path` tracking, canonical_id validation, duplicate/pre-write checks, 12 new tests |

Verification: 509+ tests pass (36 content contracts), lint/formatter clean.
CR evidence: CR-06, CR-11, CR-12, CR-21.

## Phase 2 — Roster validator — COMPLETE

All three Phase 2 remediation tasks done (2.1-2.3).

| Task | Status | Key result |
|------|--------|-----------|
| 2.1 — Lock canonical PTS formula | ✅ | `calculate_squad_pts()`, loadout/nob support, shared parity fixture |
| 2.2 — Enforce exactly one Warlord | ✅ | Shared Warlord validation, `is_warlord` param, `is_unit_eligible_warlord()` |
| 2.3 — Enforce plan/feature gates | ✅ | Shared `_check_roster_limits()` — create/duplicate/update all enforced |

Verification: 544 tests pass, lint/formatter clean.
CR evidence: CR-12, CR-16, CR-17, CR-19.
