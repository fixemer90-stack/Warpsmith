---
title: "Code Review Remediation Plan"
parent: code-review
status: draft
priority: P0
source: triage-summary.md
scope: CR remediation after CR-24
---

# Code Review Remediation Plan

> **For Hermes:** Use `subagent-driven-development` or one focused implementation session per task. Do not batch unrelated fixes. Each task must end with tests, docs sync where applicable, and CR artifact/status updates.

**Goal:** turn the CR-00..CR-24 review result into an ordered remediation program that stabilizes canonical data, runtime state, core rules, replay/result truth, API/auth/persistence, and AI integration before re-running CR-24.

**Architecture:** fix foundations first. Canonical wiki data and runtime identity/state become the source of truth; validators and combat/gameplay consume that canonical layer; replay/result persists authoritative final state; API/auth/persistence hardening wraps the product boundary; AI integration is last so it uses stable movement/combat/game-state contracts.

**Tech stack:** Python 3.12, FastAPI, SQLite, Jinja2, Alpine.js, pytest, ruff, Warhammer 40k 10th edition rules.

## Non-negotiable separation rules

These are hard architectural boundaries for the whole remediation program:

- Display name != runtime identity.
  - Display names are UI/log labels only.
  - Runtime state, replay snapshots, damage, ownership, deaths, movement, charges, and result attribution must use stable runtime ids.
- Raw wiki data != runtime canonical data.
  - Wiki frontmatter/body is source input, not the object model consumed directly by validators/combat/game state.
  - The compiler/schema layer must normalize wiki data into canonical runtime records before game systems use it.
- AI decision != authoritative state mutation.
  - AI may propose actions/intents only.
  - Game-state/scenario engines validate and apply mutations; AI must not bypass movement, charge, combat, VP, ownership, or persistence invariants.
- Round snapshots != final result authority.
  - Round snapshots are replay timeline evidence.
  - The final result must come from an authoritative final state/result payload, with VP/winner/kills/losses derived from the same source.
- Tests passing != CR status closed.
  - Executable checks are necessary but not sufficient.
  - A finding is closed only when implementation, regression evidence, affected CR artifacts, `triage-summary.md`, and `code-review.md` are all updated.

## Dependency graph

| Phase                                             | Depends on | Unlocks                    |
| ------------------------------------------------- | ---------- | -------------------------- |
| 0. Canonical Data and Runtime State Stabilization | —          | 1                          |
| 1. Content Compiler and Schemas                   | 0          | 2, 3                       |
| 2. Roster Validator                               | 1          | 4                          |
| 3. Combat Math                                    | 1          | 4                          |
| 4. Game State, VP, Phase Invariants               | 2, 3       | 5                          |
| 5. Movement, Charge, Melee Identity               | 4          | 6                          |
| 6. Replay and Result Authoritative State          | 5          | 7, 8                       |
| 7. API, Auth, Persistence Hardening               | 6          | CR-24                      |
| 8. AI Integration                                 | 6          | CR-24                      |
| CR-24 Final Regression Gate                       | 7, 8       | Release readiness decision |

## Global rules for every phase

- Work in one phase at a time; do not start phase N+1 until phase N checkpoint passes.
- Write regression tests before production changes where feasible.
- Keep runtime identifiers separate from display names.
- No hardcoded faction/unit/detachment lists where wiki/API should be source of truth.
- After backend changes run at minimum the scoped tests plus:
  - `uv run ruff check .`
  - `uv run ruff format --check .`
  - `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/ -q`
- After JS/HTML changes also run:
  - `node -c web/static/team_builder.js`
  - `node -c web/static/scenario_setup.js`
  - `node -c web/static/battlefield_map.js`
  - Browser smoke for affected pages.
- Update relevant CR artifact(s), `code-review.md`, and `triage-summary.md` after each phase.
- Each phase is not complete until its phase completion artifact is written and linked from the affected review metadata.

## Phase completion artifact

