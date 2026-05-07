# Roadmap — Warpsmith

> Дорожная карта разработки. Версия 0.7.7
> **Статус:** Phase 0 ✅ | Phase 1 ✅ | Phase 2 ✅

---

## ✅ Phase 0: Foundation

```
[████████████████████] 100% · 12 features
```

### Features

| #    | Статус | Фича                                                    | Часы |
| ---- | ------ | ------------------------------------------------------- | ---- |
| 0.1  | ✅      | FastAPI scaffold + main.py + структура backend/web/docs | 4h   |
| 0.2  | ✅      | JWT auth + bcrypt hash (PBKDF2 в Docker)                | 3h   |
| 0.3  | ✅      | Register / Login / Logout routes + формы                | 2h   |
| 0.4  | ✅      | OAuth Google + VK providers (Provider Interface)        | 4h   |
| 0.5  | ✅      | SQLite schema + migration (users, rosters, replays)     | 2h   |
| 0.6  | ✅      | Wiki vault: ~490 страниц (Orks, Tau, AdMech, rules)    | 20h  |
| 0.7  | ✅      | C4 · ADR (11) · SRS (7 разделов) · UX docs              | 6h   |
| 0.8  | ✅      | SVG Icons · ICON_MAP (18 категорий юнитов)              | 2h   |
| 0.9  | ✅      | base.html + Tailwind CDN + HTMX + Alpine.js             | 2h   |
| 0.10 | ✅      | Billing stubs · Feature Gate · Free/Premium tiers       | 3h   |
| 0.11 | ✅      | Wiki loader: registry + parser + кэш                   | 4h   |
| 0.12 | ✅      | Wiki monorepo: данные в репозитории                     | 2h   |

---

## ✅ Phase 1: Combat Engine

```
[████████████████████] 100% · 13 features
```

**Цель:** `curl /api/simulate` → JSON с распределением урона.

| # | Статус | Фича | Часы |
|---|--------|------|------|
| 1.1 | ✅ | Unit dataclass (M/T/SV/W/LD/OC, weapons, abilities) | 2h |
| 1.2 | ✅ | Weapon dataclass (S/AP/D, DiceExpr, keywords) | 1h |
| 1.3 | ✅ | Modifier system (±1, rerolls, caps, torrent, blast) | 3h |
| 1.4 | ✅ | Wiki Loader — парсинг .md frontmatter → Unit objects | 4h |
| 1.5 | ✅ | Dice pool — NumPy D6 Monte Carlo engine | 2h |
| 1.6 | ✅ | Combat sequence: Hit → Wound → Save → Damage → FNP | 4h |
| 1.7 | ✅ | Weapon keywords: Sustained, Lethal, Devastating, Anti-* | 3h |
| 1.8 | ✅ | Tests: Shoota vs Marine, HB vs Marine, Plasma | 2h |
| 1.9 | ✅ | POST /api/simulate — Weapon × Target → JSON | 2h |
| 1.10 | ✅ | PMF chart — damage distribution graph (Chart.js) | 4h |
| 1.11 | ✅ | Round Viewer stub — отображение JSON результата | 2h |
| 1.12 | ✅ | MultiAttack — несколько оружий + отряды | 3h |
| 1.13 | ✅ | Weapon Keywords Phase 2: Blast, Heavy, Torrent, Melta, Rapid Fire, Lance, Pistol, Precision, One Shot (13 тестов) | 4h |

---

## 🔧 Phase 2: Game System

```
[████████████████████] 100% · 13 features
```

**Цель:** Полный Game Loop с картой, миссиями, ростерами.

