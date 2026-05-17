# Features — Документация фич

Полный индекс всех feature-спецификаций по фазам разработки.
Каждый файл содержит: SMART-цель, data model, implementation details, тесты.

Актуально на: 2026-05-09 | v0.7.9

---

## Phase 1: Combat Engine

**Цель:** `curl /api/simulate` → JSON с распределением урона.

| # | Фича | Часы | Статус |
|---|------|------|--------|
| [F1.1](f1.1-unit-dataclass.md) | Unit Dataclass — расширение полей | 2h | ✅ |
| [F1.2](f1.2-weapon-dataclass.md) | Weapon Dataclass — DiceExpr | 1h | ✅ |
| [F1.3](f1.3-modifier-system.md) | Modifier System — ±1, caps, rerolls | 3h | ✅ |
| [F1.4](f1.4-wiki-loader.md) | Wiki Loader — парсинг .md → Unit/Weapon | 4h | ✅ |
| [F1.5](f1.5-dice-pool.md) | Dice Pool — NumPy D6 Monte Carlo | 2h | ✅ |
| [F1.6](f1.6-combat-sequence.md) | Combat Sequence — Hit→Wound→Save→Damage→FNP | 4h | ✅ |
| [F1.7](f1.7-weapon-keywords.md) | Weapon Keywords — Sustained, Lethal, Devastating | 3h | ✅ |
| [F1.8](f1.8-tests.md) | Tests — Shoota vs Marine, HB vs Marine, Plasma | 2h | ✅ |
| [F1.9](f1.9-api-simulate.md) | POST /api/simulate — Weapon × Target → JSON | 2h | ✅ |
| [F1.10](f1.10-pmf-chart.md) | PMF Chart — Chart.js распределение урона | 4h | ✅ |
| [F1.11](f1.11-round-viewer-stub.md) | Round Viewer Stub — форма + JSON | 2h | ✅ |
| [F1.12](f1.12-multiattack.md) | MultiAttack — несколько оружий + отряды | 3h | ✅ |
| [F1.13](f1.13-weapon-keywords-phase2.md) | Weapon Keywords Phase 2 — Blast, Heavy, Torrent, Melta, Rapid Fire, Lance, Pistol, Precision, One Shot | 4h | ✅ |

**Всего:** 13 features, ~36 часов. ✅ 100%

---

## Phase 2: Game System

**Цель:** Две армии через Team Builder → карта → deployment → полный бой из N раундов → VP + end-game.

| # | Фича | Часы | Статус |
|---|------|------|--------|
| [F2.1](f2.1-game-state.md) | Game State Dataclass | 4h | ✅ |
| [F2.2](f2.2-2d-map.md) | 2D Map — NumPy grid, terrain, deploy zones | 6h | ✅ |
| [F2.3](f2.3-line-of-sight.md) | Line of Sight — Bresenham ray casting | 4h | ✅ |
| [F2.4](f2.4-missions.md) | Missions — objectives, scoring, deployment | 3h | ✅ |
| [F2.5](f2.5-game-loop.md) | Game Loop — 5 фаз (Command, Movement, Shooting, Charge, Fight) | 6h | ✅ |
| [F2.6](f2.6-phase-transitions.md) | Phase Transitions — priority, alternating activations | 4h | ✅ |
| [F2.7](f2.7-battle-shock-cp-stratagems.md) | Battle-shock (в Command Phase), CP, Stratagems | 4h | ✅ |
| [F2.8](f2.8-victory-points.md) | Victory Points — tracking, end-game, Battle Ready | 2h | ✅ |
| [F2.9](f2.9-roster-validation.md) | Roster Validation — PTS, Warlord, caps | 3h | ✅ |
| [F2.10](f2.10-roster-crud.md) | Roster CRUD — SQLite save/load/delete | 2h | ✅ |
| [F2.11](f2.11-team-builder-ui.md) | Team Builder UI — Alpine.js, PTS bar | 8h | ✅ |
| [F2.12](f2.12-leader-compatibility.md) | Leader Compatibility Checker | 3h | ✅ |
| [F2.13](f2.13-cover-terrain.md) | Cover & Terrain Effects — +1 SV, Ignores Cover, Indirect Fire, Bresenham LoS | 4h | ✅ |
| [F2.14](f2.14-deep-strike.md) | Deep Strike — reserve deployment | 3h | ⚪ |
| [F2.15](f2.15-primary-missions.md) | Primary Missions — The Ritual, Supply Drop, Scorched Earth | 12h | ⚪ |
| [F2.16](f2.16-shooting-refinements.md) | Shooting Refinements — rapid fire range, cover modifiers | 4h | ⚪ |
| [F2.17](f2.17-secondary-missions.md) | Secondary Missions — Fixed & Tactical (Pariah Nexus, 18 миссий) | 16h | ⚪ |
| [F2.18](f2.18-terrain-mechanics-10e.md) | Terrain Mechanics 10e — ruins footprint LoS, woods/craters/barricades, Plunging Fire | 10h | ⚪ |

