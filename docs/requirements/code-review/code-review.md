---
title: Code Review — execution index
slug: code-review
index: CR-v0.1
status: pending
date: 2026-05-09
source: ../code-review-plan.md
tags: [requirements, code-review, verification, quality]
---

# Code Review — execution index

Этот индекс атомизированной проверки кода создан из `../code-review-plan.md`.
Он ссылается на каждый CR-артефакт и отражает статус выполнения.

## Current status

- **Overall status:** Pending
- **Total CR artifacts:** 25
- **Completed:** 0
- **In progress:** 0
- **Pending:** 25
- **Blocked:** 0
- **Critical open:** 0 known before execution
- **Important open:** 0 known before execution

## Status legend

| Status | Meaning |
|---|---|
| Pending | Review task is not started. |
| In Progress | Review task is being executed. |
| Blocked | Review cannot proceed until dependency/context is resolved. |
| Request Changes | Review executed and found blocking/important issues. |
| Approved | Review executed and no blocking issues remain. |

## Atomic review artifacts

| ID | Status | Artifact | Objective | Report target |
|---|---|---|---|---|
| CR-00 | Pending | [Inventory and baseline](cr-00-inventory-and-baseline.md) | зафиксировать живое состояние проекта до review, чтобы отличать реальные проблемы от stale docs. | `docs/reviews/YYYY-MM-DD/CR-00-inventory-and-baseline.md` |
| CR-01 | Pending | [Requirements and spec alignment map](cr-01-requirements-and-spec-alignment-map.md) | составить карту «требование → код → тесты», чтобы review не был проверкой на ощущениях. | `docs/reviews/YYYY-MM-DD/CR-01-requirements-and-spec-alignment-map.md` |
| CR-02 | Pending | [Static security and secrets scan](cr-02-static-security-and-secrets-scan.md) | найти блокирующие security issues до ручного review. | `docs/reviews/YYYY-MM-DD/CR-02-static-security-and-secrets-scan.md` |
| CR-03 | Pending | [Auth and session review](cr-03-auth-and-session-review.md) | проверить регистрацию, вход, logout, JWT cookie, OAuth boundaries. | `docs/reviews/YYYY-MM-DD/CR-03-auth-and-session-review.md` |
| CR-04 | Pending | [Authorization and ownership review](cr-04-authorization-and-ownership-review.md) | проверить, что пользователь видит и меняет только свои rosters/replays/subscriptions. | `docs/reviews/YYYY-MM-DD/CR-04-authorization-and-ownership-review.md` |
| CR-05 | Pending | [Database and persistence review](cr-05-database-and-persistence-review.md) | проверить schema, migrations/init, JSON parsing, SQLite concurrency assumptions. | `docs/reviews/YYYY-MM-DD/CR-05-database-and-persistence-review.md` |
| CR-06 | Pending | [Wiki loader and parser review](cr-06-wiki-loader-and-parser-review.md) | проверить wiki-driven data loading, YAML frontmatter, no hardcode scaling risks. | `docs/reviews/YYYY-MM-DD/CR-06-wiki-loader-and-parser-review.md` |
| CR-07 | Pending | [Combat engine review](cr-07-combat-engine-review.md) | проверить core combat correctness: Hit → Wound → Save → Damage → FNP. | `docs/reviews/YYYY-MM-DD/CR-07-combat-engine-review.md` |
| CR-08 | Pending | [Game state and phase machine review](cr-08-game-state-and-phase-machine-review.md) | проверить 10th Edition game loop, phase transitions, round counting, CP, battle-shock. | `docs/reviews/YYYY-MM-DD/CR-08-game-state-and-phase-machine-review.md` |
| CR-09 | Pending | [Movement, charge and melee review](cr-09-movement-charge-and-melee-review.md) | проверить, что melee units реально сближаются, charge возможен, melee damage логируется. | `docs/reviews/YYYY-MM-DD/CR-09-movement-charge-and-melee-review.md` |
| CR-10 | Pending | [Mission, objectives and VP review](cr-10-mission-objectives-and-vp-review.md) | проверить scoring, objectives, mission name normalization, Battle Ready VP. | `docs/reviews/YYYY-MM-DD/CR-10-mission-objectives-and-vp-review.md` |
| CR-11 | Pending | [Terrain, cover and LoS review](cr-11-terrain-cover-and-los-review.md) | проверить текущую F2.13 модель и gaps относительно F2.18 Terrain Mechanics 10e. | `docs/reviews/YYYY-MM-DD/CR-11-terrain-cover-and-los-review.md` |
| CR-12 | Pending | [Roster validation and points review](cr-12-roster-validation-and-points-review.md) | проверить PTS formula, Warlord, squad size, battleline caps, generated roster validity. | `docs/reviews/YYYY-MM-DD/CR-12-roster-validation-and-points-review.md` |
| CR-13 | Pending | [API route surface review](cr-13-api-route-surface-review.md) | проверить FastAPI route structure, method correctness, route ordering, response contracts. | `docs/reviews/YYYY-MM-DD/CR-13-api-route-surface-review.md` |
| CR-14 | Pending | [Autoplay, replay and result review](cr-14-autoplay-replay-and-result-review.md) | проверить full simulation pipeline: setup → auto-play → replay storage → result summary. | `docs/reviews/YYYY-MM-DD/CR-14-autoplay-replay-and-result-review.md` |
| CR-15 | Pending | [AI decision engine and faction profile review](cr-15-ai-decision-engine-and-faction-profile-review.md) | проверить greedy decisions, faction AI profiles, behavior activation, deployment integration. | `docs/reviews/YYYY-MM-DD/CR-15-ai-decision-engine-and-faction-profile-review.md` |
| CR-16 | Pending | [Team Builder frontend review](cr-16-team-builder-frontend-review.md) | проверить Team Builder Alpine state, unit modal, roster save/edit, Warlord UI, PTS UI. | `docs/reviews/YYYY-MM-DD/CR-16-team-builder-frontend-review.md` |
| CR-17 | Pending | [Scenario Setup and battlefield map frontend review](cr-17-scenario-setup-and-battlefield-map-frontend-review.md) | проверить mission/format selection, generated opponent, strategic map, simulation launch. | `docs/reviews/YYYY-MM-DD/CR-17-scenario-setup-and-battlefield-map-frontend-review.md` |
| CR-18 | Pending | [Pages/templates/navigation review](cr-18-pages-templates-navigation-review.md) | проверить base navigation, pricing/auth pages, static assets, favicon, mode toggles. | `docs/reviews/YYYY-MM-DD/CR-18-pages-templates-navigation-review.md` |
| CR-19 | Pending | [Billing, feature gate and subscription review](cr-19-billing-feature-gate-and-subscription-review.md) | проверить monetization boundaries and free/premium gates. | `docs/reviews/YYYY-MM-DD/CR-19-billing-feature-gate-and-subscription-review.md` |
| CR-20 | Pending | [Deployment, config and production readiness review](cr-20-deployment-config-and-production-readiness-review.md) | проверить Docker/Railway/env/security headers/rate limit/logging. | `docs/reviews/YYYY-MM-DD/CR-20-deployment-config-and-production-readiness-review.md` |
| CR-21 | Pending | [Documentation consistency review](cr-21-documentation-consistency-review.md) | проверить, что docs не расходятся с кодом после review baseline. | `docs/reviews/YYYY-MM-DD/CR-21-documentation-consistency-review.md` |
| CR-22 | Pending | [Test suite quality review](cr-22-test-suite-quality-review.md) | проверить не только что тесты проходят, но что они ловят реальные regressions. | `docs/reviews/YYYY-MM-DD/CR-22-test-suite-quality-review.md` |
| CR-23 | Pending | [Performance and scalability review](cr-23-performance-and-scalability-review.md) | проверить obvious bottlenecks before commercialization. | `docs/reviews/YYYY-MM-DD/CR-23-performance-and-scalability-review.md` |
| CR-24 | Pending | [Final integration regression gate](cr-24-final-integration-regression-gate.md) | финально подтвердить, что review/fix cycle не сломал продукт. | `docs/reviews/YYYY-MM-DD/CR-24-final-integration-regression-gate.md` |

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

## Triage summary target

После выполнения review создать:

`docs/reviews/YYYY-MM-DD/triage-summary.md`

и обновить статусы в этой таблице.