At the end of every phase, update all three metadata surfaces:

- `docs/reviews/2026-05-10/triage-summary.md`
- affected `docs/requirements/code-review/CR-XX.md` artifacts, using the actual lowercase file names in this directory
- `docs/requirements/code-review/code-review.md`

Each phase update must include this required shape:

- phase number and phase title
- task IDs completed, for example `0.1`, `0.2`, `0.3`
- CR findings closed, grouped by CR id and finding id/title where available
- CR findings still open, grouped by CR id and finding id/title where available
- accepted debt, if any, with owner/rationale/revisit trigger; otherwise state `none`
- test commands run, including exit status and short result summary
- lint/format commands run, including exit status and short result summary
- browser/API smoke evidence where applicable, including URL, endpoint, replay id, screenshot path, or curl output summary
- remaining blockers before the next phase; otherwise state `none`

Minimum markdown template for the phase completion artifact:

```markdown
### Phase N completion — <phase title>

- Completed tasks: <task ids>
- Closed findings:
  - CR-XX: <finding id/title or summary>
- Still open:
  - CR-YY: <finding id/title or summary>
- Accepted debt: <none | explicit accepted debt entry>
- Tests run:
  - `<command>` → <exit code/result>
- Lint/format run:
  - `<command>` → <exit code/result>
- Browser/API smoke evidence:
  - <none | URL/endpoint/replay id/evidence summary>
- Remaining blockers before next phase: <none | blockers>
```

Do not mark a phase complete in `code-review.md` unless this artifact exists in `triage-summary.md` and the affected CR artifacts have been updated. This prevents CR-24 from passing executable gates while review metadata remains stale.

## Phase 0 — Canonical Data + Runtime State Stabilization

**Purpose:** establish stable runtime identity and canonical game state before touching validators, combat, movement, replay, or AI.

**Primary CRs:** CR-05, CR-06, CR-12, CR-14, CR-20.

**Files likely touched:**
- `backend/state/game_state.py`
- `backend/engine/ai/autoplay.py`
- `backend/engine/replay.py`
- `backend/model/unit.py`
- `backend/loader/parser.py`
- `backend/loader/registry.py`
- `backend/db/database.py`
- `tests/test_game_state.py`
- `tests/test_autoplay.py`
- `tests/test_replay.py`
- `tests/test_loader.py`

### Task 0.1 — Define runtime unit identity contract

**Objective:** every runtime unit has a stable unique id independent of display name.

**Acceptance criteria:**
- [ ] Runtime ids include player/roster scope, e.g. `p1:boyz:0` or equivalent.
- [ ] Display name remains available separately for UI/log text.
- [ ] Duplicate unit names across players no longer collide in state maps.
- [ ] Tests cover same-name mirrored armies.

**Verification:**
- `uv run python -m pytest tests/test_game_state.py tests/test_autoplay.py -q`

### Task 0.2 — Normalize GameState serialization boundaries

**Objective:** make snapshots, replay payloads, and API payloads use one state shape.

**Acceptance criteria:**
- [ ] `_snapshot_state()` includes runtime id, display name, owner/player id, position, wounds/models, status flags, and VP.
- [ ] Round snapshots and final snapshots use the same keys.
- [ ] Existing UI consumers still receive display names.

**Verification:**
- `uv run python -m pytest tests/test_replay.py tests/test_round_viewer.py tests/test_result_screen.py -q`

### Task 0.3 — Stop destructive DB/replay behavior before further fixes

**Objective:** remove data-loss risks that can hide later regressions.

**Acceptance criteria:**
- [ ] Startup/migration path does not delete replay data.
- [ ] Replay save does not overwrite an existing replay unless explicitly requested.
- [ ] Fixed seed no longer equals durable replay identity.

**Verification:**
- `uv run python -m pytest tests/test_replay.py tests/test_db*.py -q`

### Checkpoint 0