| # | Статус | Фича | Часы |
|---|--------|------|------|
| 2.1 | ✅ | Game State: players dict, UnitState, PlayerState | 4h |
| 2.2 | ✅ | BattlefieldMap: NumPy terrain, deploy zones, objectives | 6h |
| 2.3 | ✅ | Line of Sight (LoS) — Bresenham ray casting | 4h |
| 2.4 | ✅ | Missions: MissionConfig + MissionObjective + scoring | 3h |
| 2.5 | ✅ | Game Loop: Command → Movement → Shooting → Charge → Fight | 6h |
| 2.6 | ✅ | Phase transitions via GameState.next_phase() | 4h |
| 2.7 | ✅ | Battle-shock + CP generation + stratagem resolution | 4h |
| 2.8 | ✅ | Victory Points tracking + end-game conditions | 2h |
| 2.9 | ✅ | Roster validation (PTS, Warlord, 3× cap) + GameSize enum | 3h |
| 2.10 | ✅ | Roster CRUD: SQLite save/load/delete via /api/rosters | 2h |
| 2.11 | ✅ | Team Builder UI: faction picker, unit modal, PTS bar | 8h |
| 2.12 | ✅ | Synergy hints: leader compatibility, transport capacity | 3h |
| 2.13 | ✅ | Cover & Terrain Effects: +1SV cover, Ignores Cover, Indirect Fire -1 to hit, Bresenham LoS | 4h |


---

## 🔧 Phase 3: AI & Automation

```
[█████████████░░░░░░░] 67% · 9 features (6 done, 1 in-progress, 2 pending)
```

**Цель:** AI принимает решения за обе стороны, прогоняет deploy → N раундов → результат → replay.

| # | Статус | Фича | Часы |
|---|--------|------|------|
| 3.1 | ✅ | Greedy decision engine — target/action evaluation (26 тестов) | 6h |
| 3.2 | ✅ | Faction AI Profiles — wiki-driven (Orks, Tau, AdMech) | 4h |
| 3.3 | 🔧 | Deployment AI: zone placement logic (faction_ai не интегрирован) | 3h |
| 3.4 | ✅ | Auto-play: AI vs AI full scenario (VP > 0, objectives задействованы) | 6h |
| 3.5 | ✅ | Replay recording: JSON event log per round/phase (ReplayRecorder в autoplay, 22 теста) | 3h |
| 3.6 | ✅ | Round viewer: step-by-step replay UI (round_viewer.html + replay_viewer.js, 6 тестов) | 6h |
| 3.7 | ✅ | Result screen: kills, damage, VP timeline chart (result.html + result_chart.js, 6 тестов) | 3h |
| 3.10 | ⚪ | Waaagh! — Orks Army Rule: +1" Move, 5+ FNP, +1S melee (spec: f3.10-waaagh.md) | 3h |
| 3.11 | ⚪ | For The Greater Good + Markerlight — Tau Army Rule: Spotter/Guided, +1 BS, Sustained Hits (spec: f3.11-ftgg-markerlight.md) | 4h |

### 🔧 Phase 3 — Что доделать

| #   | Задача                         | Где             | Суть                                                                                                                             |
| --- | ------------------------------ | --------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| 3.3 | Подключить faction_ai к деплою | `deployment.py` | `deploy_game()` не учитывает FactionAIProfile. Импортировать `load_profile()`, применять faction-specific logic при расстановке. |

**Deprecated (заменены F3.2):** Ork AI, T'au AI, AdMech AI.

---

## ✅ Phase 4: Web UI Polish

```
[████████████████████] 100% · 10 features
```

**Цель:** Полноценное веб-приложение, готовое к пользователям. ✅ Верифицировано: все фичи рабочие.

| # | Статус | Фича | Часы |
|---|--------|------|------|
| 4.1 | ✅ | Faction browser + category/PTS filter | 4h |
| 4.2 | ✅ | Unit modal: squad size, loadout, wargear, full datasheet | 6h |
| 4.3 | ✅ | Detachment picker with rule preview | 3h |
| 4.4 | ✅ | Synergy hints: leader compatibility, transport capacity | 4h |
| 4.5 | ✅ | Canvas map: terrain tiles + deploy zones interactivity | 8h |
| 4.6 | ✅ | Progressive Disclosure: Beginner / Intermediate / Expert | 4h |
| 4.7 | ✅ | Tooltips on every stat (M/T/SV/W/LD/OC) | 3h |
| 4.8 | ✅ | SVG icons integration in unit cards | 2h |
| 4.9 | ✅ | Generate Random Opponent | 2h |
| 4.11 | ✅ | Movement Phase (10ed): Normal Move / Advance / Fall Back / Remain Stationary, AI objective distribution | 4h |

