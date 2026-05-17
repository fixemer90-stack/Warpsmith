---
title: "CR-01 — Requirements and spec alignment map"
status: request-changes
review_task: CR-01
date: 2026-05-09
source: ../../requirements/code-review/cr-01-requirements-and-spec-alignment-map.md
---

# CR-01 — Requirements and spec alignment map

## Verdict

**REQUEST CHANGES / DOC ALIGNMENT REQUIRED**

The project has enough implementation and test coverage to proceed with domain CR tasks, but the requirements layer is not fully aligned. Several source-of-truth documents disagree about feature numbering, completion percentages, UI map technology, progressive disclosure modes, auth protection semantics, and monetization readiness.

This CR does not block continuing with CR-02/CR-03, but it marks documentation/spec alignment as requiring changes before final CR-24 release gate.

## Executive summary

Inputs reviewed:

- `docs/requirements/SRS.md`
- `docs/requirements/UX.md`
- `docs/features/Features_index.md`
- `docs/architecture/C4.md`
- `ROADMAP.md`
- Feature specs under `docs/features/*.md`
- Test inventory under `tests/test_*.py`
- Known code paths from CR-00 and current architecture map

Verified inventory:

- Feature spec files: `62`
- Feature spec statuses:
  - `done`: 53
  - `pending`: 8
  - `in-progress`: 1
- Test files: `41`
- Pytest collection from CR-00: `457 tests collected`

## Critical findings

None.

## Important findings

### Important 1 — Roadmap and Features_index disagree on Phase 2/Phase 3 scope

Evidence:

- `docs/features/Features_index.md` says Phase 2 has `19 features, ~123 часов, ✅ 68%`.
- `ROADMAP.md` says Phase 2 has `14 features (13 done, 1 pending)` and summary row `14 / ~72ч / 93%`.
- `docs/features/Features_index.md` Phase 3 uses F3.4/F3.5/F3.6/F3.7 for deployment/autoplay/replay/round-viewer/result, while `ROADMAP.md` uses F3.3/F3.4/F3.5/F3.6/F3.7 and says F3.3 is in-progress.

Impact:

- Review tasks cannot use roadmap status as a reliable source of truth without cross-checking `docs/features/Features_index.md` and individual feature specs.
- CR-15 and CR-21 must resolve the F3.3/F3.4 numbering/status mismatch.

### Important 2 — SRS still says Scenario Setup uses Canvas map, while accepted implementation is SVG strategic map

Evidence:

- `docs/requirements/SRS.md` FR-2.3: `Canvas-отображение карты`.
- `docs/features/Features_index.md` marks F4.14 strategic battlefield map done and F4.5/F4.10 as superseded.
- `docs/architecture/C4.md` describes Scenario Setup as SVG battlefield map.

Impact:

- SRS is stale for map implementation and can mislead CR-17.
- CR-21 should update SRS to say strategic SVG map; Canvas remains for replay/round-viewer only.

### Important 3 — UX draft describes three Progressive Disclosure modes, implementation/docs describe two modes

Evidence:

- `docs/requirements/UX.md` defines Beginner / Intermediate / Expert.
- Project memory and feature docs describe Beginner / Expert only, with default Expert.
- Tests include `test_progressive_disclosure.py`, but CR-01 did not deep-review implementation; CR-18/CR-21 should reconcile.

Impact:

- UX source is stale or aspirational.
- Reviewers must not treat Intermediate mode as implemented unless CR-18 proves otherwise.

### Important 4 — SRS auth requirement overstates `/api/*` protection

Evidence:

- `docs/requirements/SRS.md` FR-5.5 says `/api/*` endpoints check JWT via `Depends(get_current_user)`.
- Current API surface includes intentionally public endpoints such as health, units, factions, detachments, map tiles, simulate-like utility endpoints, and public browsing routes.

Impact:

- CR-03/CR-04 must review endpoint-by-endpoint auth/authorization, not blanket `/api/*`.
- SRS should distinguish public read APIs from user-owned mutation APIs.

### Important 5 — Monetization requirements are broader than current implementation

Evidence:

- SRS FR-7 describes Stripe checkout, webhook, portal, feature gates, ads, premium exports, downgrade handling.
- Architecture and endpoints docs currently describe billing stubs and Feature Gate scaffolding.
- Feature specs only include `F6.7 — Premium Trial` as pending; Phase 6 roadmap has broader pending items.

Impact:

- CR-19 must treat billing as incomplete/stubbed unless code proves otherwise.
- Requirements should label Stripe/ads/export gates as pending, not production-ready.

