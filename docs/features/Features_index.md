# Features — Документация фич

Полный индекс всех feature-спецификаций по фазам разработки.
Каждый файл содержит: SMART-цель, data model, implementation details, тесты.

---

## Phase 1: Combat Engine

**Цель:** `curl /api/simulate` → JSON с распределением урона.

| # | Фича | Часы | Приоритет |
|---|------|------|-----------|
| [F1.1](f1.1-unit-dataclass.md) | Unit Dataclass — расширение полей | 2h | 1 |
| [F1.2](f1.2-weapon-dataclass.md) | Weapon Dataclass — DiceExpr | 1h | 1 |
| [F1.3](f1.3-modifier-system.md) | Modifier System — ±1, caps, rerolls | 3h | 2 |
| [F1.4](f1.4-wiki-loader.md) | Wiki Loader — парсинг .md → Unit/Weapon | 4h | 2 |
| [F1.5](f1.5-dice-pool.md) | Dice Pool — NumPy D6 Monte Carlo | 2h | 2 |
| [F1.6](f1.6-combat-sequence.md) | Combat Sequence — Hit→Wound→Save→Damage→FNP | 4h | 3 |
| [F1.7](f1.7-weapon-keywords.md) | Weapon Keywords — Sustained, Lethal, Devastating | 3h | 3 |
| [F1.8](f1.8-tests.md) | Tests — Shoota vs Marine, HB vs Marine, Plasma | 2h | 4 |
| [F1.9](f1.9-api-simulate.md) | POST /api/simulate — Weapon × Target → JSON | 2h | 4 |
| [F1.10](f1.10-pmf-chart.md) | PMF Chart — Chart.js распределение урона | 4h | 5 |
| [F1.11](f1.11-round-viewer-stub.md) | Round Viewer Stub — форма + JSON | 2h | 5 |
| [F1.12](f1.12-multiattack.md) | MultiAttack — несколько оружий + отряды | 3h | 5 |
| [F1.13](f1.13-weapon-keywords-phase2.md) | Weapon Keywords Phase 2 — Blast, Heavy, Torrent, Melta, Rapid Fire, Lance, Pistol, Precision, One Shot | 6h | 2 | ⏳ |

**Всего:** 13 features, ~36 часов. 🔧 92%

---

## Phase 2: Game System

**Цель:** Две армии через Team Builder → карта → deployment → полный бой из N раундов (6 фаз/раунд) → VP + end-game условия. Итог: `Scenario.run_game()` прогоняет бой до победы по VP/раундам.

| # | Фича | Часы | Приоритет |
|---|------|------|-----------|
| [F2.1](f2.1-game-state.md) | Game State Dataclass | 4h | 1 |
| [F2.2](f2.2-2d-map.md) | 2D Map — NumPy grid, terrain, deploy zones | 6h | 1 |
| [F2.3](f2.3-line-of-sight.md) | Line of Sight — Bresenham ray casting | 4h | 2 |
| [F2.4](f2.4-missions.md) | Missions — objectives, scoring, deployment | 3h | 2 |
| [F2.5](f2.5-game-loop.md) | Game Loop — 6 фаз, run_round() | 6h | 2 |
| [F2.6](f2.6-phase-transitions.md) | Phase Transitions — priority, alternating activations | 4h | 3 |
| [F2.7](f2.7-battle-shock-cp-stratagems.md) | Battle-shock, CP, Stratagems | 4h | 3 |
| [F2.8](f2.8-victory-points.md) | Victory Points — tracking, end-game | 2h | 3 |
| [F2.9](f2.9-roster-validation.md) | Roster Validation — PTS, Warlord, caps | 3h | 4 |
| [F2.10](f2.10-roster-crud.md) | Roster CRUD — SQLite save/load/delete | 2h | 4 |
| [F2.11](f2.11-team-builder-ui.md) | Team Builder UI — Alpine.js, PTS bar | 8h | 5 |
| [F2.12](f2.12-leader-compatibility.md) | Leader Compatibility Checker | 3h | 5 |
| [F2.13](f2.13-cover-terrain.md) | Cover & Terrain Effects — +1 SV, Ignores Cover, Indirect Fire | 4h | 2 | ⏳ |
| [F2.14](f2.14-deep-strike.md) | Deep Strike & Reserves — deploy from off-map, >9" rule | 3h | 3 | ⏳ |
| [F2.15](f2.15-shooting-refinements.md) | Shooting Refinements — BGNT, Look Out Sir, Pistol in engagement | 3h | 3 | ⏳ |

