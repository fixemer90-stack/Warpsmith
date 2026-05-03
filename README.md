# Warpsmith — WH40k Battle Simulator

> Симулятор боёв Warhammer 40,000 с Monte Carlo анализом, AI и веб-интерфейсом.

**Версия:** 0.4.0 | **Статус:** Phase 1 ✅ | Phase 2 ✅ | Phase 3 🚧

Warpsmith — симулятор боёв по правилам Warhammer 40,000 10-й редакции. Вики как источник данных: фракции, юниты, оружие, стратагемы.

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
- Battle-shock тесты + CP generation + stratagems
- Roster validation + GameSize enum (Combat Patrol–Onslaught)
- Roster CRUD через `/api/rosters`
- Victory Points tracking and end-game conditions
- Team Builder UI: faction picker, unit modal, PTS bar
- Leader Compatibility Checker

### 🌐 Веб-интерфейс
- Team Builder: динамический выбор фракций/юнитов/детачментов
- Swagger: http://127.0.0.1:8000/docs
- REST API: 10 эндпоинтов

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
WIKI_PATH=/mnt/d/Python/Balthier/wiki python -m pytest tests/ -v
# → 150+ теста, покрытие 80%+
```

## 📁 Структура

```
/mnt/d/Python/Balthier/
├── INDEX.md              ← этот файл (верхнеуровневый индекс)
├── wiki/                 ~478 .md (юниты, стратагемы, правила)
└── simulator/
    ├── DEV_INDEX.md      хаб разработчика
    ├── main.py           FastAPI
    ├── backend/          auth · engine · loader · model · state · db
    ├── web/              routes · templates · static
    ├── tests/            20+ файлов, 150+ теста
    └── docs/             architecture · requirements · features
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
| [docs/features/](docs/features/) | 24 feature-спецификации |
| wiki/WIKI_INDEX.md | Индекс вики-данных |

## 📊 Статистика

- **Тестов:** 150+ (100% pass, 80%+ покрытие)
- **Юнитов:** 160 (Orks 81, Tau 40, AdMech 39)
- **Wiki:** ~478 .md файлов
- **Стратагем:** 114 (Core 13, Orks 42, AdMech 42, Tau 19)
- **Энхансментов:** 88
- **Детачментов:** 22
- **API эндпоинтов:** 10
- **Фаз:** 7, ~75 фич, ~270 часов