**Всего:** 19 features, ~123 часов. ✅ 68%

---

## Phase 3: AI & Automation

**Цель:** AI принимает решения за обе стороны, прогоняет deploy → N раундов → результат → replay.

| # | Фича | Часы | Статус |
|---|------|------|--------|
| [F3.1](f3.1-greedy-decision-engine.md) | Greedy decision engine — target/action evaluation + objective movement | 6h | ✅ |
| [F3.2](f3.2-faction-ai-profiles.md) | Faction AI Profiles — wiki-driven (Orks, Tau, AdMech) | 4h | ✅ |
| [F3.4](f3.4-deployment-ai.md) | Deployment AI: zone placement + faction_ai profiles | 3h | ✅ |
| [F3.5](f3.5-autoplay.md) | Auto-play: AI vs AI — 16 тестов, VP > 0, objectives | 6h | ✅ |
| [F3.6](f3.6-replay-recording.md) | Replay recording — 18 тестов, ReplayRecorder, SQLite | 3h | ✅ |
| [F3.7](f3.7-round-viewer.md) | Round viewer: Alpine.js + Canvas replay | 6h | ✅ |
| [F3.8](f3.8-result-screen.md) | Result screen: Chart.js VP timeline, phase table | 3h | ✅ |
| [F3.10](f3.10-waaagh.md) | Waaagh! Army Rule — Orks: +1"M, 5+FNP, +1S melee | 3h | ⚪ |
| [F3.11](f3.11-ftgg-markerlight.md) | For The Greater Good + Markerlight — Tau: Spotter/Guided | 4h | ⚪ |

**Всего:** 9 features, ~46 часов. 🔧 78%

---

## Phase 4: Web UI Polish

**Цель:** Полноценное веб-приложение, готовое к пользователям.

| # | Фича | Часы | Статус |
|---|------|------|--------|
| [F4.1](f4.1-faction-browser.md) | Faction browser with category/PTS filter | 4h | ✅ |
| [F4.2](f4.2-unit-modal.md) | Unit modal: squad size, loadout, wargear | 6h | ✅ |
| [F4.3](f4.3-detachment-picker.md) | Compact detachment picker: rule preview + stratagem/enhancement badges | 3h | ✅ |
| [F4.4](f4.4-synergy-hints.md) | Synergy hints: leader compatibility, transport capacity | 4h | ✅ |
| [F4.5](f4.5-canvas-map.md) | Canvas map: terrain tiles + deploy zones (superseded by F4.14) | 8h | ✅ |
| [F4.6](f4.6-progressive-disclosure.md) | Progressive Disclosure: Beginner/Expert modes | 4h | ✅ |
| [F4.7](f4.7-stat-tooltips.md) | Tooltips on every stat (M/T/SV/W/LD/OC) | 3h | ✅ |
| [F4.8](f4.8-svg-icons.md) | SVG icons integration in unit cards | 2h | ✅ |
| [F4.9](f4.9-generate-opponent.md) | Generate Random Opponent: valid Warlord + squad_size + auto-play redirect | 2h | ✅ |
| [F4.10](f4.10-leaflet-map.md) | Leaflet map: game format + mission visualization (superseded by F4.14) | 6h | ✅ |
| [F4.11](f4.11-movement-phase.md) | Movement Phase (10ed): Normal/Advance/Fall Back/Remain Stationary | 4h | ✅ |
| [F4.12](f4.12-my-rosters.md) | My Rosters + explicit Warlord persistence in Team Builder | 4h | ✅ |
| [F4.13](f4.13-replays-list.md) | Replays List Page — `/replays` | 1h | ✅ |
| [F4.14](f4.14-strategic-battlefield-map.md) | Strategic battlefield map: mission objectives + roster units + scale | 6h | ✅ |