## Suggestions

1. Promote `Features_index.md` + individual feature specs as the feature-level source of truth, and treat `ROADMAP.md` as planning/status visualization until CR-21 reconciles it.
2. Add a short `Source of truth` note to SRS or README: SRS is product-level, feature specs are implementation-level, Swagger/OpenAPI is API schema source.
3. Add traceability IDs from SRS FR-* to feature specs where missing, especially auth, monetization, deployment, and UI flows.
4. For pending specs F2.14/F2.15/F2.16/F2.17/F2.18/F3.10/F3.11/F6.7, mark review risk as `Known gap / pending feature`, not a code defect.

## Requirements coverage map

| Feature / Requirement | Source requirement | Primary code paths | Tests | Review owner | Risk |
|---|---|---|---|---|---|
| Team Builder core | SRS FR-1.1–FR-1.9, F2.11, F4.2, F4.12 | `web/templates/team_builder.html`, `web/static/team_builder.js`, `web/static/unit_modal.js`, `web/routes/api.py`, `web/routes/api_rosters.py`, `backend/state/roster.py` | `test_team_builder.py`, `test_unit_modal.py`, `test_roster.py`, `test_rosters.py`, `test_generate_roster.py` | CR-12, CR-16 | Medium — complex frontend/backend contract, explicit Warlord and PTS edge cases |
| Roster validation / persistence | SRS FR-1.5–FR-1.8, FR-5.7, F2.9, F2.10, F4.12 | `backend/state/roster.py`, `backend/db/database.py`, `web/routes/api_rosters.py`, `web/static/my_rosters.js`, `web/templates/my_rosters.html` | `test_roster.py`, `test_rosters.py`, `test_generate_roster.py` | CR-04, CR-05, CR-12 | Medium — ownership/auth and JSON column parsing are recurring risks |
| Detachment picker/data | SRS FR-1.9, F4.3 | `web/routes/api.py`, `web/routes/api_detachments.py`, `backend/loader/registry.py`, `web/templates/partials/detachment_picker.html`, `web/static/detachment_picker.js` | `test_detachment_picker.py` | CR-06, CR-13, CR-16 | Medium — duplicate route ownership documented |
| Unit browser/modal/icons | UX sections 1, 2, 6; F4.1, F4.2, F4.7, F4.8 | `web/routes/api.py`, `web/templates/faction_browser.html`, `web/static/faction_browser.js`, `web/templates/partials/unit_modal.html`, `web/static/unit_modal.js`, `backend/loader/icon_map.py` | `test_faction_browser.py`, `test_unit_modal.py`, `test_tooltips.py`, `test_icon_map.py` | CR-06, CR-16, CR-18 | Medium — all tags must be shown verbatim; no filtering/dedup |
| Scenario Setup / battlefield map | SRS FR-2.1–FR-2.5, F4.14, stale F4.5/F4.10 | `web/templates/scenario_setup.html`, `web/templates/partials/battlefield_map.html`, `web/static/scenario_setup.js`, `web/static/battlefield_map.js`, `web/routes/pages.py`, `web/routes/api.py` | `test_canvas_map.py`, `test_autoplay.py` | CR-17 | High — SRS still says Canvas; accepted implementation is SVG strategic map |
| Combat engine | SRS FR-4.3–FR-4.4, F1.1–F1.13 | `backend/model/unit.py`, `backend/model/weapon.py`, `backend/engine/dice.py`, `backend/engine/modifiers.py`, `backend/engine/combat.py`, `web/routes/api.py` | `test_unit.py`, `test_weapon.py`, `test_dice.py`, `test_modifiers.py`, `test_combat.py`, `test_weapon_keywords_phase2.py`, `test_pmf_chart.py` | CR-07 | Medium — broad rules surface, but good test coverage |
| Game state / phase loop | SRS FR-4.2, F2.1, F2.5, F2.6, F2.7 | `backend/state/game_state.py`, `backend/engine/scenario.py`, `backend/engine/stratagems.py` | `test_game_state.py`, `test_scenario.py`, `test_phase_transitions.py`, `test_f2_7_battle_shock_cp_stratagems.py` | CR-08 | Medium — 10e phase/CP/Battle-shock rules are sensitive |
| Movement / charge / melee | SRS FR-4.2, F4.11 | `backend/engine/scenario.py`, `backend/state/game_state.py`, `backend/state/map.py`, `backend/engine/ai/decision.py` | `test_scenario.py`, `test_autoplay.py`, `test_ai_decision.py` | CR-09 | High — recurring bugs around occupied cells, adjacency, melee log parsing |
| Missions / objectives / VP | SRS FR-2.1, FR-3.4, F2.4, F2.8, F2.15 pending | `backend/state/mission.py`, `backend/state/game_state.py`, `backend/engine/scenario.py`, `backend/engine/ai/autoplay.py` | `test_mission.py`, `test_result_screen.py`, `test_round_viewer.py`, `test_autoplay.py` | CR-10 | Medium — pending primary/secondary missions are known gaps |
| Terrain / cover / LoS | SRS FR-2.2–FR-2.3, F2.2, F2.3, F2.13, F2.18 pending | `backend/state/map.py`, `backend/state/line_of_sight.py`, `backend/engine/combat.py`, `wiki/raw/papers/Terrain.md` | `test_map.py`, `test_line_of_sight.py`, `test_combat.py` | CR-11 | High — F2.13 is simplified; F2.18 full 10e terrain remains pending |
| AI decision/faction/deployment | SRS FR-4.1, FR-4.5, F3.1, F3.2, F3.4/F3.3 mismatch, F3.10/F3.11 pending | `backend/engine/ai/decision.py`, `backend/engine/ai/faction_ai.py`, `backend/engine/ai/deployment.py`, `backend/engine/ai/autoplay.py`, `wiki/factions/*.md` | `test_ai_decision.py`, `test_faction_ai.py`, `test_deployment_ai.py`, `test_autoplay.py` | CR-15 | High — roadmap/spec numbering mismatch and army-rule pending gaps |
| Autoplay / replay / result | SRS FR-3.1–FR-3.6, F3.5/F3.6/F3.7/F3.8, F4.13 | `backend/engine/ai/autoplay.py`, `backend/engine/replay.py`, `web/routes/api_replays.py`, `web/templates/result.html`, `web/templates/round_viewer.html`, `web/static/replay_viewer.js`, `web/static/result_chart.js` | `test_autoplay.py`, `test_replay.py`, `test_parse_log_events.py`, `test_result_screen.py`, `test_round_viewer.py` | CR-14 | Medium — log parsing and summary ownership are sensitive |
| API route surface | SRS API implications, C4, `docs/api/endpoints.md` | `main.py`, `web/routes/api.py`, `web/routes/api_rosters.py`, `web/routes/api_replays.py`, `web/routes/api_detachments.py`, `web/routes/auth.py`, `backend/billing/webhooks.py` | route-specific tests across suite | CR-13 | Medium — route ordering and duplicate detachment route ownership |
| Auth/session/OAuth | SRS FR-5.1–FR-5.16 | `backend/auth/`, `backend/auth/providers/`, `web/routes/auth.py`, `main.py`, `backend/db/database.py` | authentication coverage partially in `test_rosters.py`, `test_security_headers.py`, route tests; dedicated auth test coverage needs CR-03 check | CR-03, CR-04 | High — SRS overstates `/api/*` protection; endpoint-by-endpoint authorization needed |
| Billing / tiers / ads | SRS FR-7.1–FR-7.10, Phase 6, F6.7 pending | `backend/billing/plans.py`, `backend/billing/webhooks.py`, `backend/auth/dependencies.py`, templates for pricing/base pages | likely sparse; CR-19 must inventory | CR-19 | High — mostly stubs/pending commercialization work |
| Deployment / production readiness | SRS NFRs, F5.1–F5.7 | `Dockerfile`, `docker-compose.yml`, `railway.json`, `.github/workflows/*.yml`, `backend/security/headers.py`, `backend/logging_setup.py`, backup scripts | `test_docker.py`, `test_rate_limit.py`, `test_security_headers.py`, `test_logging.py`, `scripts/test_backup_system.py` | CR-20 | Medium — production env and local env differ |
| Documentation consistency | SRS, UX, Features_index, C4, ROADMAP, README, DEV_INDEX, AGENTS | `docs/**/*.md`, `README.md`, `ROADMAP.md`, `ROADMAP.html`, `AGENTS.md` | docs scans; no dedicated pytest for docs consistency | CR-21 | High — multiple stale/mismatched docs found in CR-01 |
| Test suite quality | SRS NFR-3, all feature specs with `## Тесты` sections | `tests/`, `pyproject.toml` | `457 collected`, `41 test_*.py` | CR-22 | Medium — collection is strong, but regression quality must be reviewed |
| Performance/scalability | SRS NFR-1/NFR-2/NFR-3, wiki loader target, simulation target | `backend/loader/registry.py`, `backend/engine/ai/autoplay.py`, `backend/engine/scenario.py`, list APIs, frontend maps | `test_coverage.py`, performance assertions sparse | CR-23 | Medium/High — performance targets documented but need measurement |