- [ ] Runtime unit identity is unique and tested.
- [ ] No replay overwrite/data-loss regression.
- [ ] Full tests pass.

## Phase 1 — Content compiler / schemas

**Purpose:** make wiki/frontmatter content compile into validated schemas before runtime use.

**Primary CRs:** CR-06, CR-11, CR-12, CR-21.

**Files likely touched:**
- `backend/model/unit.py`
- `backend/loader/parser.py`
- `backend/loader/registry.py`
- `wiki/`
- `tests/test_parser.py`
- `tests/test_registry.py`
- new: `tests/test_content_contracts.py`

### Task 1.1 — Create content contract tests

**Objective:** fail fast on invalid wiki content that breaks runtime logic.

**Acceptance criteria:**
- [ ] Unit files compile into typed Unit objects without silent defaults for required gameplay fields.
- [ ] Points, squad_size, model_count, weapons, faction, tags, keywords, OC/LD/SV/T/W/M are validated.
- [ ] Known allowed exceptions are explicit and documented in test data.

**Verification:**
- `uv run python -m pytest tests/test_content_contracts.py -q`

### Task 1.2 — Replace unsafe/stale cache behavior

**Objective:** registry cache must not load unsafe pickle or stale content after wiki changes.

**Acceptance criteria:**
- [ ] No unsafe pickle cache path for untrusted content.
- [ ] Cache invalidates on source file mtime/content hash or is disabled in tests.
- [ ] Tests cover adding/changing a wiki file.

**Verification:**
- `uv run python -m pytest tests/test_registry.py tests/test_content_contracts.py -q`

### Task 1.3 — Compile squad/points metadata consistently

**Objective:** one canonical squad metadata shape feeds roster validation and UI.

**Acceptance criteria:**
- [ ] `unit.squad_size` from YAML/frontmatter is authoritative.
- [ ] `model_count` is not used as roster min/max replacement.
- [ ] Single-model vehicles and transport capacity cannot be misread as squad size.

**Verification:**
- `uv run python -m pytest tests/test_parser.py tests/test_roster*.py -q`

### Checkpoint 1

- [ ] Wiki content compiles with explicit errors.
- [ ] No unsafe/stale cache risk.
- [ ] Roster validator can rely on canonical metadata.

## Phase 2 — Roster validator

**Purpose:** make roster validation authoritative and shared across API, generated rosters, saved rosters, and UI expectations.

**Primary CRs:** CR-12, CR-16, CR-17, CR-19.

**Files likely touched:**
- `backend/state/roster.py`
- `web/routes/api_rosters.py`
- `web/static/team_builder.js`
- `web/templates/team_builder.html`
- `tests/test_roster*.py`
- `tests/test_api_rosters.py`

### Task 2.1 — Lock the canonical PTS formula

**Objective:** backend and frontend use the same squad cost formula.

**Acceptance criteria:**
- [ ] Backend formula: `(points / minSquad + loadoutPts) * squadSize + nobPts`.
- [ ] `totalPts` sums stored total squad `pts` values.
- [ ] Tests cover Boyz/Nobz/single-model vehicles and loadout/nob upgrades.

**Verification:**
- `uv run python -m pytest tests/test_roster*.py -q`
- Browser/API smoke if frontend changed.

### Task 2.2 — Enforce exactly one Warlord when required

**Objective:** saved and generated rosters have valid Warlord semantics.

**Acceptance criteria:**
- [ ] Multiple Characters require explicit Warlord.
- [ ] Generated roster sets exactly one valid `is_warlord: true`.
- [ ] Team Builder UI visibly exposes Warlord selection and warnings.

**Verification:**
- `uv run python -m pytest tests/test_roster*.py tests/test_api_rosters.py -q`
- Browser smoke `/team-builder` for crown/warning/save-disabled state.

### Task 2.3 — Enforce plan/feature gates consistently

**Objective:** Free/Premium roster limits cannot be bypassed through duplicate/import paths.

