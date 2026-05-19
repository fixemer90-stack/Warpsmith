     1|---
     2|title: "Full code review triage summary"
     3|date: 2026-05-10
     4|status: open
     5|verdict: not-release-ready
     6|source: docs/requirements/code-review/code-review.md
     7|scope: CR-00..CR-24
     8|---
     9|
    10|# Full code review triage summary
    11|
    12|## Verdict
    13|
    14|Not release-ready.
    15|
    16|CR-24 executable gates passed, but release readiness is blocked by unresolved code-review debt and one reproduced integration regression:
    17|
    18|- Official tracker state after CR-24: 25 CR artifacts, 1 Approved, 24 Request Changes, 38 Critical open, 112 Important open.
    19|- No Critical finding is accepted debt for release. Critical findings require fix + re-review.
    20|- Important findings require either fix + re-review or an explicit accepted-debt entry with owner, due date, and release impact.
    21|- CR-24 reproduced stale final VP in result/replay output: Battle Ready VP is included in runtime state but missing from the stored final round snapshot/result page.
    22|
    23|## Count reconciliation note
    24|
    25|The canonical release tracker is `docs/requirements/code-review/code-review.md` and currently reports 38 Critical / 112 Important open.
    26|
    27|A quick scan of per-CR artifacts found a mismatch against the tracker because some artifacts/reports use different count formats and several older reports do not expose machine-readable frontmatter. Before closing the review program, reconcile counts by normalizing every CR report with explicit `critical`, `important`, and `suggestions` frontmatter or by updating the execution index from the report artifacts in one scripted pass.
    28|
    29|## Release gates
    30|
    31|| Gate | Status | Evidence |
    32||---|---:|---|
    33|| Ruff lint | Pass | `uv run ruff check .` -> All checks passed |
    34|| Ruff format check | Pass | `uv run ruff format --check .` -> 98 files already formatted |
    35|| JS syntax | Pass | `node -c web/static/team_builder.js`, `scenario_setup.js`, `battlefield_map.js` |
    36|| Full pytest | Pass | 454 passed, 3 skipped, 33 warnings |
    37|| Local server health | Pass | `/api/health` -> 200, `{"status":"ok","version":"0.7.7"}` |
    38|| Browser smoke | Pass | `/`, `/team-builder`, `/scenario-setup`, `/my-rosters`, `/result/auto_242424` load without console errors |
    39|| Review debt gate | Fail | 38 Critical / 112 Important still open |
    40|| Result VP consistency | Fail | `/result/auto_242424` showed 28/4 while runtime result was 38/14 |
    41|
    42|
    43|## Phase 2 remediation re-check — 2026-05-18
    44|
    45|Task 2.2 Warlord semantics are complete after follow-up fixes. Keyword-only `CHARACTER` eligibility, Team Builder zero-eligible warning/save-disabled behavior, generated/API/backend validation parity, and regression coverage were re-verified. Phase 2 checkpoint is marked complete in the remediation plan.
    46|
    47|Verification:
    48|- `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_roster*.py tests/test_rosters.py tests/test_generate_roster.py tests/test_team_builder.py -q` → 82 passed, 48 warnings.
    49|- `uv run python -m pytest tests/ -q` → 604 passed, 3 skipped, 60 warnings.
    50|- Ruff lint/format and `git diff --check` clean for Task 2.2 code, tests, and docs.
    51|
    52|## Finding groups
    53|
    54|Remediation plan: [docs/requirements/code-review/remediation-plan.md](remediation-plan.md)
    55|
    56|All CR findings are triaged into exactly four groups. CR headings remain stable link targets from the execution index and CR artifacts.
    57|
    58|| Group | CRs | Release meaning |
    59||---|---|---|
    60|| P0 release blocker | CR-02, CR-03, CR-04, CR-05, CR-14, CR-19, CR-20, CR-22, CR-24 | Must be fixed before any release-ready verdict. These findings cover security/auth, ownership, data loss, paid-feature enforcement, production safety, result integrity, and tests for those blockers. |
    61|| P1 core correctness | CR-06, CR-07, CR-08, CR-09, CR-10, CR-11, CR-12, CR-13, CR-15, CR-16, CR-17, CR-18 | Core product correctness and integration. These can be worked after P0 is stabilized, but they still block a high-confidence simulator release unless explicitly narrowed. |
    62|| P2 important debt | CR-01, CR-21, CR-23 | Important debt that should be fixed before commercialization scale-up, or accepted with owner/date/guardrail if release scope is intentionally narrowed. |
    63|| Accepted / postponed | CR-00 | Items not currently blocking release. No Critical or Important finding is accepted as release debt yet; only CR-00 baseline suggestions are postponed as hygiene notes. |
    64|
    65|## P0 release blocker
    66|
    67|Must be fixed before any release-ready verdict. Critical findings cannot be accepted as debt. Important findings in this group also block release because they protect auth, persistence, billing, production safety, final result integrity, or regression confidence.
    68|
    69|### CR-02 — Static security and secrets scan
    70|
    71|- **Group:** P0 release blocker
    72|- **Counts:** C2 / I7 / S4
    73|- **Triage status:** Open
    74|- **Report:** [docs/reviews/2026-05-09/CR-02-static-security-and-secrets-scan.md](../2026-05-09/CR-02-static-security-and-secrets-scan.md)
    75|- **Next action:** Resolve secret/security findings first; rotate anything that may be real.
    76|
    77|### CR-03 — Auth and session review
    78|
    79|- **Group:** P0 release blocker
    80|- **Counts:** C1 / I5 / S3
    81|- **Triage status:** Open
    82|- **Report:** [docs/reviews/2026-05-09/CR-03-auth-and-session-review.md](../2026-05-09/CR-03-auth-and-session-review.md)
    83|- **Next action:** Fix auth/session blockers and add regression tests around login/logout/JWT cookie behavior.
    84|
    85|### CR-04 — Authorization and ownership review
    86|
    87|- **Group:** P0 release blocker
    88|- **Counts:** C2 / I3 / S3
    89|- **Triage status:** Open
    90|- **Report:** [docs/reviews/2026-05-09/CR-04-authorization-and-ownership-review.md](../2026-05-09/CR-04-authorization-and-ownership-review.md)
    91|- **Next action:** Fix roster/replay/subscription ownership boundaries.
    92|
    93|### CR-05 — Database and persistence review
    94|
    95|- **Group:** P0 release blocker
    96|- **Counts:** C1 / I6 / S4
    97|- **Triage status:** Open
    98|- **Report:** [docs/reviews/2026-05-09/CR-05-database-and-persistence-review.md](../2026-05-09/CR-05-database-and-persistence-review.md)
    99|- **Next action:** Fix persistence/data-loss risks before production deploy.
   100|
   101|### CR-14 — Autoplay, replay and result review
   102|
   103|- **Group:** P0 release blocker
   104|- **Counts:** C3 / I4 / S0
   105|- **Triage status:** Open
   106|- **Report:** [docs/reviews/2026-05-09/CR-14-autoplay-replay-and-result-review.md](../2026-05-09/CR-14-autoplay-replay-and-result-review.md)
   107|- **Next action:** Fix non-unique replay IDs, final VP snapshots, duplicate-name attribution, VP event parsing, result-card charge counts.
   108|
   109|### CR-19 — Billing, feature gate and subscription review
   110|
   111|- **Group:** P0 release blocker
   112|- **Counts:** C3 / I8 / S1
   113|- **Triage status:** Open
   114|- **Report:** [docs/reviews/2026-05-10/CR-19-billing-feature-gate-and-subscription-review.md](CR-19-billing-feature-gate-and-subscription-review.md)
   115|- **Next action:** Implement or explicitly disable commercialization promises: webhook signature, user-bound checkout/portal, auto-play gating, roster limits, tier features.
   116|
   117|### CR-20 — Deployment, config and production readiness review
   118|
   119|- **Group:** P0 release blocker
   120|- **Counts:** C2 / I7 / S1
   121|- **Triage status:** Open
   122|- **Report:** [docs/reviews/2026-05-10/CR-20-deployment-config-and-production-readiness-review.md](CR-20-deployment-config-and-production-readiness-review.md)
   123|- **Next action:** Fix replay-deleting migration, hardcoded JWT fallback, CSP/sentry/rate-limit/branch deployment risks.
   124|
   125|### CR-22 — Test suite quality review
   126|
   127|- **Group:** P0 release blocker
   128|- **Counts:** C2 / I9 / S2
   129|- **Triage status:** Open
   130|- **Report:** [docs/reviews/2026-05-10/CR-22-test-suite-quality-review.md](CR-22-test-suite-quality-review.md)
   131|- **Next action:** Add tests for blocking security/auth/billing/persistence/result regressions; remove weak/placeholder coverage.
   132|
   133|### CR-24 — Final integration regression gate
   134|
   135|- **Group:** P0 release blocker
   136|- **Counts:** C1 / I1 / S1
   137|- **Triage status:** Open
   138|- **Report:** [docs/reviews/2026-05-10/CR-24-final-integration-regression-gate.md](CR-24-final-integration-regression-gate.md)
   139|- **Next action:** Re-run after triage/remediation; current blocker is unresolved CR debt plus stale result VP smoke.
   140|
   141|## P1 core correctness
   142|
   143|Core simulator and UI/API correctness. Fix after P0 batches, then run focused deterministic probes plus full regression.
   144|
   145|### CR-06 — Wiki loader and parser review
   146|
   147|- **Group:** P1 core correctness
   148|- **Counts:** C1 / I4 / S1
   149|- **Triage status:** Open
   150|- **Report:** [docs/reviews/2026-05-09/CR-06-wiki-loader-and-parser-review.md](../2026-05-09/CR-06-wiki-loader-and-parser-review.md)
   151|- **Next action:** Fix unsafe cache/content validation gaps; reconcile unit files vs loaded units and zero/no-weapon data quality findings.
   152|
   153|### CR-07 — Combat engine review
   154|
   155|- **Group:** P1 core correctness
   156|- **Counts:** C3 / I4 / S1
   157|- **Triage status:** Open
   158|- **Report:** [docs/reviews/2026-05-09/CR-07-combat-engine-review.md](../2026-05-09/CR-07-combat-engine-review.md)
   159|- **Next action:** Fix combat rules: natural 6 auto-wounds without Lethal Hits, Devastating Wounds saves, AP double-apply, Sustained Hits resolution.
   160|
   161|### CR-08 — Game state and phase machine review
   162|
   163|- **Group:** P1 core correctness
   164|- **Counts:** C3 / I4 / S1
   165|- **Triage status:** Open
   166|- **Report:** [docs/reviews/2026-05-09/CR-08-game-state-and-phase-machine-review.md](../2026-05-09/CR-08-game-state-and-phase-machine-review.md)
   167|- **Next action:** Fix 10e phase/round/CP/battle-shock state-machine blockers with deterministic probes.
   168|
   169|### CR-09 — Movement, charge and melee review
   170|
   171|- **Group:** P1 core correctness
   172|- **Counts:** C3 / I3 / S0
   173|- **Triage status:** Open
   174|- **Report:** [docs/reviews/2026-05-09/CR-09-movement-charge-and-melee-review.md](../2026-05-09/CR-09-movement-charge-and-melee-review.md)
   175|- **Next action:** Fix melee movement/charge/melee damage integration so units can reliably engage and log damage.
   176|
   177|### CR-10 — Mission, objectives and VP review
   178|
   179|- **Group:** P1 core correctness
   180|- **Counts:** C2 / I4 / S0
   181|- **Triage status:** Open
   182|- **Report:** [docs/reviews/2026-05-09/CR-10-mission-objectives-and-vp-review.md](../2026-05-09/CR-10-mission-objectives-and-vp-review.md)
   183|- **Next action:** Fix scoring/objective/Battle Ready/winner consistency issues.
   184|
   185|### CR-11 — Terrain, cover and LoS review
   186|
   187|- **Group:** P1 core correctness
   188|- **Counts:** C3 / I4 / S0
   189|- **Triage status:** Open
   190|- **Report:** [docs/reviews/2026-05-09/CR-11-terrain-cover-and-los-review.md](../2026-05-09/CR-11-terrain-cover-and-los-review.md)
   191|- **Next action:** Fix cover argument order, AP0 cover cap, documented LoS blocking, LoS cache invalidation, and terrain integration tests.
   192|
   193|### CR-12 — Roster validation and points review
   194|
   195|- **Group:** P1 core correctness
   196|- **Counts:** C3 / I4 / S0
   197|- **Triage status:** Open
   198|- **Report:** [docs/reviews/2026-05-09/CR-12-roster-validation-and-points-review.md](../2026-05-09/CR-12-roster-validation-and-points-review.md)
   199|- **Next action:** Fix PTS/Warlord/squad size/battleline/generated roster validation gaps.
   200|
   201|### CR-13 — API route surface review
   202|
   203|- **Group:** P1 core correctness
   204|- **Counts:** C3 / I5 / S0
   205|- **Triage status:** Open
   206|- **Report:** [docs/reviews/2026-05-09/CR-13-api-route-surface-review.md](../2026-05-09/CR-13-api-route-surface-review.md)
   207|- **Next action:** Fix route/auth/frontend fetch/status-code contract issues after ownership/auth batch.
   208|
   209|### CR-15 — AI decision engine and faction profile review
   210|
   211|- **Group:** P1 core correctness
   212|- **Counts:** C3 / I4 / S0
   213|- **Triage status:** Open
   214|- **Report:** [docs/reviews/2026-05-09/CR-15-ai-decision-engine-and-faction-profile-review.md](../2026-05-09/CR-15-ai-decision-engine-and-faction-profile-review.md)
   215|- **Next action:** Wire F3.1/F3.2 decision engine into live phases; verify faction behavior overrides, target priorities, deployment objectives.
   216|
   217|### CR-16 — Team Builder frontend review
   218|
   219|- **Group:** P1 core correctness
   220|- **Counts:** C0 / I2 / S2
   221|- **Triage status:** Open
   222|- **Report:** [docs/reviews/2026-05-10/CR-16-team-builder-frontend-review.md](CR-16-team-builder-frontend-review.md)
   223|- **Next action:** Remove stale duplicate modal risk and replace placeholder modal tests with browser-visible assertions.
   224|
   225|### CR-17 — Scenario Setup and battlefield map frontend review
   226|
   227|- **Group:** P1 core correctness
   228|- **Counts:** C0 / I4 / S1
   229|- **Triage status:** Open
   230|- **Report:** [docs/reviews/2026-05-10/CR-17-scenario-setup-and-battlefield-map-frontend-review.md](CR-17-scenario-setup-and-battlefield-map-frontend-review.md)
   231|- **Next action:** Fix Scenario Setup/map/generated-opponent contracts beyond happy-path launch.
   232|
   233|### CR-18 — Pages/templates/navigation review
   234|
   235|- **Group:** P1 core correctness
   236|- **Counts:** C0 / I4 / S1
   237|- **Triage status:** Open
   238|- **Report:** [docs/reviews/2026-05-10/CR-18-pages-templates-navigation-review.md](CR-18-pages-templates-navigation-review.md)
   239|- **Next action:** Fix broken pricing CTA, shared helper CSS under Tailwind CDN, Progressive Disclosure localStorage failure path, and tests.
   240|
   241|## P2 important debt
   242|
   243|Important but not the first release-stop batch. These items need fix or explicit accepted-debt entries before commercialization scale-up.
   244|
   245|### CR-01 — Requirements and spec alignment map
   246|
   247|- **Group:** P2 important debt
   248|- **Counts:** C0 / I5 / S4
   249|- **Triage status:** Open
   250|- **Report:** [docs/reviews/2026-05-09/CR-01-requirements-and-spec-alignment-map.md](../2026-05-09/CR-01-requirements-and-spec-alignment-map.md)
   251|- **Next action:** Fix spec/docs alignment after code fixes; do not let stale specs define release readiness.
   252|
   253|### CR-21 — Documentation consistency review
   254|
   255|- **Group:** P2 important debt
   256|- **Counts:** C0 / I8 / S2
   257|- **Triage status:** Open
   258|- **Report:** [docs/reviews/2026-05-10/CR-21-documentation-consistency-review.md](CR-21-documentation-consistency-review.md)
   259|- **Next action:** Sync docs after fixes: feature specs, C4, indexes, ROADMAP, AGENTS, CHANGELOG.
   260|
   261|### CR-23 — Performance and scalability review
   262|
   263|- **Group:** P2 important debt
   264|- **Counts:** C0 / I7 / S3
   265|- **Triage status:** Open
   266|- **Report:** [docs/reviews/2026-05-10/CR-23-performance-and-scalability-review.md](CR-23-performance-and-scalability-review.md)
   267|- **Next action:** Fix or accept pagination/indexing/cache/sync-autoplay/telemetry risks before commercialization scale-up.
   268|
   269|## Accepted / postponed
   270|
   271|No Critical or Important finding is accepted as release debt yet. Accepted/postponed currently contains only baseline notes and future hygiene.
   272|
   273|### CR-00 — Inventory and baseline
   274|
   275|- **Group:** Accepted / postponed
   276|- **Counts:** C0 / I0 / S4
   277|- **Triage status:** Accepted as baseline notes
   278|- **Report:** [docs/reviews/2026-05-09/CR-00-inventory-and-baseline.md](../2026-05-09/CR-00-inventory-and-baseline.md)
   279|- **Next action:** Baseline captured. Keep suggestions as follow-up hygiene while fixing later CRs.
   280|
   281|
   282|## Accepted debt register
   283|
   284|No Critical or Important finding is accepted as debt yet.
   285|
   286|Use this table only after an explicit decision to defer a non-Critical item:
   287|
   288|| Finding / CR | Severity | Owner | Accepted until | Justification | Required guardrail |
   289||---|---|---|---|---|---|
   290|| _none_ | — | — | — | — | — |
   291|
   292|## Re-review checklist
   293|
   294|For each remediation batch:
   295|
   296|1. Fix only the findings in that batch; avoid mixing unrelated refactors.
   297|2. Add focused regression tests/probes that would have caught the original finding.
   298|3. Run scoped tests first, then full project gates:
   299|   - `uv run ruff check .`
   300|   - `uv run ruff format --check .`
   301|   - `node -c web/static/team_builder.js`
   302|   - `node -c web/static/scenario_setup.js`
   303|   - `node -c web/static/battlefield_map.js`
   304|   - `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/ -q`
   305|4. Update the relevant CR report/artifact with fixed/re-reviewed status.
   306|5. Update this triage summary and `docs/requirements/code-review/code-review.md` counts.
   307|6. After all P0/P1 release blockers are closed or explicitly accepted where allowed, re-run CR-24.
   308|
   309|## Phase 0 — Canonical Data + Runtime State Stabilization — COMPLETE
   310|
   311|**2026-05-16.** All three Phase 0 remediation tasks done:
   312|
   313|| Task | Status | Key change |
   314||------|--------|------------|
   315|| 0.1 — Runtime unit identity contract | ✅ | `RosterState.units` list-based, `_build_summary`/`_parse_log_events` runtime-ID aware |
   316|| 0.2 — Canonical GameState serializer | ✅ | Single `snapshot_game_state()` in `game_state.py`, autoplay+replay delegate |
   317|| 0.3 — Stop destructive DB/replay | ✅ | No DROP TABLE, INSERT-not-REPLACE, UUID game_id |
   318|
   319|Verification: 484 tests pass, lint/formatter clean. CR regression evidence in CR-05/06/12/14/20.
   320|
   321|## Phase 1 — Content compiler / schemas — COMPLETE
   322|
   323|All five Phase 1 remediation tasks done (1.1-1.5).
   324|
   325|| Task | Status | Key result |
   326||------|--------|-----------|
   327|| 1.1 — Content contract tests | ✅ | 23 tests, content.v1 Pydantic schema validation |
   328|| 1.2 — Safe cache | ✅ | Pickle removed, JSON manifest pipeline |
   329|| 1.3 — Squad/points metadata | ✅ | `squad_size` authoritative, `model_count` per-model |
   330|| 1.4 — Canonical JSON artifacts | ✅ | 16 sharded artifacts, canonical IDs, strict schemas, deterministic rebuild |
   331|| 1.5 — Frontmatter canonical IDs | ✅ | `source_path` tracking, canonical_id validation, duplicate/pre-write checks, 12 new tests |
   332|
   333|Verification: 509+ tests pass (36 content contracts), lint/formatter clean.
   334|CR evidence: CR-06, CR-11, CR-12, CR-21.
   335|
   336|## Phase 2 — Roster validator — REQUEST CHANGES after Task 2.2 check
   337|
   338|Task 2.2 was re-opened on 2026-05-17 after an independent check found Warlord eligibility/UI parity blockers.
   339|
   340|| Task | Status | Key result |
   341||------|--------|-----------|
   342|| 2.1 — Lock canonical PTS formula | ✅ | `calculate_squad_pts()`, loadout/nob support, shared parity fixture |
   343|| 2.2 — Enforce exactly one Warlord | ❌ changes_requested | Keyword-only `CHARACTER` units are not Warlord-eligible in shared validation; Team Builder treats zero eligible Characters as UI-valid. |
   344|| 2.3 — Enforce plan/feature gates | ✅ | Shared `_check_roster_limits()` — create/duplicate/update all enforced |
   345|
   346|Verification during check: scoped roster suite `68 passed, 48 warnings`; full suite `593 passed, 3 skipped, 60 warnings`; Ruff lint/format clean for checked files.
   347|CR evidence exists in CR-12, CR-16, CR-17, CR-19 but must be refreshed after Task 2.2 fixes.
   348|
   349|## Phase 2 — REQUEST CHANGES
   350|
   351|Date: 2026-05-17
   352|
   353|Task 2.2 is not currently complete after the 2026-05-17 check.
   354|
   355|| Task | Status | Key changes |
   356|| --- | --- | --- |
   357|| 2.1 — Lock canonical PTS formula | completed | Backend canonical `calculate_squad_pts()` used by validation/API; loadout/Nob production path and parity fixture verified. |
   358|| 2.2 — Enforce exactly one Warlord when required | changes_requested | Shared Warlord validator mostly works, but keyword-only `CHARACTER` units are not eligible and Team Builder does not reject/warn for zero eligible Characters. |
   359|| 2.3 — Enforce plan/feature gates consistently | completed | Shared Free/Premium roster gates verified for create/duplicate/generated-save/update/public paths. |
   360|
   361|Verification during Task 2.2 check:
   362|- `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_roster*.py tests/test_rosters.py -q` → 68 passed, 48 warnings.
   363|- `uv run python -m pytest tests/ -q` → 593 passed, 3 skipped, 60 warnings.
   364|- `uv run ruff check backend/state/roster.py web/routes/api_rosters.py backend/billing/plans.py backend/engine/ai/autoplay.py tests/test_roster.py tests/test_rosters.py tests/test_autoplay.py` → clean.
   365|- `uv run ruff format --check backend/state/roster.py web/routes/api_rosters.py backend/billing/plans.py backend/engine/ai/autoplay.py tests/test_roster.py tests/test_rosters.py tests/test_autoplay.py` → 7 files already formatted.
   366|- `git diff --check` → clean for checked Task 2.2 files.
   367|
   368|
   369|## Phase 3 completion — Combat math
   370|
   371|- Date: 2026-05-17
   372|- Completed tasks: 3.1, 3.2, 3.3
   373|- Closed findings:
   374|  - CR-07: natural 6 / Lethal Hits semantics; AP applied exactly once; Devastating Wounds only on Critical Wounds; Sustained Hits extra hits now resolve through wound/save/damage as normal non-critical hits.
   375|  - CR-11: AP/cover/Ignores Cover interaction regression evidence recorded; Sustained Hits closure recorded because Task 3.3 is co-owned by CR-11 in the remediation plan.
   376|- Still open:
   377|  - CR-07/CR-11 original review artifacts remain Request Changes until all non-Phase-3 findings are separately fixed or explicitly accepted.
   378|- Accepted debt: none.
   379|- Tests run:
   380|  - `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_modifiers.py tests/test_combat*.py -q` → 50 passed in 10.38s.
   381|  - `uv run python -m pytest tests/ -q` → 583 passed, 3 skipped, 60 warnings in 56.40s.
   382|- Lint/format run:
   383|  - `uv run ruff check backend/engine/combat.py backend/engine/modifiers.py tests/test_combat.py tests/test_modifiers.py` → All checks passed.
   384|  - `uv run ruff format --check backend/engine/combat.py backend/engine/modifiers.py tests/test_combat.py tests/test_modifiers.py` → 4 files already formatted.
   385|  - `git diff --check -- <Task 3.3 touched docs/code files>` → clean.
   386|- Browser/API smoke evidence: none required for backend combat math phase.
   387|- Remaining blockers before next phase: none for Phase 3 checkpoint.
   388|
   389|## Phase 4 — REOPENED / REQUEST CHANGES
   390|
   391|Date: 2026-05-18
   392|
   393|| Task | Status | Key changes |
   394|| --- | --- | --- |
   395|| 4.1 — Assert 5-phase 10e loop invariants | completed | Locked Command → Movement → Shooting → Charge → Fight phase order and canonical phase consumers. |
   396|| 4.2 — Lock CP and battle-shock reset semantics | completed | Active-player-only CP, CP idempotency per player turn, owner-scoped battle-shock reset/tests. |
   397|| 4.3 — Lock VP, objectives, mission normalization, Battle Ready | changes_requested | 2026-05-18 check found mission scoring values not mission-defined, VP sync drift, generic VP-cap end condition, missing Battle Ready/final snapshot tests, and red Ruff/format gates. |
   398|
   399|Verification summary:
   400|- Task 4.2 scoped: `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_game_state.py tests/test_scenario.py -q` → 28 passed.
   401|- Task 4.2 extended CP/battle-shock: `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_game_state.py tests/test_scenario.py tests/test_f2_7_battle_shock_cp_stratagems.py -q` → 42 passed.
   402|- Full suite: `uv run python -m pytest tests/ -q` → 602 passed, 3 skipped, 60 warnings.
   403|- Ruff: `uv run ruff check backend/engine/scenario.py tests/test_game_state.py tests/test_scenario.py tests/test_f2_7_battle_shock_cp_stratagems.py` → All checks passed.
   404|- Format: `uv run ruff format --check backend/engine/scenario.py tests/test_game_state.py tests/test_scenario.py tests/test_f2_7_battle_shock_cp_stratagems.py` → 4 files already formatted.
   405|- Health smoke: `/api/health` → `{"status":"ok","version":"0.7.9"}`.
   406|
   407|Remaining blockers before Phase 5: Task 4.3 is reopened; Phase 4 checkpoint is not complete until scoring/VP sync/VP-cap/tests/Ruff findings are fixed and re-verified.
   408|
   409|## Phase 4 — REQUEST CHANGES after re-check — 2026-05-19
   410|
   411|Phase 4 is not closed. Task 4.1 and Task 4.2 remain supported by the current re-check, but Task 4.3 blocks the checkpoint.
   412|
   413|| Task | Status | Evidence |
   414|| --- | --- | --- |
   415|| 4.1 — Assert 5-phase 10e loop invariants | Passing | Phase order probe reports `command -> movement -> shooting -> charge -> fight`, enum count 5. |
   416|| 4.2 — Lock CP and battle-shock reset semantics | Passing | Scenario Command probe shows active player CP/VP only and idempotent repeated processing. |
   417|| 4.3 — Lock VP, objectives, mission normalization, Battle Ready | REQUEST CHANGES | Only War probe returns 5 VP instead of 3; Purge the Foe returns 0 instead of 5; Battle Ready finalization/final snapshot regressions missing. |
   418|
   419|Verification: scoped Phase 4 suite 80 passed in 8.55s; full suite 622 passed, 3 skipped, 60 warnings in 51.93s; Ruff check and format check passed for Phase 4 files.
   420|
   421|

## Phase 4 — COMPLETE (updated 2026-05-19 after re-check)

| Task | Status | Notes |
|---|---|---|
| 4.1 | COMPLETE | Canonical 5-phase loop invariants remain green. |
| 4.2 | COMPLETE | CP/battle-shock owner-scope and idempotence remain green. |
| 4.3 | COMPLETE | Re-check blockers fixed: Only War=3, Purge=5, Battle Ready exact-once + final snapshot parity tests added. |

Verification summary:
- Scoped: 84 passed.
- Full suite: 626 passed, 3 skipped.
- Ruff check / Ruff format --check: passed.

