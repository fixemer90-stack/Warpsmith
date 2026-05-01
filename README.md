# Warpsmith — WH40k Battle Simulator

> Симулятор боёв Warhammer 40,000 с Monte Carlo анализом, AI и веб-интерфейсом.

**Версия:** 0.3.0 | **Статус:** Phase 1 ✅ | Phase 2 🚧

Warpsmith — это полнофункциональный симулятор боёв по правилам Warhammer 40,000 10-й редакции. Проект использует вики как источник данных о юнитах, оружии и правилах, обеспечивая точность и актуальность.

## ✨ Возможности

### 🎯 Phase 1: Combat Engine (Завершён)
- **Monte Carlo симуляция**: Точная статистическая оценка исходов боёв
- **Полная последовательность атак**: Hit → Wound → Save → Damage → FNP
- **Все ключевые механики**: Sustained Hits, Lethal, Devastating Wounds, Plasma Overcharge, Anti-*, Blast, Rapid Fire
- **Множественное оружие**: Юниты с несколькими типами оружия
- **Отрядные атаки**: Симуляция атак от целых отрядов
- **PMF анализ**: Probability Mass Function с визуализацией распределений

### 🌐 Веб-интерфейс
- **PMF Chart**: Интерактивные графики распределения повреждений (Chart.js)
- **Round Viewer**: Просмотр результатов симуляции с историей раундов
- **REST API**: Полноценное API для интеграции

### 📊 Технические особенности
- **Язык**: Python 3.12+ с строгой типизацией
- **Фреймворк**: FastAPI + Uvicorn
- **Фронтенд**: Jinja2 + Tailwind CSS + HTMX + Alpine.js
- **База данных**: SQLite с миграциями
- **Тестирование**: pytest + 53 теста (100% coverage на engine)
- **Архитектура**: Чистая архитектура с разделением на слои

## 🚀 Быстрый старт

### Локальный запуск

```bash
# Клонирование
git clone https://github.com/fixemer90-stack/Warpsmith.git
cd simulator

# Установка зависимостей
pip install -r requirements.txt
# или
pip install -e .

# Запуск сервера
python main.py

# Открыть в браузере: http://127.0.0.1:8000
```

### API примеры

```bash
# Симуляция оружия
curl -X POST http://127.0.0.1:8000/api/simulate \
  -H "Content-Type: application/json" \
  -d '{
    "attacker_faction": "test",
    "attacker_unit": "Attacker",
    "defender_faction": "test",
    "defender_unit": "Tactical Marine",
    "weapon_name": "Plasma Gun",
    "distance": 24,
    "n_iterations": 10000
  }'

# Симуляция юнита (несколько оружий)
curl -X POST http://127.0.0.1:8000/api/simulate-unit \
  -H "Content-Type: application/json" \
  -d '{
    "attacker_faction": "test",
    "attacker_unit": "MultiWeapon",
    "defender_faction": "test",
    "defender_unit": "Target",
    "squad_size": 1,
    "n_iterations": 10000
  }'
```

## 📁 Структура проекта

```
simulator/
├── main.py                    # Точка входа FastAPI
├── pyproject.toml            # Зависимости и конфигурация
├── AGENTS.md                 # Правила разработки для AI-агентов
├── ROADMAP.md                # Дорожная карта развития
├── CHANGELOG.md              # История изменений
├── DEV_INDEX.md              # Хаб документации
│
├── backend/                  # Бэкенд (Python)
│   ├── auth/                 # JWT аутентификация
│   ├── billing/              # Платежи и подписки
│   ├── loader/               # Парсер вики (.md → Python)
│   │   ├── registry.py       # WikiRegistry с кэшированием
│   │   └── parser.py         # Парсинг frontmatter/markdown
│   ├── engine/               # Движок симуляции
│   │   ├── dice.py           # NumPy Monte Carlo
│   │   ├── combat.py         # Hit→Wound→Save→Damage→FNP
│   │   └── modifiers.py      # Модификаторы и правила
│   ├── model/                # Data models
│   │   └── unit.py           # Unit/Weapon dataclasses
│   ├── state/                # Игровое состояние (Phase 2)
│   ├── ai/                   # AI поведение (Phase 3)
│   ├── db/                   # SQLite persistence
│   └── reporter/             # Вывод результатов
│
├── web/                      # Веб-интерфейс
│   ├── routes/               # FastAPI роуты
│   │   ├── api.py            # JSON API
│   │   ├── pages.py          # HTML страницы
│   │   └── auth.py           # Аутентификация
│   ├── templates/            # Jinja2 шаблоны
│   │   ├── base.html         # Layout
│   │   ├── pmf_chart.html    # PMF визуализация
│   │   ├── round_viewer.html # Просмотр результатов
│   │   └── auth/             # Страницы входа/регистрации
│   └── static/               # Статические файлы
│       └── icons/            # SVG иконки фракций
│
├── docs/                     # Документация
│   ├── architecture/         # C4-диаграммы, ADR решения
│   └── requirements/         # SRS, UX дизайн
│
├── tests/                    # Тесты (pytest)
│   ├── test_combat.py        # Симуляция боя
│   ├── test_dice.py          # Дайсы и статистика
│   ├── test_modifiers.py     # Модификаторы
│   └── test_pmf_chart.py     # Веб-интерфейс
│
├── wiki/                     # Данные (источник правды)
│   ├── factions/             # Описания фракций
│   ├── units/                # Юниты по фракциям
│   ├── stratagems/           # Стратагемы
│   └── rules/                # Правила игры
│
└── ref_data/                 # Сгенерированные данные
    ├── admech_ref.json       # AdMech faction data
    ├── orks_ref.json         # Orks faction data
    └── tau_ref.json          # T'au faction data
```