---

## ☁️ Phase 5: Production

```
[████████████████████] 100% · 7/7 features
```

**Цель:** Приложение на сервере, HTTPS, мониторинг. ✅ Все 7 фич реализованы: Docker, Railway deploy, rate limiting (slowapi), CORS hardening + CSP, structlog/Sentry логирование, CI/CD GitHub Actions, SQLite backup.

| # | Статус | Фича | Часы |
|---|--------|------|------|
| 5.1 | ✅ | Dockerfile + single-stage build | 3h |
| 5.2 | ✅ | Railway deployment + wiki monorepo | 4h |
| 5.3 | ✅ | Rate limiting (slowapi) — 30 req/min anon, health exempt, Retry-After заголовки | 2h |
| 5.4 | ✅ | CORS hardening + CSP security headers — production-aware, 6 security заголовков | 2h |
| 5.5 | ✅ | Logging (structlog) + Sentry error tracking | 2h |
| 5.6 | ✅ | CI/CD: GitHub Actions (lint + test + deploy) | 4h |
| 5.7 | ✅ | SQLite backup strategy + restore script | 1h |

---

## 💰 Phase 6: Monetization

```
[░░░░░░░░░░░░░░░░░░░░] 0% · 7 features
```

| # | Статус | Фича | Часы |
|---|--------|------|------|
| 6.1 | ⚪ | Stripe Checkout Session (live keys) | 4h |
| 6.2 | ⚪ | Stripe webhook — signature verification | 2h |
| 6.3 | ⚪ | Feature Gate в API: tier check на каждом эндпоинте | 3h |
| 6.4 | ⚪ | Upgrade banner + ad placeholder (Free tier) | 2h |
| 6.5 | ⚪ | Ad network integration | 4h |
| 6.6 | ⚪ | Usage limits — max simulations/day for Free | 2h |
| 6.7 | ⚪ | 2-Week Premium Trial for new users | 2h |

---

## 🚀 Phase 7: Expansion

```
[░░░░░░░░░░░░░░░░░░░░] 0% · 10 features
```

| #    | Статус | Фича                                             | Часы |
| ---- | ------ | ------------------------------------------------ | ---- |
| 7.1  | ⚪      | Fill remaining faction stubs (Chaos, Imperium)   | —    |
| 7.2  | ⚪      | Export: CSV/JSON для ростереров и реплеев        | 4h   |
| 7.3  | ⚪      | Import: Battlescribe / NewRecruit roster         | 8h   |
| 7.4  | ⚪      | Community: публичные ростера, рейтинг, лайки     | 6h   |
| 7.5  | ⚪      | Campaign mode: linked scenarios, persistent army | 10h  |
| 7.6  | ⚪      | Mobile responsive — адаптация под телефоны       | 6h   |
| 7.7  | ⚪      | i18n: английская локализация                     | 8h   |
| 7.8  | ⚪      | Custom AI personalities (aggressive / cautious)  | 6h   |
| 7.9  | ⚪      | Analytics: most used units, weapons, win rates   | 4h   |


---

## 📊 Сводка

| Фаза                   | Features | Часы      | Статус |
| ---------------------- | -------- | --------- | ------ |
| **0. Foundation**      | 12       | ~40ч      | ✅ 100% |
| **1. Combat Engine**   | 13       | ~70ч      | ✅ 100% |
| **2. Game System**     | 13       | ~62ч      | ✅ 100% |
| **3. AI & Automation** | 9        | ~46ч      | 🔧 67%  |
| **4. Web UI Polish**   | 10       | ~41ч      | ✅ 100% |
| **5. Production**      | 7        | ~15ч      | ✅ 100% |
| **6. Monetization**    | 7        | ~15ч      | ⏳ 0%   |
| **7. Expansion**       | 10       | ~40ч      | ⏳ 0%   |
| **Итого**              | **~81**  | **~329ч** |        |
