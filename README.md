# Warpsmith — WH40k Battle Simulator

> Симулятор боёв Warhammer 40,000 — Monte Carlo анализ, AI, веб-интерфейс.

**Версия:** 0.7.7 | **Статус:** Phase 1 ✅ | Phase 2 🔧 | Phase 3 🔧 | Phase 4 ✅ | Phase 5 ✅

Warpsmith — симулятор боёв по правилам Warhammer 40,000 10-й редакции. Wiki-driven: фракции, юниты, оружие, стратагемы — всё из YAML frontmatter в ~490 .md файлах. Monorepo: данные в `simulator/wiki/`, попадают в Docker-образ автоматически.

🌐 **Live:** [warpsmith-production.up.railway.app](https://warpsmith-production.up.railway.app/)

📋 [DEV_INDEX.md](DEV_INDEX.md) — хаб разработчика | 🛣️ [ROADMAP.md](ROADMAP.md) — дорожная карта

## ✨ Возможности

### ✅ Phase 0: Foundation (100%)
- FastAPI + Jinja2 + Tailwind CSS + HTMX + Alpine.js
- JWT auth + bcrypt + OAuth (Google, VK)
- SQLite: users, rosters, replays
- Wiki vault: ~490 .md (Orks 81, Tau 40, AdMech 39 юнитов)
- C4 + ADR (11) + SRS + UX documentation

### ✅ Phase 1: Combat Engine (100%)
- Monte Carlo симуляция (Hit → Wound → Save → Damage → FNP)
- 9 базовых + 9 Phase 2 weapon keywords: Sustained, Lethal, Devastating, Blast, Heavy, Torrent, Melta, Rapid Fire, Lance, Pistol, Precision, One Shot, Anti-*
- MultiAttack: несколько оружий и отряды
- POST `/api/simulate` и `/api/simulate-unit` — JSON с PMF
- PMF chart (Chart.js), 13 тестов F1.13

### 🔧 Phase 2: Game System (93%)
- Game State: фазы, позиции, CP, VP, ранения
- 2D-карта (NumPy), Bresenham LoS ray casting
- Cover & Terrain Effects: +1 SV, Ignores Cover, Indirect Fire -1 to hit
- F2.18 Terrain Mechanics 10e requirement: ruins footprint LoS, woods/craters/barricades, Plunging Fire
- 3 миссии: Only War, Purge the Foe, Take and Hold
- Game Loop (5 фаз): Command (CP + Battle-shock) → Movement → Shooting → Charge → Fight
- Battle-shock + CP generation + stratagem resolution
- Roster validation (PTS, Warlord, 3× cap) + CRUD через `/api/rosters`
- Team Builder UI: faction picker, unit modal, PTS bar, detachment picker

### 🔧 Phase 3: AI & Automation (78%)
- Greedy Decision Engine: target/action evaluation (26 тестов)
- Faction AI Profiles: wiki-driven (Orks, Tau, AdMech)
- Deployment AI: zone placement (4 deployment types, faction_ai pending)
- Auto-play: AI vs AI full scenario — VP > 0, objectives задействованы
- Replay recording: JSON event log → SQLite (22 теста)
- Round viewer: Alpine.js + Canvas step-by-step replay
- Result screen: Chart.js VP timeline, phase breakdown table
- ⚪ Waaagh! (Orks) + For The Greater Good (Tau) — спеки готовы

### ✅ Phase 4: Web UI Polish (100%)
- Faction browser: category/PTS filter, sort, search
- Unit modal: squad size, loadout, wargear, full datasheet with weapons table
- Compact detachment picker: rule preview + stratagem/enhancement badges
- Synergy hints: leader compatibility, transport capacity
- Canvas map: terrain tiles + deploy zones interactivity
- Progressive Disclosure: Beginner / Expert modes
- Stat tooltips on every stat (M/T/SV/W/LD/OC) with glossary modal
- SVG icons (18 категорий, inline) в unit cards
- Generate Random Opponent: AI-ростер в 1 клик, валидный Warlord, корректный squad_size, запуск симуляции
- Movement Phase (10ed): Normal Move / Advance / Fall Back / Remain Stationary
- Team Builder: явный выбор Warlord при нескольких Character/Warlord-capable юнитах

### ✅ Phase 5: Production (100%)
- Dockerfile + docker-compose, single-stage build
- Railway deployment: wiki monorepo, `/` healthcheck
- Rate limiting: slowapi (30 req/min anon, Retry-After)
- Security: CORS hardening + 6 security headers (CSP, HSTS, etc.)
- Logging: structlog (JSON в stdout) + Sentry error tracking
- CI/CD: GitHub Actions (ruff lint + pytest + Docker build)
- SQLite backup: backup, restore, list, cleanup

### 🌐 Веб-интерфейс
- [Team Builder](https://warpsmith-production.up.railway.app/team-builder) — сбор армии
- [Faction Browser](https://warpsmith-production.up.railway.app/faction-browser) — просмотр юнитов
- [Scenario Setup](https://warpsmith-production.up.railway.app/scenario-setup) — выбор сторон, миссии
- Round Viewer + Result Screen — пошаговый реплей боёв
- [Swagger API Docs](https://warpsmith-production.up.railway.app/docs)

## 🧪 Тестирование

```bash
cd simulator
uv run python -m pytest tests/ -q
# → 454 теста (41 файл), 3 skipped
```

## 📁 Структура

```
simulator/
├── DEV_INDEX.md              хаб разработчика
├── ROADMAP.md                дорожная карта (7 фаз, 82 фичи)
├── main.py                   FastAPI приложение
├── wiki/                     ~490 .md — данные в репозитории (monorepo)
├── backend/
│   ├── auth/                 JWT + OAuth
│   ├── billing/              Stripe, Feature Gate
│   ├── engine/               combat · dice · modifiers · scenario · replay · ai/
│   ├── loader/               wiki парсер + registry (160 units, 23 detachments)
│   ├── model/                Unit, Weapon dataclasses
│   ├── state/                GameState, Map, Mission, Roster
│   ├── db/                   SQLite
│   └── security/             CORS, CSP headers
├── web/
│   ├── routes/
│   │   ├── api.py            core: /units, /simulate, /map, /health, /factions
│   │   ├── api_detachments.py    /detachments
│   │   ├── api_rosters.py        /rosters, /generate, /synergies
│   │   ├── api_replays.py        /auto-play, /replays, /results
│   │   ├── auth.py           /register, /login, /logout
│   │   └── pages.py          HTML pages
│   ├── templates/            Jinja2 + HTMX partials
│   └── static/               JS (Alpine.js), SVG icons (18)
├── tests/                    41 файл, 454 теста
└── docs/                     architecture · requirements · features (62 specs)
```

## 📚 Документация

| Документ | О чём |
|----------|-------|
| [DEV_INDEX.md](DEV_INDEX.md) | Хаб разработчика: запуск, API, тесты |
| [ROADMAP.md](ROADMAP.md) | Дорожная карта (7 фаз, 82 фичи, 339h) |
| [ROADMAP.html](ROADMAP.html) | Визуальная дорожная карта |
| [RELEASE.md](RELEASE.md) | Политика релизов (ZeroVer, GitHub Flow) |
| [CHANGELOG.md](CHANGELOG.md) | История изменений (Keep a Changelog) |
| [AGENTS.md](AGENTS.md) | Правила разработки для AI-агентов |
| [docs/architecture/C4.md](docs/architecture/C4.md) | C4-архитектура (4 уровня) |
| [docs/architecture/ADR.md](docs/architecture/ADR.md) | 11 архитектурных решений |
| [docs/requirements/code-review-plan.md](docs/requirements/code-review-plan.md) | План полной проверки кода: 25 атомизированных review-задач |
| [docs/features/Features_index.md](docs/features/Features_index.md) | 62 feature-спецификации |
| [wiki/WIKI_INDEX.md](wiki/WIKI_INDEX.md) | Индекс вики-данных |

## 📊 Статистика

- **Тестов:** 454 (41 файл), 3 skipped
- **Юнитов:** 160 (Orks 81, Tau 40, AdMech 39)
- **Wiki:** ~490 .md — в репозитории (`simulator/wiki/`)
- **Стратагем:** 114 (Core 13, Orks 42, AdMech 42, Tau 19)
- **Энхансментов:** 88
- **Детачментов:** 23
- **API эндпоинтов:** 25+ (4 модуля: api, api_detachments, api_rosters, api_replays)
- **Фаз:** 7 · 82 фичи · ~339 часов
- **SVG иконок:** 18 категорий
