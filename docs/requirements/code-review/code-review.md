     1|---
     2|title: Code Review — execution index
     3|slug: code-review
     4|index: CR-v0.1
     5|status: in-progress
     6|date: 2026-05-10
     7|triage_summary: ../../reviews/2026-05-10/triage-summary.md
     8|source: ../code-review-plan.md
     9|tags: [requirements, code-review, verification, quality]
    10|---
    11|
    12|# Code Review — execution index
    13|
    14|Этот индекс атомизированной проверки кода создан из `../code-review-plan.md`.
    15|Он ссылается на каждый CR-артефакт и отражает статус выполнения.
    16|
    17|Remediation plan: [remediation-plan.md](remediation-plan.md)
    18|
    19|## Current status
    20|
    21|- **Overall status:** In Progress
    22|- **Total CR artifacts:** 25
    23|- **Completed:** 1
    24|- **In progress:** 0
    25|- **Pending:** 0
    26|- **Blocked:** 0
    27|- **Request Changes:** 24
    28|- **Critical open:** 38
    29|- **Important open:** 112
    30|
    31|## Status legend
    32|
    33|| Status | Meaning |
    34||---|---|
    35|| Pending | Review task is not started. |
    36|| In Progress | Review task is being executed. |
    37|| Blocked | Review cannot proceed until dependency/context is resolved. |
    38|| Request Changes | Review executed and found blocking/important issues. |
    39|| Approved | Review executed and no blocking issues remain. |
    40|
    41|## Atomic review artifacts
    42|
    43|| ID | Status | Artifact | Counts | Priority | Triage | Objective | Report |
    44||---|---|---|---:|---|---|---|---|
    45|| CR-00 | Approved | [Inventory and baseline](cr-00-inventory-and-baseline.md) | C0 / I0 / S4 | Accepted/postponed | [triage](../../reviews/2026-05-10/triage-summary.md#cr-00) | зафиксировать живое состояние проекта до review, чтобы отличать реальные проблемы от stale docs. | [report](../../reviews/2026-05-09/CR-00-inventory-and-baseline.md) |
    46|| CR-01 | Request Changes | [Requirements and spec alignment map](cr-01-requirements-and-spec-alignment-map.md) | C0 / I5 / S4 | P2 | [triage](../../reviews/2026-05-10/triage-summary.md#cr-01) | составить карту «требование → код → тесты», чтобы review не был проверкой на ощущениях. | [report](../../reviews/2026-05-09/CR-01-requirements-and-spec-alignment-map.md) |
    47|| CR-02 | Request Changes | [Static security and secrets scan](cr-02-static-security-and-secrets-scan.md) | C2 / I7 / S4 | P0 | [triage](../../reviews/2026-05-10/triage-summary.md#cr-02) | найти блокирующие security issues до ручного review. | [report](../../reviews/2026-05-09/CR-02-static-security-and-secrets-scan.md) |
    48|| CR-03 | Request Changes | [Auth and session review](cr-03-auth-and-session-review.md) | C1 / I5 / S3 | P0 | [triage](../../reviews/2026-05-10/triage-summary.md#cr-03) | проверить регистрацию, вход, logout, JWT cookie, OAuth boundaries. | [report](../../reviews/2026-05-09/CR-03-auth-and-session-review.md) |
    49|| CR-04 | Request Changes | [Authorization and ownership review](cr-04-authorization-and-ownership-review.md) | C2 / I3 / S3 | P0 | [triage](../../reviews/2026-05-10/triage-summary.md#cr-04) | проверить, что пользователь видит и меняет только свои rosters/replays/subscriptions. | [report](../../reviews/2026-05-09/CR-04-authorization-and-ownership-review.md) |
    50|| CR-05 | Request Changes | [Database and persistence review](cr-05-database-and-persistence-review.md) | C1 / I6 / S4 | P0 | [triage](../../reviews/2026-05-10/triage-summary.md#cr-05) | проверить schema, migrations/init, JSON parsing, SQLite concurrency assumptions. | [report](../../reviews/2026-05-09/CR-05-database-and-persistence-review.md) |
    51|| CR-06 | Request Changes | [Wiki loader and parser review](cr-06-wiki-loader-and-parser-review.md) | C1 / I4 / S1 | P1 | [triage](../../reviews/2026-05-10/triage-summary.md#cr-06) | проверить wiki-driven data loading, YAML frontmatter, no hardcode scaling risks. | [report](../../reviews/2026-05-09/CR-06-wiki-loader-and-parser-review.md) |
    52|| CR-07 | Request Changes | [Combat engine review](cr-07-combat-engine-review.md) | C3 / I4 / S1 | P1 | [triage](../../reviews/2026-05-10/triage-summary.md#cr-07) | проверить core combat correctness: Hit → Wound → Save → Damage → FNP. | [report](../../reviews/2026-05-09/CR-07-combat-engine-review.md) |
    53|| CR-08 | Request Changes | [Game state and phase machine review](cr-08-game-state-and-phase-machine-review.md) | C3 / I4 / S1 | P1 | [triage](../../reviews/2026-05-10/triage-summary.md#cr-08) | проверить 10th Edition game loop, phase transitions, round counting, CP, battle-shock. | [report](../../reviews/2026-05-09/CR-08-game-state-and-phase-machine-review.md) |
    54|| CR-09 | Request Changes | [Movement, charge and melee review](cr-09-movement-charge-and-melee-review.md) | C3 / I3 / S0 | P1 | [triage](../../reviews/2026-05-10/triage-summary.md#cr-09) | проверить, что melee units реально сближаются, charge возможен, melee damage логируется. | [report](../../reviews/2026-05-09/CR-09-movement-charge-and-melee-review.md) |
    55|| CR-10 | Request Changes | [Mission, objectives and VP review](cr-10-mission-objectives-and-vp-review.md) | C2 / I4 / S0 | P1 | [triage](../../reviews/2026-05-10/triage-summary.md#cr-10) | проверить scoring, objectives, mission name normalization, Battle Ready VP. | [report](../../reviews/2026-05-09/CR-10-mission-objectives-and-vp-review.md) |
    56|| CR-11 | Request Changes | [Terrain, cover and LoS review](cr-11-terrain-cover-and-los-review.md) | C3 / I4 / S0 | P1 | [triage](../../reviews/2026-05-10/triage-summary.md#cr-11) | проверить текущую F2.13 модель и gaps относительно F2.18 Terrain Mechanics 10e. | [report](../../reviews/2026-05-09/CR-11-terrain-cover-and-los-review.md) |
    57|| CR-12 | Request Changes | [Roster validation and points review](cr-12-roster-validation-and-points-review.md) | C3 / I4 / S0 | P1 | [triage](../../reviews/2026-05-10/triage-summary.md#cr-12) | проверить PTS formula, Warlord, squad size, battleline caps, generated roster validity. | [report](../../reviews/2026-05-09/CR-12-roster-validation-and-points-review.md) |
    58|| CR-13 | Request Changes | [API route surface review](cr-13-api-route-surface-review.md) | C3 / I5 / S0 | P1 | [triage](../../reviews/2026-05-10/triage-summary.md#cr-13) | проверить FastAPI route structure, method correctness, route ordering, response contracts. | [report](../../reviews/2026-05-09/CR-13-api-route-surface-review.md) |
    59|| CR-14 | Request Changes | [Autoplay, replay and result review](cr-14-autoplay-replay-and-result-review.md) | C3 / I4 / S0 | P0 | [triage](../../reviews/2026-05-10/triage-summary.md#cr-14) | проверить full simulation pipeline: setup → auto-play → replay storage → result summary. | [report](../../reviews/2026-05-09/CR-14-autoplay-replay-and-result-review.md) |
    60|| CR-15 | Request Changes | [AI decision engine and faction profile review](cr-15-ai-decision-engine-and-faction-profile-review.md) | C3 / I4 / S0 | P1 | [triage](../../reviews/2026-05-10/triage-summary.md#cr-15) | проверить greedy decisions, faction AI profiles, behavior activation, deployment integration. | [report](../../reviews/2026-05-09/CR-15-ai-decision-engine-and-faction-profile-review.md) |
    61|| CR-16 | Request Changes | [Team Builder frontend review](cr-16-team-builder-frontend-review.md) | C0 / I2 / S2 | P1 | [triage](../../reviews/2026-05-10/triage-summary.md#cr-16) | проверить Team Builder Alpine state, unit modal, roster save/edit, Warlord UI, PTS UI. | [report](../../reviews/2026-05-10/CR-16-team-builder-frontend-review.md) |
    62|| CR-17 | Request Changes | [Scenario Setup and battlefield map frontend review](cr-17-scenario-setup-and-battlefield-map-frontend-review.md) | C0 / I4 / S1 | P1 | [triage](../../reviews/2026-05-10/triage-summary.md#cr-17) | проверить mission/format selection, generated opponent, strategic map, simulation launch. | [report](../../reviews/2026-05-10/CR-17-scenario-setup-and-battlefield-map-frontend-review.md) |
    63|| CR-18 | Request Changes | [Pages/templates/navigation review](cr-18-pages-templates-navigation-review.md) | C0 / I4 / S1 | P1 | [triage](../../reviews/2026-05-10/triage-summary.md#cr-18) | проверить base navigation, pricing/auth pages, static assets, favicon, mode toggles. | [report](../../reviews/2026-05-10/CR-18-pages-templates-navigation-review.md) |
    64|| CR-19 | Request Changes | [Billing, feature gate and subscription review](cr-19-billing-feature-gate-and-subscription-review.md) | C3 / I8 / S1 | P0 | [triage](../../reviews/2026-05-10/triage-summary.md#cr-19) | проверить monetization boundaries and free/premium gates. | [report](../../reviews/2026-05-10/CR-19-billing-feature-gate-and-subscription-review.md) |
    65|| CR-20 | Request Changes | [Deployment, config and production readiness review](cr-20-deployment-config-and-production-readiness-review.md) | C2 / I7 / S1 | P0 | [triage](../../reviews/2026-05-10/triage-summary.md#cr-20) | проверить Docker/Railway/env/security headers/rate limit/logging. | [report](../../reviews/2026-05-10/CR-20-deployment-config-and-production-readiness-review.md) |
    66|| CR-21 | Request Changes | [Documentation consistency review](cr-21-documentation-consistency-review.md) | C0 / I8 / S2 | P2 | [triage](../../reviews/2026-05-10/triage-summary.md#cr-21) | проверить, что docs не расходятся с кодом после review baseline. | [report](../../reviews/2026-05-10/CR-21-documentation-consistency-review.md) |
    67|| CR-22 | Request Changes | [Test suite quality review](cr-22-test-suite-quality-review.md) | C2 / I9 / S2 | P0 | [triage](../../reviews/2026-05-10/triage-summary.md#cr-22) | проверить не только что тесты проходят, но что они ловят реальные regressions. | [report](../../reviews/2026-05-10/CR-22-test-suite-quality-review.md) |
    68|| CR-23 | Request Changes | [Performance and scalability review](cr-23-performance-and-scalability-review.md) | C0 / I7 / S3 | P2 | [triage](../../reviews/2026-05-10/triage-summary.md#cr-23) | проверить obvious bottlenecks before commercialization. | [report](../../reviews/2026-05-10/CR-23-performance-and-scalability-review.md) |
    69|| CR-24 | Request Changes | [Final integration regression gate](cr-24-final-integration-regression-gate.md) | C1 / I1 / S1 | P0 | [triage](../../reviews/2026-05-10/triage-summary.md#cr-24) | финально подтвердить, что review/fix cycle не сломал продукт. | [report](../../reviews/2026-05-10/CR-24-final-integration-regression-gate.md) |
    70|
    71|## Execution order
    72|
    73|1. Выполнить CR-00, CR-01, CR-02 как mandatory baseline.
    74|2. После baseline можно выполнять domain batches параллельно по плану из `../code-review-plan.md`.
    75|3. CR-24 выполнять только после triage/fixes или после явного решения принять debt.
    76|
    77|## Artifact links
    78|
    79|- [CR-00 — Inventory and baseline](cr-00-inventory-and-baseline.md)
    80|- [CR-01 — Requirements and spec alignment map](cr-01-requirements-and-spec-alignment-map.md)
    81|- [CR-02 — Static security and secrets scan](cr-02-static-security-and-secrets-scan.md)
    82|- [CR-03 — Auth and session review](cr-03-auth-and-session-review.md)
    83|- [CR-04 — Authorization and ownership review](cr-04-authorization-and-ownership-review.md)
    84|- [CR-05 — Database and persistence review](cr-05-database-and-persistence-review.md)
    85|- [CR-06 — Wiki loader and parser review](cr-06-wiki-loader-and-parser-review.md)
    86|- [CR-07 — Combat engine review](cr-07-combat-engine-review.md)
    87|- [CR-08 — Game state and phase machine review](cr-08-game-state-and-phase-machine-review.md)
    88|- [CR-09 — Movement, charge and melee review](cr-09-movement-charge-and-melee-review.md)
    89|- [CR-10 — Mission, objectives and VP review](cr-10-mission-objectives-and-vp-review.md)
    90|- [CR-11 — Terrain, cover and LoS review](cr-11-terrain-cover-and-los-review.md)
    91|- [CR-12 — Roster validation and points review](cr-12-roster-validation-and-points-review.md)
    92|- [CR-13 — API route surface review](cr-13-api-route-surface-review.md)
    93|- [CR-14 — Autoplay, replay and result review](cr-14-autoplay-replay-and-result-review.md)
    94|- [CR-15 — AI decision engine and faction profile review](cr-15-ai-decision-engine-and-faction-profile-review.md)
    95|- [CR-16 — Team Builder frontend review](cr-16-team-builder-frontend-review.md)
    96|- [CR-17 — Scenario Setup and battlefield map frontend review](cr-17-scenario-setup-and-battlefield-map-frontend-review.md)
    97|- [CR-18 — Pages/templates/navigation review](cr-18-pages-templates-navigation-review.md)
    98|- [CR-19 — Billing, feature gate and subscription review](cr-19-billing-feature-gate-and-subscription-review.md)
    99|- [CR-20 — Deployment, config and production readiness review](cr-20-deployment-config-and-production-readiness-review.md)
   100|- [CR-21 — Documentation consistency review](cr-21-documentation-consistency-review.md)
   101|- [CR-22 — Test suite quality review](cr-22-test-suite-quality-review.md)
   102|- [CR-23 — Performance and scalability review](cr-23-performance-and-scalability-review.md)
   103|- [CR-24 — Final integration regression gate](cr-24-final-integration-regression-gate.md)
   104|
   105|## Triage summary
   106|
   107|Created and linked: [docs/reviews/2026-05-10/triage-summary.md](../../reviews/2026-05-10/triage-summary.md)
   108|
   109|Current triage verdict: not release-ready. CR-24 executable gates passed, but release readiness remains blocked by open Critical/Important review debt and the reproduced result VP consistency issue.
   110|
   111|## Phase 2 checkpoint evidence
   112|
   113|Date: 2026-05-18
   114|
   115|Phase 2 roster-validator remediation is complete after Task 2.2 and Task 2.3 closure re-check sync. Shared Warlord validation/backend-frontend parity and feature-gate enforcement are aligned across task, review, source plan, index, and CR artifacts.
   116|
   117|Latest observed verification:
   118|- `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_roster*.py tests/test_rosters.py tests/test_generate_roster.py tests/test_team_builder.py -q` → 82 passed, 48 warnings.
   119|- `uv run python -m pytest tests/ -q` → 604 passed, 3 skipped, 60 warnings.
   120|- `uv run ruff check backend/state/roster.py web/routes/api_rosters.py backend/billing/plans.py backend/engine/ai/autoplay.py tests/test_roster.py tests/test_rosters.py tests/test_generate_roster.py tests/test_team_builder.py` → All checks passed.
   121|- `uv run ruff format --check backend/state/roster.py web/routes/api_rosters.py backend/billing/plans.py backend/engine/ai/autoplay.py tests/test_roster.py tests/test_rosters.py tests/test_generate_roster.py tests/test_team_builder.py` → 8 files already formatted.
   122|- `git diff --check -- docs/remediation/task-02-02-enforce-exactly-one-warlord-when-required.md docs/remediation/task-02-03-enforce-plan-feature-gates-consistently.md docs/remediation/remediation-plan.md docs/remediation/index.md docs/reviews/2026-05-18/task-02-03-enforce-plan-feature-gates-consistently-review.md docs/requirements/code-review/code-review.md` → clean.
   123|
   124|
   125|## Phase 3 checkpoint evidence
   126|
   127|Date: 2026-05-18
   128|
   129|Phase 3 combat-math remediation is complete and verified. Tasks 3.1, 3.2, and 3.3 are marked complete with all requirements checked. Focused combat/modifier suite: `50 passed in 10.38s`. Full suite: `604 passed, 3 skipped, 60 warnings`. Ruff lint/format and diff-check clean for Phase 3 touched files. CR-07 and CR-11 artifacts contain Phase 3 regression evidence.
   130|
   131|## Phase 4 checkpoint evidence — 2026-05-18
   132|
   133|Status: COMPLETE for Phase 4 remediation tasks 4.1, 4.2, and 4.3.
   134|
   135|Closed scope:
   136|- CR-08: 10e phase loop, CP generation, battle-shock reset timing, round/turn reset invariants.
   137|- CR-10: VP/objective scoring and mission normalization invariants — Task 4.3 fixed mission-defined 3/5/5 scoring, removed VP cap, and synced VP tracker to PlayerState.
   138|- CR-14: replay/result-facing phase/VP state remains aligned with canonical runtime state.
   139|- CR-24: full regression gate remains green after Phase 4 fixes.
   140|
   141|Verification (Task 4.3 fix run):
   142|- `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_mission.py tests/test_autoplay.py tests/test_result_screen.py -q` → 52 passed.
   143|- `uv run python -m pytest tests/ -q` → 604 passed, 3 skipped, 60 warnings.
   144|- `uv run ruff check backend/state/mission.py backend/engine/scenario.py tests/test_mission.py` → All checks passed.
   145|- `uv run ruff format --check backend/state/mission.py backend/engine/scenario.py tests/test_mission.py` → 3 files already formatted.
   146|- `git diff --check -- backend/state/mission.py backend/engine/scenario.py tests/test_mission.py` → clean.
   147|
   148|## Phase 5 checkpoint evidence — 2026-05-18
   149|
   150|Status: COMPLETE for Phase 5 remediation tasks 5.1, 5.2, and 5.3.
   151|
   152|Closed scope:
   153|- CR-09: charge destination (8-cell adjacency, no enemy-occupy), engagement identity, melee opponent-scoping, melee combat-engine resolution.
   154|- CR-11: terrain/LoS cache invalidation, cover argument order fix, AP0 cover cap enforcement.
   155|- CR-14: melee damage log format (`hits ... for ... damage`) with runtime IDs; cover fixes ensure correct shooting results.
   156|- CR-15: engagement and melee fixes ensure AI decisions have correct combat context.
   157|
   158|Verification (Phase 5 closure):
   159|- `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_movement.py tests/test_terrain.py tests/test_scenario.py tests/test_result_screen.py -q` → 22 passed.
   160|- `uv run python -m pytest tests/ -q` → 622 passed, 3 skipped, 60 warnings.
   161|- `uv run ruff check backend/state/map.py backend/engine/combat.py backend/engine/scenario.py tests/test_movement.py tests/test_terrain.py` → All checks passed.
   162|- `uv run ruff format --check backend/state/map.py backend/engine/combat.py backend/engine/scenario.py tests/test_movement.py tests/test_terrain.py` → 5 files already formatted.
   163|- `git diff --check -- backend/state/map.py backend/engine/combat.py backend/engine/scenario.py tests/test_movement.py tests/test_terrain.py` → clean.
   164|
   165|## Phase 4 checkpoint evidence — 2026-05-19 re-check
   166|
   167|Verdict: REQUEST CHANGES. Do not treat earlier Phase 4 completion evidence as final. Task 4.3 still blocks the checkpoint:
   168|
   169|- Only War isolated objective probe: 5 VP, expected 3.
   170|- Take and Hold isolated objective probe: 5 VP, expected 5.
   171|- Purge the Foe isolated objective probe: 0 VP, expected 5.
   172|- Scenario VP sync and VP-cap removal probes pass.
   173|- Battle Ready exact-once/idempotence/final replay-result tests are still missing.
   174|
   175|Latest gates: scoped Phase 4 suite 80 passed in 8.55s; full suite 622 passed, 3 skipped, 60 warnings in 51.93s; Ruff check passed; Ruff format check passed.
   176|
   177|

## Phase 4 checkpoint sync — 2026-05-19 (Task 4.3 re-check FIXED)

- Task 4.3 reopened findings are fixed and re-verified.
- Mission VP contract now enforced through mission-defined values in canonical scoring paths.
- Battle Ready finalization is idempotent and final snapshot parity is covered by regression tests.
- Verification: scoped 84 passed; full suite 626 passed, 3 skipped; Ruff/format clean.