**Acceptance criteria:**
- [ ] Create, duplicate, import/generate-save paths share one validator.
- [ ] Free limit matches product requirement and UI.
- [ ] Public roster creation respects feature flags.

**Verification:**
- `uv run python -m pytest tests/test_api_rosters.py tests/test_billing*.py -q`

### Checkpoint 2

- [ ] Roster validation is shared and test-covered.
- [ ] UI/API/generated roster behavior matches.

## Phase 3 — Combat math

**Purpose:** fix core hit/wound/save/damage/FNP math before tuning gameplay or AI.

**Primary CRs:** CR-07, CR-11.

**Files likely touched:**
- `backend/engine/combat.py`
- `backend/engine/modifiers.py`
- `backend/engine/scenario.py`
- `tests/test_combat*.py`
- `tests/test_modifiers.py`

### Task 3.1 — Fix natural 6 / Lethal Hits semantics

**Objective:** natural 6 auto-wounds only when Lethal Hits applies.

**Acceptance criteria:**
- [ ] Plain natural 6 to hit does not auto-wound.
- [ ] Lethal Hits natural 6 does auto-wound.
- [ ] Tests distinguish both paths.

**Verification:**
- `uv run python -m pytest tests/test_combat*.py tests/test_modifiers.py -q`

### Task 3.2 — Fix AP/save application and Devastating Wounds

**Objective:** AP and Devastating Wounds follow one consistent 10e-compatible path.

**Acceptance criteria:**
- [ ] AP is applied exactly once.
- [ ] Cover/save modifiers are applied at the correct stage.
- [ ] Devastating Wounds behavior is explicit and tested.

**Verification:**
- `uv run python -m pytest tests/test_combat*.py tests/test_terrain*.py -q`

### Task 3.3 — Fix Sustained Hits resolution

**Objective:** extra hits are resolved as real hit results, not dropped/no-op metadata.

**Acceptance criteria:**
- [ ] Sustained Hits adds correct additional hits.
- [ ] Downstream wound/save/damage counts include the extra hits.

**Verification:**
- `uv run python -m pytest tests/test_modifiers.py tests/test_combat*.py -q`

### Checkpoint 3

- [ ] Focused combat tests pass.
- [ ] Existing scenario tests still pass.

## Phase 4 — Game state / VP / phase invariants

**Purpose:** lock 10e phase flow, CP/VP, battle-shock, objective control, and end-game invariants.

**Primary CRs:** CR-08, CR-10, CR-14, CR-24.

**Files likely touched:**
- `backend/state/game_state.py`
- `backend/state/mission.py`
- `backend/engine/scenario.py`
- `backend/engine/ai/autoplay.py`
- `tests/test_game_state.py`
- `tests/test_scenario.py`
- `tests/test_mission*.py`
- `tests/test_autoplay.py`

### Task 4.1 — Assert 5-phase 10e loop invariants

**Objective:** Command -> Movement -> Shooting -> Charge -> Fight only.

**Acceptance criteria:**
- [ ] GamePhase has exactly 5 members.
- [ ] Battle-shock runs in Command, not separate Morale.
- [ ] Round increments after Fight only.

**Verification:**
- `uv run python -m pytest tests/test_game_state.py tests/test_scenario.py -q`

### Task 4.2 — Lock CP and battle-shock reset semantics

**Objective:** CP starts at 0, +1/round, relevant flags reset at correct times.

**Acceptance criteria:**
- [ ] No Warlord CP bonus.
- [ ] `is_battle_shocked` clears in Command only.
- [ ] `has_advanced` resets at new round.

**Verification:**
- `uv run python -m pytest tests/test_game_state.py tests/test_scenario.py -q`

### Task 4.3 — Lock VP, objectives, mission normalization, Battle Ready

**Objective:** VP source is deterministic and 10e-aligned.

