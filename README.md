# Warpsmith — WH40k Battle Simulator

> Симулятор боёв Warhammer 40,000 с Monte Carlo анализом, AI и веб-интерфейсом.

**Версия:** 0.6.0 | **Статус:** Phase 1 ✅ | Phase 2 ✅ | Phase 3 🟢 | Phase 4 ✅ | Phase 5 🟢

Warpsmith — симулятор боёв по правилам Warhammer 40,000 10-й редакции. Wiki-driven: фракции, юниты, оружие, стратагемы — всё из YAML.

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

### ✅ Phase 3: AI & Automation (29%)
- Greedy Decision Engine: target/action evaluation
- Deployment AI: zone placement (4 deployment types)
- Faction AI Profiles: wiki-driven (WIP)

### ✅ Phase 4: Web UI Polish (75%)
- Faction browser + category/PTS filter
- Unit modal: squad size, loadout, wargear
- Detachment picker with rule preview
- Synergy hints: leader compatibility, transport capacity
- Canvas map: terrain tiles + deploy zones
- SVG icons (19 categories)

### 🟢 Phase 5: Production (29%)
- Dockerfile + docker-compose
- Deployment: Dokku, Railway, self-host (systemd)

### 🌐 Веб-интерфейс
- Team Builder: faction/units/detachments selection
- Faction Browser: filter, sort, browse units
- Scenario Setup: choose sides, mission, map
- Swagger: http://127.0.0.1:8000/docs

## 🚀 Быстрый старт

```bash
cd /mnt/d/Python/Balthier/simulator
python main.py
# → http://127.0.0.1:8000

# API пример
curl -X POST http://127.0.0.1:8000/api/simulate \
  -H "Content-Type: application/json" \
  -d '{
    "attacker_faction": "orks",
    "attacker_unit": "Boyz",
    "defender_faction": "tau",
    "defender_unit": "Strike Team",
    "weapon_name": "Shoota",
    "n_iterations": 5000
  }'
```

## 🧪 Тестирование

```bash
cd /mnt/d/Python/Balthier/simulator
python -m pytest tests/ -q
# → ~300 тестов
```

## 📁 Структура

```
/mnt/d/Python/Balthier/
├── INDEX.md              верхнеуровневый индекс проекта
├── wiki/                 ~481 .md (юниты, стратагемы, правила)
└── simulator/
    ├── DEV_INDEX.md      хаб разработчика
    ├── main.py           FastAPI
    ├── backend/          auth · billing · engine · loader · model · db
    ├── web/              routes · templates · static
    ├── tests/            27 файлов, ~300 тестов
    └── docs/             architecture · requirements · features (50 specs)
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
| [/mnt/d/Python/Balthier/wiki/WIKI_INDEX.md](/mnt/d/Python/Balthier/wiki/WIKI_INDEX.md) | Индекс вики-данных |

## 📊 Статистика

- **Тестов:** ~300 (27 файлов)
- **Юнитов:** 160 (Orks 81, Tau 40, AdMech 39)
- **Wiki:** ~481 .md файлов
- **Стратагем:** 114 (Core 13, Orks 42, AdMech 42, Tau 19)
- **Энхансментов:** 88
- **Детачментов:** 22
- **API эндпоинтов:** 20+
- **Фаз:** 7, ~75 фич, ~270 часов
- **SVG иконок:** 19 категорий
