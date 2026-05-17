---
title: Code Review — execution index
slug: code-review
index: CR-v0.1
status: in-progress
date: 2026-05-10
triage_summary: ../../reviews/2026-05-10/triage-summary.md
source: ../code-review-plan.md
tags: [requirements, code-review, verification, quality]
---

# Code Review — execution index

Этот индекс атомизированной проверки кода создан из `../code-review-plan.md`.
Он ссылается на каждый CR-артефакт и отражает статус выполнения.

Remediation plan: [remediation-plan.md](remediation-plan.md)

## Current status

- **Overall status:** In Progress
- **Total CR artifacts:** 25
- **Completed:** 1
- **In progress:** 0
- **Pending:** 0
- **Blocked:** 0
- **Request Changes:** 24
- **Critical open:** 38
- **Important open:** 112

## Status legend

| Status | Meaning |
|---|---|
| Pending | Review task is not started. |
| In Progress | Review task is being executed. |
| Blocked | Review cannot proceed until dependency/context is resolved. |
| Request Changes | Review executed and found blocking/important issues. |
| Approved | Review executed and no blocking issues remain. |

## Atomic review artifacts

| ID | Status | Artifact | Counts | Priority | Triage | Objective | Report |
|---|---|---|---:|---|---|---|---|
| CR-00 | Approved | [Inventory and baseline](cr-00-inventory-and-baseline.md) | C0 / I0 / S4 | Accepted/postponed | [triage](../../reviews/2026-05-10/triage-summary.md#cr-00) | зафиксировать живое состояние проекта до review, чтобы отличать реальные проблемы от stale docs. | [report](../../reviews/2026-05-09/CR-00-inventory-and-baseline.md) |
| CR-01 | Request Changes | [Requirements and spec alignment map](cr-01-requirements-and-spec-alignment-map.md) | C0 / I5 / S4 | P2 | [triage](../../reviews/2026-05-10/triage-summary.md#cr-01) | составить карту «требование → код → тесты», чтобы review не был проверкой на ощущениях. | [report](../../reviews/2026-05-09/CR-01-requirements-and-spec-alignment-map.md) |
| CR-02 | Request Changes | [Static security and secrets scan](cr-02-static-security-and-secrets-scan.md) | C2 / I7 / S4 | P0 | [triage](../../reviews/2026-05-10/triage-summary.md#cr-02) | найти блокирующие security issues до ручного review. | [report](../../reviews/2026-05-09/CR-02-static-security-and-secrets-scan.md) |
| CR-03 | Request Changes | [Auth and session review](cr-03-auth-and-session-review.md) | C1 / I5 / S3 | P0 | [triage](../../reviews/2026-05-10/triage-summary.md#cr-03) | проверить регистрацию, вход, logout, JWT cookie, OAuth boundaries. | [report](../../reviews/2026-05-09/CR-03-auth-and-session-review.md) |
| CR-04 | Request Changes | [Authorization and ownership review](cr-04-authorization-and-ownership-review.md) | C2 / I3 / S3 | P0 | [triage](../../reviews/2026-05-10/triage-summary.md#cr-04) | проверить, что пользователь видит и меняет только свои rosters/replays/subscriptions. | [report](../../reviews/2026-05-09/CR-04-authorization-and-ownership-review.md) |
| CR-05 | Request Changes | [Database and persistence review](cr-05-database-and-persistence-review.md) | C1 / I6 / S4 | P0 | [triage](../../reviews/2026-05-10/triage-summary.md#cr-05) | проверить schema, migrations/init, JSON parsing, SQLite concurrency assumptions. | [report](../../reviews/2026-05-09/CR-05-database-and-persistence-review.md) |
| CR-06 | Request Changes | [Wiki loader and parser review](cr-06-wiki-loader-and-parser-review.md) | C1 / I4 / S1 | P1 | [triage](../../reviews/2026-05-10/triage-summary.md#cr-06) | проверить wiki-driven data loading, YAML frontmatter, no hardcode scaling risks. | [report](../../reviews/2026-05-09/CR-06-wiki-loader-and-parser-review.md) |
| CR-07 | Request Changes | [Combat engine review](cr-07-combat-engine-review.md) | C3 / I4 / S1 | P1 | [triage](../../reviews/2026-05-10/triage-summary.md#cr-07) | проверить core combat correctness: Hit → Wound → Save → Damage → FNP. | [report](../../reviews/2026-05-09/CR-07-combat-engine-review.md) |
| CR-08 | Request Changes | [Game state and phase machine review](cr-08-game-state-and-phase-machine-review.md) | C3 / I4 / S1 | P1 | [triage](../../reviews/2026-05-10/triage-summary.md#cr-08) | проверить 10th Edition game loop, phase transitions, round counting, CP, battle-shock. | [report](../../reviews/2026-05-09/CR-08-game-state-and-phase-machine-review.md) |
| CR-09 | Request Changes | [Movement, charge and melee review](cr-09-movement-charge-and-melee-review.md) | C3 / I3 / S0 | P1 | [triage](../../reviews/2026-05-10/triage-summary.md#cr-09) | проверить, что melee units реально сближаются, charge возможен, melee damage логируется. | [report](../../reviews/2026-05-09/CR-09-movement-charge-and-melee-review.md) |
| CR-10 | Request Changes | [Mission, objectives and VP review](cr-10-mission-objectives-and-vp-review.md) | C2 / I4 / S0 | P1 | [triage](../../reviews/2026-05-10/triage-summary.md#cr-10) | проверить scoring, objectives, mission name normalization, Battle Ready VP. | [report](../../reviews/2026-05-09/CR-10-mission-objectives-and-vp-review.md) |
| CR-11 | Request Changes | [Terrain, cover and LoS review](cr-11-terrain-cover-and-los-review.md) | C3 / I4 / S0 | P1 | [triage](../../reviews/2026-05-10/triage-summary.md#cr-11) | проверить текущую F2.13 модель и gaps относительно F2.18 Terrain Mechanics 10e. | [report](../../reviews/2026-05-09/CR-11-terrain-cover-and-los-review.md) |
| CR-12 | Request Changes | [Roster validation and points review](cr-12-roster-validation-and-points-review.md) | C3 / I4 / S0 | P1 | [triage](../../reviews/2026-05-10/triage-summary.md#cr-12) | проверить PTS formula, Warlord, squad size, battleline caps, generated roster validity. | [report](../../reviews/2026-05-09/CR-12-roster-validation-and-points-review.md) |
| CR-13 | Request Changes | [API route surface review](cr-13-api-route-surface-review.md) | C3 / I5 / S0 | P1 | [triage](../../reviews/2026-05-10/triage-summary.md#cr-13) | проверить FastAPI route structure, method correctness, route ordering, response contracts. | [report](../../reviews/2026-05-09/CR-13-api-route-surface-review.md) |
| CR-14 | Request Changes | [Autoplay, replay and result review](cr-14-autoplay-replay-and-result-review.md) | C3 / I4 / S0 | P0 | [triage](../../reviews/2026-05-10/triage-summary.md#cr-14) | проверить full simulation pipeline: setup → auto-play → replay storage → result summary. | [report](../../reviews/2026-05-09/CR-14-autoplay-replay-and-result-review.md) |
| CR-15 | Request Changes | [AI decision engine and faction profile review](cr-15-ai-decision-engine-and-faction-profile-review.md) | C3 / I4 / S0 | P1 | [triage](../../reviews/2026-05-10/triage-summary.md#cr-15) | проверить greedy decisions, faction AI profiles, behavior activation, deployment integration. | [report](../../reviews/2026-05-09/CR-15-ai-decision-engine-and-faction-profile-review.md) |
| CR-16 | Request Changes | [Team Builder frontend review](cr-16-team-builder-frontend-review.md) | C0 / I2 / S2 | P1 | [triage](../../reviews/2026-05-10/triage-summary.md#cr-16) | проверить Team Builder Alpine state, unit modal, roster save/edit, Warlord UI, PTS UI. | [report](../../reviews/2026-05-10/CR-16-team-builder-frontend-review.md) |
| CR-17 | Request Changes | [Scenario Setup and battlefield map frontend review](cr-17-scenario-setup-and-battlefield-map-frontend-review.md) | C0 / I4 / S1 | P1 | [triage](../../reviews/2026-05-10/triage-summary.md#cr-17) | проверить mission/format selection, generated opponent, strategic map, simulation launch. | [report](../../reviews/2026-05-10/CR-17-scenario-setup-and-battlefield-map-frontend-review.md) |
| CR-18 | Request Changes | [Pages/templates/navigation review](cr-18-pages-templates-navigation-review.md) | C0 / I4 / S1 | P1 | [triage](../../reviews/2026-05-10/triage-summary.md#cr-18) | проверить base navigation, pricing/auth pages, static assets, favicon, mode toggles. | [report](../../reviews/2026-05-10/CR-18-pages-templates-navigation-review.md) |
| CR-19 | Request Changes | [Billing, feature gate and subscription review](cr-19-billing-feature-gate-and-subscription-review.md) | C3 / I8 / S1 | P0 | [triage](../../reviews/2026-05-10/triage-summary.md#cr-19) | проверить monetization boundaries and free/premium gates. | [report](../../reviews/2026-05-10/CR-19-billing-feature-gate-and-subscription-review.md) |
| CR-20 | Request Changes | [Deployment, config and production readiness review](cr-20-deployment-config-and-production-readiness-review.md) | C2 / I7 / S1 | P0 | [triage](../../reviews/2026-05-10/triage-summary.md#cr-20) | проверить Docker/Railway/env/security headers/rate limit/logging. | [report](../../reviews/2026-05-10/CR-20-deployment-config-and-production-readiness-review.md) |
| CR-21 | Request Changes | [Documentation consistency review](cr-21-documentation-consistency-review.md) | C0 / I8 / S2 | P2 | [triage](../../reviews/2026-05-10/triage-summary.md#cr-21) | проверить, что docs не расходятся с кодом после review baseline. | [report](../../reviews/2026-05-10/CR-21-documentation-consistency-review.md) |
| CR-22 | Request Changes | [Test suite quality review](cr-22-test-suite-quality-review.md) | C2 / I9 / S2 | P0 | [triage](../../reviews/2026-05-10/triage-summary.md#cr-22) | проверить не только что тесты проходят, но что они ловят реальные regressions. | [report](../../reviews/2026-05-10/CR-22-test-suite-quality-review.md) |
| CR-23 | Request Changes | [Performance and scalability review](cr-23-performance-and-scalability-review.md) | C0 / I7 / S3 | P2 | [triage](../../reviews/2026-05-10/triage-summary.md#cr-23) | проверить obvious bottlenecks before commercialization. | [report](../../reviews/2026-05-10/CR-23-performance-and-scalability-review.md) |
| CR-24 | Request Changes | [Final integration regression gate](cr-24-final-integration-regression-gate.md) | C1 / I1 / S1 | P0 | [triage](../../reviews/2026-05-10/triage-summary.md#cr-24) | финально подтвердить, что review/fix cycle не сломал продукт. | [report](../../reviews/2026-05-10/CR-24-final-integration-regression-gate.md) |

## Execution order

1. Выполнить CR-00, CR-01, CR-02 как mandatory baseline.
2. После baseline можно выполнять domain batches параллельно по плану из `../code-review-plan.md`.
3. CR-24 выполнять только после triage/fixes или после явного решения принять debt.

## Artifact links

- [CR-00 — Inventory and baseline](cr-00-inventory-and-baseline.md)
- [CR-01 — Requirements and spec alignment map](cr-01-requirements-and-spec-alignment-map.md)
- [CR-02 — Static security and secrets scan](cr-02-static-security-and-secrets-scan.md)
- [CR-03 — Auth and session review](cr-03-auth-and-session-review.md)
- [CR-04 — Authorization and ownership review](cr-04-authorization-and-ownership-review.md)
- [CR-05 — Database and persistence review](cr-05-database-and-persistence-review.md)
- [CR-06 — Wiki loader and parser review](cr-06-wiki-loader-and-parser-review.md)
- [CR-07 — Combat engine review](cr-07-combat-engine-review.md)
- [CR-08 — Game state and phase machine review](cr-08-game-state-and-phase-machine-review.md)
- [CR-09 — Movement, charge and melee review](cr-09-movement-charge-and-melee-review.md)
- [CR-10 — Mission, objectives and VP review](cr-10-mission-objectives-and-vp-review.md)
- [CR-11 — Terrain, cover and LoS review](cr-11-terrain-cover-and-los-review.md)
- [CR-12 — Roster validation and points review](cr-12-roster-validation-and-points-review.md)
- [CR-13 — API route surface review](cr-13-api-route-surface-review.md)
- [CR-14 — Autoplay, replay and result review](cr-14-autoplay-replay-and-result-review.md)
- [CR-15 — AI decision engine and faction profile review](cr-15-ai-decision-engine-and-faction-profile-review.md)
- [CR-16 — Team Builder frontend review](cr-16-team-builder-frontend-review.md)
- [CR-17 — Scenario Setup and battlefield map frontend review](cr-17-scenario-setup-and-battlefield-map-frontend-review.md)
- [CR-18 — Pages/templates/navigation review](cr-18-pages-templates-navigation-review.md)
- [CR-19 — Billing, feature gate and subscription review](cr-19-billing-feature-gate-and-subscription-review.md)
- [CR-20 — Deployment, config and production readiness review](cr-20-deployment-config-and-production-readiness-review.md)
- [CR-21 — Documentation consistency review](cr-21-documentation-consistency-review.md)
- [CR-22 — Test suite quality review](cr-22-test-suite-quality-review.md)
- [CR-23 — Performance and scalability review](cr-23-performance-and-scalability-review.md)
- [CR-24 — Final integration regression gate](cr-24-final-integration-regression-gate.md)

## Triage summary

Created and linked: [docs/reviews/2026-05-10/triage-summary.md](../../reviews/2026-05-10/triage-summary.md)

Current triage verdict: not release-ready. CR-24 executable gates passed, but release readiness remains blocked by open Critical/Important review debt and the reproduced result VP consistency issue.

## Phase 2 checkpoint evidence

Date: 2026-05-17

Phase 2 roster-validator remediation is complete and verified: 68 scoped roster tests passed; full suite 562 passed, 3 skipped; Ruff lint/format clean for Phase 2 Python files.
