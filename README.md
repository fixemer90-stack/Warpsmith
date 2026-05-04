# Warpsmith — WH40k Battle Simulator

> Симулятор боёв Warhammer 40,000 с Monte Carlo анализом, AI и веб-интерфейсом.

**Версия:** 0.6.6 | **Статус:** Phase 1 ✅ | Phase 2 ✅ | Phase 3 🟢 | Phase 4 ✅ | Phase 5 🟢

Warpsmith — симулятор боёв по правилам Warhammer 40,000 10-й редакции. Wiki-driven: фракции, юниты, оружие, стратагемы — всё из YAML.

🌐 **Live:** [warpsmith-production.up.railway.app](https://warpsmith-production.up.railway.app/)

Быстрый вход: [DEV_INDEX.md](DEV_INDEX.md) — хаб разработчика, [ROADMAP.md](ROADMAP.md) — дорожная карта.

## ✨ Возможности

### ✅ Phase 1: Combat Engine
- Monte Carlo симуляция (Hit → Wound → Save → Damage → FNP)
- Sustained Hits, Lethal, Devastating Wounds, Plasma, Anti-*, Blast
- MultiAttack: несколько оружий и отряды
- POST `/api/simulate` — JSON с PMF

### ✅ Phase 2: Game System (100%)
- Game State: фазы, CP, VP, движение, урон
- 2D-карта (NumPy), LoS ray casting, cover
- 3 миссии: Only War, Purge the Foe, Take and Hold
- Battle-shock + CP generation + stratagems
- Roster validation + CRUD через `/api/rosters`
- Team Builder UI: faction picker, unit modal, PTS bar, detachment picker

### 🟢 Phase 3: AI & Automation (43%)
- Greedy Decision Engine: target/action evaluation (26 тестов)
- Deployment AI: zone placement (4 deployment types)
- Faction AI Profiles: wiki-driven (Orks, Tau, AdMech) — 3 профиля загружаются
- Test coverage: 44+ тестов на AI

### ✅ Phase 4: Web UI Polish (100%)
- Faction browser + category/PTS filter
- Unit modal: squad size, loadout, wargear, full datasheet
- Detachment picker with rule preview
- Synergy hints: leader compatibility, transport capacity
- Canvas map: terrain tiles + deploy zones interactivity
- Progressive Disclosure: Beginner/Intermediate/Expert modes
- Stat tooltips (M/T/SV/W/LD/OC) with glossary
- SVG icons (18 categories, inline)
- Generate Random Opponent: AI-ростер в 1 клик

### 🟢 Phase 5: Production (43%)
- Dockerfile + docker-compose + multi-stage build
- Deployment: Railway (serverless)
- Wiki monorepo: data included in Docker-образ автоматически
- Logging: structlog (JSON в stdout) + Sentry error tracking

### 🌐 Веб-интерфейс
- [Team Builder](https://warpsmith-production.up.railway.app/team-builder): faction/units/detachments selection
- [Faction Browser](https://warpsmith-production.up.railway.app/faction-browser): filter, sort, browse units
- [Scenario Setup](https://warpsmith-production.up.railway.app/scenario-setup): choose sides, mission, map
- [Swagger API](https://warpsmith-production.up.railway.app/docs): интерактивная документация API

## 🧪 Тестирование

```bash
cd simulator
python -m pytest tests/ -q
# → ~351 тест
```

## 📁 Структура

```
simulator/
├── DEV_INDEX.md          хаб разработчика
├── main.py               FastAPI приложение
├── wiki/                 ~490 .md (юниты, стратагемы, правила) — в репозитории
├── backend/              auth · billing · engine · loader · model · db
├── web/                  routes · templates · static
├── tests/                29 файлов, ~340 тестов
└── docs/                 architecture · requirements · features (50 specs)
```

## 📚 Документация

| Документ | О чём |
|----------|-------|
| [DEV_INDEX.md](DEV_INDEX.md) | Хаб разработчика: запуск, API, тесты |
| [ROADMAP.md](ROADMAP.md) | Дорожная карта (7 фаз, ~75 фич) |
| [RELEASE.md](RELEASE.md) | Политика релизов (ZeroVer, GitHub Flow) |
| [CHANGELOG.md](CHANGELOG.md) | История изменений |
| [AGENTS.md](AGENTS.md) | Правила разработки для AI |
| [docs/architecture/C4.md](docs/architecture/C4.md) | Архитектура (4 уровня) |
| [docs/features/Features_index.md](docs/features/Features_index.md) | 50 feature-спецификаций |
| [wiki/WIKI_INDEX.md](wiki/WIKI_INDEX.md) | Индекс вики-данных |

## 📊 Статистика

- **Тестов:** ~340 (29 файлов)
- **Юнитов:** 160 (Orks 81, Tau 40, AdMech 39)
- **Wiki:** ~490 .md файлов — в репозитории (simulator/wiki/)
- **Стратагем:** 114 (Core 13, Orks 42, AdMech 42, Tau 19)
- **Энхансментов:** 88
- **Детачментов:** 23
- **API эндпоинтов:** 20+
- **Фаз:** 7, ~75 фич, ~270 часов
- **SVG иконок:** 18 категорий