## Pending feature specs / known gaps

| Feature | Status | Review handling |
|---|---|---|
| F2.14 Deep Strike | pending | Known gap; review only if code claims support |
| F2.15 Primary Missions | pending | Known gap; do not mark absence as bug outside planning |
| F2.16 Shooting Refinements | pending | Known gap; relevant to CR-07/CR-11 |
| F2.17 Secondary Missions | pending | Known gap; relevant to CR-10 |
| F2.18 Terrain Mechanics 10e | pending | Known gap; F2.13 remains simplified baseline |
| F3.10 Waaagh! | pending | Known gap; roadmap/spec/code should be checked in CR-15 |
| F3.11 FTGG + Markerlight | pending | Known gap; roadmap/spec/code should be checked in CR-15 |
| F6.7 Premium Trial | pending | Known gap; relevant to CR-19 |

## Tests-first alignment notes

The test suite has direct files for most implemented domains:

- Combat: `test_combat.py`, `test_modifiers.py`, `test_weapon_keywords_phase2.py`, `test_dice.py`, `test_weapon.py`, `test_unit.py`
- Game system: `test_game_state.py`, `test_map.py`, `test_line_of_sight.py`, `test_mission.py`, `test_scenario.py`, `test_phase_transitions.py`
- AI/autoplay: `test_ai_decision.py`, `test_faction_ai.py`, `test_deployment_ai.py`, `test_autoplay.py`
- Replay/result: `test_replay.py`, `test_parse_log_events.py`, `test_round_viewer.py`, `test_result_screen.py`
- UI/API: `test_team_builder.py`, `test_unit_modal.py`, `test_faction_browser.py`, `test_detachment_picker.py`, `test_canvas_map.py`, `test_progressive_disclosure.py`, `test_tooltips.py`, `test_synergy_hints.py`
- Production/security: `test_docker.py`, `test_rate_limit.py`, `test_security_headers.py`, `test_logging.py`
- Roster/user data: `test_roster.py`, `test_rosters.py`, `test_generate_roster.py`