**Всего:** 15 features, ~55 часов. 🔧 80%

---

## Phase 3: AI & Automation

**Цель:** AI принимает решения за обе стороны, прогоняет deploy → N раундов → результат. Итог: `POST /api/auto-play` возвращает `{winner, VP, round_logs}`, replay сохраняется в SQLite, round_viewer и result_screen отображают ход боя.

| # | Фича | Часы | Приоритет | Статус |
|---|------|------|-----------|--------|
| [F3.1](f3.1-greedy-decision-engine.md) | Greedy decision engine — target/action evaluation + objective movement 🔧 | 6h | 1 | 🔧 |
| [F3.2](f3.2-faction-ai-profiles.md) | Faction AI Profiles — wiki-driven (Orks, Tau, AdMech) | 4h | 2 | ✅ |
| [F3.4](f3.4-deployment-ai.md) | Deployment AI: zone placement logic | 3h | 3 | ✅ |
|| [F3.5](f3.5-autoplay.md) | Auto-play: AI vs AI full scenario — 16 тестов, Scenario.run_round(), deploy_game(), F3.2 AI | 6h | 3 | ✅ |
|| [F3.6](f3.6-replay-recording.md) | Replay recording: JSON event log per round/phase — 18 тестов, ReplayRecorder, SQLite persistence | 3h | 4 | ✅ |
|| [F3.7](f3.7-round-viewer.md) | Round viewer: step-by-step replay UI | 6h | 5 | ⏳ |
|| [F3.8](f3.8-result-screen.md) | Result screen: kills, damage, VP timeline chart | 3h | 5 | ⏳ |
| [F3.10](f3.10-waaagh.md) | Waaagh! Army Rule — Orks: +1"M, 5+FNP, +1S melee раз за бой | 3h | 2 | ⏳ |
| [F3.11](f3.11-ftgg-markerlight.md) | For The Greater Good + Markerlight — Tau: Spotter/Guided, +1BS, Sustained Hits 1 | 4h | 2 | ⏳ |

**Всего:** 9 features, ~42 часов. 🟢 55%