**Acceptance criteria:**
- [ ] Mission names normalize spaces and hyphens.
- [ ] Dynamic objectives: Only War 3, Take and Hold/Purge the Foe 5.
- [ ] Battle Ready +10 VP applied exactly once and visible in final authoritative state.
- [ ] Game ends by rounds/wipe/mission cap, not early VP>=10.

**Verification:**
- `uv run python -m pytest tests/test_mission*.py tests/test_autoplay.py tests/test_result_screen.py -q`

### Checkpoint 4

- [ ] Game loop invariants pass.
- [ ] VP/final score agrees across runtime, API, and planned replay contract.

## Phase 5 — Movement / charge / melee identity

**Purpose:** make movement, charge, engagement, melee damage, and unit identity coherent before replay/result and AI.

**Primary CRs:** CR-09, CR-11, CR-14, CR-15.

**Files likely touched:**
- `backend/engine/scenario.py`
- `backend/state/game_state.py`
- `backend/state/map.py`
- `backend/engine/ai/decision.py`
- `tests/test_movement*.py`
- `tests/test_scenario.py`
- `tests/test_autoplay.py`

### Task 5.1 — Fix charge destination and engagement identity

**Objective:** charge moves to adjacent legal cell and marks scoped units as engaged.

**Acceptance criteria:**
- [ ] Charge never attempts to occupy enemy cell.
- [ ] Engagement uses runtime ids, not names.
- [ ] Same-name mirrored units can engage independently.

**Verification:**
- `uv run python -m pytest tests/test_movement*.py tests/test_scenario.py -q`

### Task 5.2 — Fix melee target selection and damage logging

**Objective:** melee resolves adjacent targets and logs parsable damage with actor/target identity.

**Acceptance criteria:**
- [ ] Adjacent melee attacks resolve.
- [ ] Damage log/event uses `hits ... for ... damage` or structured equivalent.
- [ ] Summary attribution is not name-based.

**Verification:**
- `uv run python -m pytest tests/test_scenario.py tests/test_result_screen.py -q`

### Task 5.3 — Fix terrain/LoS movement-related blockers

**Objective:** terrain/LoS cache and cover integration do not corrupt movement/shooting assumptions.

**Acceptance criteria:**
- [ ] `set_terrain()` invalidates LoS cache.
- [ ] Cover helper argument order is correct.
- [ ] AP0 cover cap is enforced.

**Verification:**
- `uv run python -m pytest tests/test_terrain*.py tests/test_scenario.py -q`

### Checkpoint 5

- [ ] Melee units can move, charge, engage, and deal damage.
- [ ] Duplicate unit names do not corrupt movement/melee/result attribution.

## Phase 6 — Replay/result authoritative state

**Purpose:** make persisted replay and result pages derive from one authoritative final state.

**Primary CRs:** CR-14, CR-18, CR-24.

**Files likely touched:**
- `backend/engine/ai/autoplay.py`
- `backend/engine/replay.py`
- `web/routes/api_replays.py`
- `web/static/replay_viewer.js`
- `web/static/result_chart.js`
- `web/templates/result.html`
- `tests/test_replay.py`
- `tests/test_round_viewer.py`
- `tests/test_result_screen.py`

### Task 6.1 — Persist authoritative final snapshot

**Objective:** final replay/result state includes all post-game scoring and final unit state.

**Acceptance criteria:**
- [ ] Battle Ready VP is included in final persisted state.
- [ ] `/api/results/{game_id}` and `/result/{game_id}` show same final VP.
- [ ] VP chart/stat cards use the same authoritative source.

**Verification:**
- `uv run python -m pytest tests/test_replay.py tests/test_result_screen.py -q`
- Deterministic generated replay smoke.

### Task 6.2 — Fix event parsing and summary attribution

**Objective:** result summaries derive from scoped ids/structured events, not ambiguous display names.

**Acceptance criteria:**
- [ ] Kills/damage/charges attributed correctly in same-faction/same-name games.
- [ ] VP logs with totals and Battle Ready parse as VP events or are represented by structured final state.
- [ ] Player 2 charge card can show non-zero normal events.