Potential gaps to verify later:

- Dedicated auth/OAuth tests beyond roster authorization and security headers.
- Dedicated billing/feature-gate tests.
- Dedicated docs consistency tests for SRS/Roadmap/Features_index drift.
- Performance target tests for SRS NFR-1/NFR-2.

## Five-axis review notes

### Correctness

- Feature specs and tests are broad enough to proceed.
- Requirements status correctness is not fully reliable because roadmap and feature index disagree.

### Readability / simplicity

- Feature specs are understandable, but source-of-truth hierarchy is implicit.
- CR-21 should make this explicit to prevent future stale-doc churn.

### Architecture

- C4 architecture is more current than SRS for API modules, map architecture, Warlord, generated rosters, and terrain requirement context.
- API endpoint docs are current enough for CR-13.

### Security

- SRS auth language is too broad. Public vs protected endpoints must be reviewed individually.
- Billing/security requirements are mostly planning-level and need implementation verification.

### Performance

- Performance targets exist in SRS but are not yet mapped to measurable gates in this CR.
- CR-23 should add measurements for page load, wiki load, and autoplay duration.

## What is done well

- The project has feature specs for nearly every implemented domain.
- Tests are split by domain, which maps cleanly to CR task ownership.
- C4 and AGENTS capture many recent implementation details that are missing from older SRS/UX docs.

## Verification story

Commands/tools used:

- Read `docs/requirements/SRS.md`
- Read `docs/requirements/UX.md`
- Read `docs/features/Features_index.md`
- Read `docs/architecture/C4.md`
- Read `ROADMAP.md`
- Parsed `docs/features/f*.md` frontmatter/status with Python
- Listed `tests/test_*.py` with Python
- Used CR-00 baseline for test collection count and route inventory

Python inventory result:

```text
FEATURE_SPEC_FILES 62
STATUS_COUNTS {'done': 53, 'pending': 8, 'in-progress': 1}
TEST_FILES 41
```

## Completion

- Completed at: `2026-05-09`
- Verdict: `REQUEST CHANGES / DOC ALIGNMENT REQUIRED`
- Critical: `0`
- Important: `5`
- Suggestions: `4`