**Deprecated files (заменены):**
- [F3.2 — Ork AI](f3.2-ork-ai.md) (deprecated → superseded by F3.2 Faction AI Profiles)
- [F3.3 — T'au AI](f3.3-tau-ai.md) (deprecated → superseded by F3.2 Faction AI Profiles)
- [F3.9 — AdMech AI](f3.9-admech-ai.md) (deprecated → superseded by F3.2 Faction AI Profiles)

---

## Phase 4: Web UI Polish

**Цель:** Полноценное веб-приложение, готовое к пользователям.

| # | Фича | Часы | Приоритет | Статус |
|---|------|------|-----------|--------|
| [F4.1](f4.1-faction-browser.md) | Faction browser with category/PTS filter | 4h | 1 | ✅ |
| [F4.2](f4.2-unit-modal.md) | Unit modal: squad size, loadout, wargear selection | 6h | 1 | ✅ |
| [F4.3](f4.3-detachment-picker.md) | Detachment picker with rule preview | 3h | 2 | ✅ |
| [F4.4](f4.4-synergy-hints.md) | Synergy hints: leader compatibility, transport capacity | 4h | 2 | ✅ |
| [F4.5](f4.5-canvas-map.md) | ~~Canvas map~~ (deprecated → F4.10) | 8h | 3 | ❌ |
| [F4.10](f4.10-leaflet-map.md) | Leaflet map: game format + mission visualization | 6h | 3 | ⚪ |
| [F4.6](f4.6-progressive-disclosure.md) | Progressive Disclosure: Beginner/Intermediate/Expert | 4h | 4 | ✅ |
| [F4.7](f4.7-stat-tooltips.md) | Tooltips on every stat (M/T/SV/W/LD/OC) | 3h | 4 | ✅ |
| [F4.8](f4.8-svg-icons.md) | SVG icons integration in unit cards | 2h | 5 | ✅ |
| [F4.9](f4.9-generate-opponent.md) | Generate Random Opponent — `/api/rosters/generate` для AI-ростера | 2h | 3 | ✅ |
| [F4.12](f4.12-my-rosters.md) | My Rosters — управление ростером: delete, edit, duplicate | 4h | 2 | ⏳ |

**Всего:** 11 features, ~47 часов. 🔧 89%

---

## Phase 5: Production

**Цель:** Приложение на сервере, HTTPS, мониторинг.

| # | Фича | Часы | Приоритет | Статус |
|---|------|------|-----------|--------|
| [F5.1](f5.1-dockerfile-compose.md) | Dockerfile + docker-compose | 3h | 1 | ✅ |
| [F5.2](f5.2-deployment.md) | Deployment (Dokku / Railway / self-host) | 4h | 1 | ✅ |
| [F5.3](f5.3-rate-limiting.md) | Rate limiting (slowapi) | 1h | 2 | ✅ |
| [F5.4](f5.4-cors-csp-security.md) | CORS hardening + CSP security headers | 1h | 2 | ✅ |
| [F5.5](f5.5-logging-sentry.md) | Logging (structlog) + Sentry error tracking | 2h | 3 | ✅ |
| [F5.6](f5.6-cicd-github-actions.md) | CI/CD: GitHub Actions (lint + test + deploy) | 4h | 3 | ✅ |
| [F5.7](f5.7-sqlite-backup.md) | SQLite backup strategy + restore script | 1h | 4 | ✅ |

**Всего:** 7 features, ~16 часов. ✅ 100%

---

## Phase 2+3: Сквозной пайплайн AI vs AI

```
Team Builder (F2.11) → Roster CRUD (F2.10) → Roster Validation (F2.9)
    │
    ▼
POST /api/auto-play
    │
    ├─ deploy_game()        F3.4 — AI расставляет юниты по MissionConfig
    ├─ Scenario.run_game()   F2.5 — Game Loop (while not is_game_over)
    │   ├─ _command_phase    VP scoring через mission.calculate_victory_points()  F2.4/F2.8
    │   ├─ _movement_phase   AI movement                                            F3.1
    │   ├─ _shooting_phase   AI target selection                                   F3.1
    │   ├─ _charge_phase     AI charge decisions                                   F3.1
    │   ├─ _fight_phase      Combat engine (Hit→Wound→Save→Damage→FNP)             F1.6
    │   └─ _morale_phase     Battle-shock tests                                    F2.7
    │
    ├─ is_game_over?         rounds > max_rounds или VP ≥ 10                       F2.8
    ├─ winner                player с наибольшим VP                                F2.8
    └─ save_replay()         Replay → SQLite                                       F3.6
        │
        ▼
    /replay/{game_id}        Round Viewer (F3.7) + Result Screen (F3.8)
```

---

## Сводка

| Фаза | Features | Часы | Статус |
|------|----------|------|--------|
| **Phase 1** — Combat Engine | 12 | ~30h | ✅ 100% |
| **Phase 2** — Game System | 12 | ~40h | ✅ 100% |
| **Phase 3** — AI & Automation | 7 | ~35h | ✅ 100% |
| **Phase 4** — Web UI Polish | 9 | ~37h | ✅ 100% |
| **Phase 5** — Production | 7 | ~16h | ✅ 100% |
| **Phase 6** — Monetization | 7 | ~17h | ⏳ 0% |
| **Phase 7** — Expansion | 10 | ~40h | ⏳ 0% |
| **Итого** | **~62** | **~216h** | |