**Всего:** 14 features, ~57 часов. ✅ 100%

---

## Phase 5: Production

**Цель:** Приложение на сервере, HTTPS, мониторинг.

| # | Фича | Часы | Статус |
|---|------|------|--------|
| [F5.1](f5.1-dockerfile-compose.md) | Dockerfile + docker-compose | 3h | ✅ |
| [F5.2](f5.2-deployment.md) | Deployment (Dokku / Railway / self-host) | 4h | ✅ |
| [F5.3](f5.3-rate-limiting.md) | Rate limiting (slowapi) | 1h | ✅ |
| [F5.4](f5.4-cors-csp-security.md) | CORS hardening + CSP security headers | 1h | ✅ |
| [F5.5](f5.5-logging-sentry.md) | Logging (structlog) + Sentry error tracking | 2h | ✅ |
| [F5.6](f5.6-cicd-github-actions.md) | CI/CD: GitHub Actions (lint + test + deploy) | 4h | ✅ |
| [F5.7](f5.7-sqlite-backup.md) | SQLite backup strategy + restore script | 1h | ✅ |

**Всего:** 7 features, ~16 часов. ✅ 100%

---

## Phase 6: Monetization

| # | Фича | Часы | Статус |
|---|------|------|--------|
| [F6.7](f6.7-premium-trial.md) | 2-Week Premium Trial for new users | 2h | ⚪ |

**Всего:** 1 spec (остальные — без спек). ⏳ 0%

---

## Phase 7: Expansion

**Всего:** 10 features (без спек). ⏳ 0%

---

## Сквозной пайплайн AI vs AI

```
Team Builder (F2.11) → Roster CRUD (F2.10) → Roster Validation (F2.9)
    │
    ▼
POST /api/auto-play  (api_replays.py)
    │
    ├─ deploy_game()        F3.4 — AI расставляет юниты
    ├─ Scenario.run_round() × N  F2.5 — Game Loop (5 фаз)
    │   ├─ Command phase     VP scoring (F2.4/F2.8) + Battle-shock (F2.7)
    │   ├─ Movement phase    F4.11 — Normal/Advance/Fall Back
    │   ├─ Shooting phase    Combat engine (F1.6) + Cover (F2.13)
    │   ├─ Charge phase      2D6 roll → engagement
    │   ├─ Fight phase       Melee resolution
    │
    ├─ is_game_over?         rounds > max_rounds (F2.8)
    ├─ winner                max VP (F2.8)
    └─ save_replay()         Replay → SQLite (F3.6)
        │
        ▼
    /replay/{game_id}        Round Viewer (F3.7) + Result Screen (F3.8)
```

---

## Сводка

| Фаза | Features | Часы | Статус |
|------|----------|------|--------|
| **Phase 1** — Combat Engine | 13 | ~36h | ✅ 100% |
| **Phase 2** — Game System | 19 | ~123h | ✅ 68% |
| **Phase 3** — AI & Automation | 9 | ~46h | 🔧 78% |
| **Phase 4** — Web UI Polish | 14 | ~57h | ✅ 100% |
| **Phase 5** — Production | 7 | ~16h | ✅ 100% |
| **Phase 6** — Monetization | 7 | ~17h | ⏳ 0% |
| **Phase 7** — Expansion | 10 | ~40h | ⏳ 0% |
| **Итого** | **~78** | **~329h** | |