## 🎯 Roadmap

### ✅ Phase 0: Foundation (Завершена)
- FastAPI scaffold, аутентификация, база данных
- Wiki vault (360+ страниц данных)
- C4 архитектура, ADR решения

### ✅ Phase 1: Combat Engine (Завершена)
- Monte Carlo симуляция (NumPy)
- Полная последовательность боя
- Модификаторы и специальные правила
- API и веб-интерфейс
- **Все 12 фич реализованы!**

### 🚧 Phase 2: Game System (В разработке)
- Игровое состояние (позиции, раны, CP, VP)
- 2D-карта с террейном и LoS
- Game Loop: Deployment → Round → End
- Roster validation и управление

### 🏗 Phase 3: AI & Automation (Планируется)
- Greedy AI для принятия решений
- Фракционные AI (Ork, T'au)
- Автоплей: AI vs AI бои
- Replay recording

### 🎨 Phase 4: Web UI Polish (Планируется)
- Faction browser с фильтрами
- Unit modal с настройками
- Canvas карта с интерактивностью
- Progressive disclosure UX

## 🧪 Тестирование

```bash
# Запуск всех тестов
python -m pytest tests/ -v

# С покрытием
python -m pytest tests/ --cov=backend/engine

# Только combat engine
python -m pytest tests/test_combat.py -v
```

**Результаты:** 53 теста ✅, coverage >80% на engine.

## 🤝 Разработка

Проект использует:
- **ZeroVer**: v0.PHASE.PATCH
- **GitHub Flow**: main + feature branches
- **Conventional commits**: feat/fix/docs/test/refactor
- **PEP 8 + type hints**: Строгое соблюдение стандартов

### Добавление новой фракции

1. Создать `wiki/factions/<Name>.md`
2. Добавить юнитов в `wiki/units/<faction>/`
3. Создать AI в `backend/ai/<faction>_ai.py`
4. **Код движка менять не нужно!**

## 📈 Статистика проекта

- **Строки кода**: ~5000+ (Python + HTML/JS)
- **Тестов**: 53 (100% на combat engine)
- **Фич**: 12/12 в Phase 1
- **Время разработки**: ~60 часов
- **Технологии**: 8 (Python, FastAPI, NumPy, Chart.js, HTMX...)

## 📚 Документация

- **[ROADMAP.md](ROADMAP.md)** — Детальная дорожная карта
- **[AGENTS.md](AGENTS.md)** — Правила для AI-агентов
- **[CHANGELOG.md](CHANGELOG.md)** — История изменений
- **[DEV_INDEX.md](DEV_INDEX.md)** — Хаб документации
- **[docs/architecture/](docs/architecture/)** — C4-диаграммы и ADR

## 🐛 Issues и Contributing

- **GitHub Issues**: [Сообщить о баге](https://github.com/fixemer90-stack/Warpsmith/issues)
- **Contributing**: См. [AGENTS.md](AGENTS.md) для правил разработки
- **Feature requests**: Используйте GitHub Issues с тегом `enhancement`

## 📄 Лицензия

MIT License — см. [LICENSE](LICENSE) файл.

---

**Warpsmith** — ваш надежный помощник в анализе боёв Warhammer 40,000! ⚔️🚀