**Verification:**
- `uv run python -m pytest tests/test_result_screen.py tests/test_replay.py -q`

### Task 6.3 — Add repeatable final gate smoke script

**Objective:** replace ad-hoc `/tmp` CR-24 replay probes with repo-owned smoke.

**Acceptance criteria:**
- [ ] Script creates deterministic isolated replay/result smoke.
- [ ] Script asserts runtime VP, API VP, and result payload/page VP match.
- [ ] Script uses isolated DB or cleans up its data.

**Files likely touched:**
- Create: `scripts/smoke_final_gate.py`
- Test: `tests/test_final_gate_smoke.py` or direct script invocation documented in CR-24.

**Verification:**
- `uv run python scripts/smoke_final_gate.py`

### Checkpoint 6

- [ ] Replay/result identity and final state are authoritative.
- [ ] CR-24 result VP bug is fixed and covered.

## Phase 7 — API/auth/persistence hardening

**Purpose:** close release blockers around public boundaries, auth/ownership, billing gates, deployment safety, and DB persistence.

**Primary CRs:** CR-02, CR-03, CR-04, CR-05, CR-13, CR-19, CR-20, CR-22.

**Files likely touched:**
- `backend/auth/__init__.py`
- `backend/auth/providers/*`
- `backend/billing/*`
- `backend/db/database.py`
- `web/routes/api.py`
- `web/routes/api_rosters.py`
- `web/routes/api_replays.py`
- `web/routes/auth.py`
- `main.py`
- `tests/test_auth*.py`
- `tests/test_billing*.py`
- `tests/test_api*.py`
- `tests/test_deployment*.py`

### Task 7.1 — Fail closed on secrets/JWT/webhook config

**Objective:** production cannot run with insecure fallback secrets or unsigned billing webhooks.

**Acceptance criteria:**
- [ ] HOSTING/production requires explicit JWT secret.
- [ ] Stripe webhook rejects unsigned/invalid events.
- [ ] No secret values are printed in logs or committed test files.

**Verification:**
- `uv run python -m pytest tests/test_auth*.py tests/test_billing*.py tests/test_deployment*.py -q`

### Task 7.2 — Enforce ownership on roster/replay/subscription APIs

**Objective:** users can only read/write their own protected resources.

**Acceptance criteria:**
- [ ] Roster CRUD checks owner.
- [ ] Replay list/detail respects public/private/owner policy.
- [ ] Subscription/portal endpoints are user-bound.

**Verification:**
- `uv run python -m pytest tests/test_api_rosters.py tests/test_api_replays.py tests/test_auth*.py -q`

### Task 7.3 — Enforce billing/feature gates consistently

**Objective:** Free/Premium constraints match product and cannot be bypassed.

**Acceptance criteria:**
- [ ] Auto-play quota/auth gate is enforced or explicitly disabled from paid claims.
- [ ] Free roster limit matches UI/product requirement.
- [ ] `/api/me` exposes feature flags/trial state needed by UI.
- [ ] `require_tier()` is implemented or removed from claims.

**Verification:**
- `uv run python -m pytest tests/test_billing*.py tests/test_api*.py -q`

### Task 7.4 — Production hardening pass

**Objective:** deployment route and runtime safety issues are closed.

**Acceptance criteria:**
- [ ] Public `/sentry-debug` is disabled outside local/dev explicit mode.
- [ ] CSP decision is documented and tested; if enabled, browser still works.
- [ ] Rate limiting is production-appropriate or accepted with explicit deployment guardrail.
- [ ] Error responses include request id where expected.

**Verification:**
- `uv run python -m pytest tests/test_deployment*.py tests/test_api*.py -q`

### Checkpoint 7

- [ ] Auth/ownership/billing/production P0 blockers are closed.
- [ ] Full tests pass.
- [ ] Local server `/api/health` smoke passes.

## Phase 8 — AI integration

**Purpose:** wire AI decisions into already-stable movement/combat/game-state contracts.

**Primary CRs:** CR-15, CR-17.

**Files likely touched:**
- `backend/engine/ai/decision.py`
- `backend/engine/ai/faction_ai.py`
- `backend/engine/ai/deployment.py`
- `backend/engine/ai/autoplay.py`
- `backend/engine/scenario.py`
- `wiki/factions/*.md`
- `tests/test_faction_ai.py`
- `tests/test_ai_decision.py`
- `tests/test_autoplay.py`

### Task 8.1 — Use decision engine in live scenario phases

**Objective:** F3.1/F3.2 decision logic is not dead code.

**Acceptance criteria:**
- [ ] Movement/shooting/charge phases call decision engine or a documented adapter.
- [ ] `EvaluationContext.faction_profile` reaches scoring functions.
- [ ] Tests prove a faction profile changes decisions.

**Verification:**
- `uv run python -m pytest tests/test_ai_decision.py tests/test_faction_ai.py tests/test_autoplay.py -q`

### Task 8.2 — Fix behavior overrides and target priorities

**Objective:** faction profile weights/overrides affect runtime behavior predictably.

**Acceptance criteria:**
- [ ] `action_override` is honored or removed from schema/docs.
- [ ] Target multipliers below 1.0 can de-prioritize targets.
- [ ] Behavior activation marks behavior used once as intended.

**Verification:**
- `uv run python -m pytest tests/test_faction_ai.py tests/test_ai_decision.py -q`

### Task 8.3 — Verify deployment objectives and faction styles

**Objective:** Orks, Tau, and AdMech exhibit distinct deployment/movement tendencies from profile weights.

**Acceptance criteria:**
- [ ] Orks melee units bias toward engagement.
- [ ] Tau ranged units prefer ranged positioning/targets.
- [ ] Deployment uses faction profile role preferences.

**Verification:**
- `uv run python -m pytest tests/test_autoplay.py tests/test_faction_ai.py -q`
- Deterministic scenario probes with fixed seed.

### Checkpoint 8

- [ ] AI is integrated into live autoplay/scenario paths.
- [ ] Faction styles are observable and test-covered.

## Final CR-24 re-run

After phases 0-8:

1. Reconcile CR report counts:
   - Normalize CR frontmatter/counts or regenerate `code-review.md` from reports.
2. Run final static gates:
   - `uv run ruff check .`
   - `uv run ruff format --check .`
   - `node -c web/static/team_builder.js`
   - `node -c web/static/scenario_setup.js`
   - `node -c web/static/battlefield_map.js`
3. Run full tests:
   - `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/ -q`
4. Start server without reload:
   - `uv run python3 -c "import uvicorn; uvicorn.run('main:app', host='127.0.0.1', port=8000, reload=False)"`
5. Check health:
   - `curl -i -sS http://127.0.0.1:8000/api/health`
6. Browser smoke:
   - `/`
   - `/team-builder`
   - `/scenario-setup`
   - `/my-rosters`
   - `/result/<generated_game_id>`
7. Run final result consistency smoke:
   - `uv run python scripts/smoke_final_gate.py`
8. Update:
   - `docs/reviews/2026-05-10/triage-summary.md`
   - `docs/requirements/code-review/code-review.md`
   - affected CR artifacts
   - docs/indexes if feature/code docs changed.

## Exit criteria

- [ ] P0 release blocker group has zero open Critical/Important items.
- [ ] P1 core correctness group has zero open Critical items and all Important items fixed or explicitly accepted with guardrails.
- [ ] P2 important debt is either fixed or listed in Accepted/postponed with owner/date/guardrail.
- [ ] Final CR-24 gate passes.
- [ ] `triage-summary.md` and `code-review.md` counts match the CR artifacts.
- [ ] Full tests/lint/browser smoke evidence is recorded in the final CR-24 report.
