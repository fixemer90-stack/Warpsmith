# Project Index — Warpsmith

**Продукт:** Warpsmith — симулятор сценариев Warhammer 40k.

Полный индекс всех файлов проекта. От корня до каждого модуля.
Обновлён: 2026-05-01 | v0.2.0

## 📋 Легенда

| Статус | Значение |
|--------|----------|
| ✅ | Реализован / готов |
| 🏗 | В разработке / скелет |
| 📄 | Документация |
| ⚪ | Пусто / заглушка |

---

## 1️⃣ Корень проекта

```
simulator/
```

| # | Файл | Статус | Назначение |
|---|------|--------|------------|
| 1.1 | `AGENTS.md` | ✅ | Правила для AI-агентов: стек, языки, конвенции |
| 1.2 | `DEV_INDEX.md` | ✅ | Хаб разработчика |
| 1.3 | `README.md` | ✅ | README с быстрым стартом |
| 1.4 | `main.py` | ✅ | Точка входа FastAPI |
| 1.5 | `pyproject.toml` | ✅ | Зависимости: FastAPI, bcrypt, Jinja2, NumPy |
| 1.6 | `.gitignore` | ✅ | Исключения: __pycache__, .env, *.db, wiki/ |
| 1.7 | `.env.example` | ✅ | Production-конфигурация |
| 1.8 | `.env` | ✅ | Локальная разработка |
| 1.9 | `ROADMAP.md` | ✅ | Дорожная карта (7 фаз, ~75 фич) |
| 1.10 | `ROADMAP.html` | ✅ | Визуализация roadmap |

---

## 2️⃣ Backend — Ядро

```
backend/
├── auth/           ← JWT, OAuth, регистрация
├── billing/        ← Stripe, Feature Gate
├── loader/         ← загрузка данных из вики
├── model/          ← data-модели
├── engine/         ← симуляция боя (Phase 1)
├── ai/             ← AI-поведение
├── state/          ← игровое состояние
├── db/             ← SQLite
└── reporter/       ← вывод результатов
```

### 2.0 Auth — JWT + OAuth

| # | Файл | Статус | Назначение |
|---|------|--------|------------|
| 2.0.1 | `backend/auth/__init__.py` | ✅ | User, JWT, bcrypt, get_current_user, cookie helpers |
| 2.0.2 | `backend/auth/providers/__init__.py` | ⚪ | Пакет OAuth-провайдеров |
| 2.0.3 | `backend/auth/providers/base.py` | 🏗 | OAuthProvider (ABC), PROVIDER_REGISTRY |
| 2.0.4 | `backend/auth/providers/google.py` | 🏗 | Google OAuth (OIDC) |
| 2.0.5 | `backend/auth/providers/vk.py` | 🏗 | VK OAuth (VK ID) |
| 2.0.6 | `backend/auth/providers/routes.py` | 🏗 | /auth/{provider}/login, /callback, /providers |

### 2.1 Loader — загрузка данных из вики

| # | Файл | Статус | Назначение |
|---|------|--------|------------|
| 2.1.1 | `backend/loader/registry.py` | 🏗 | WikiRegistry: парсинг .md → in-memory dict |
| 2.1.2 | `backend/loader/icon_map.py` | ✅ | ICON_MAP: 16 категорий, цвета, SVG |

### 2.2 Model — data-модели

| # | Файл | Статус | Назначение |
|---|------|--------|------------|
| 2.2.1 | `backend/model/unit.py` | 🏗 | `Unit` dataclass (M/T/SV/W/LD/OC) + `Weapon` |

### 2.3 Engine — симуляция боя

| # | Файл | Статус | Назначение |
|---|------|--------|------------|
| 2.3.1 | `backend/engine/combat.py` | ⚪ | AttackSequence: Hit → Wound → Save → Damage |
| 2.3.2 | `backend/engine/modifiers.py` | ⚪ | ±1 caps, Sustained/Lethal/Devastating Wounds |
| 2.3.3 | `backend/engine/dice.py` | ⚪ | NumPy D6 pool — Monte Carlo |
| 2.3.4 | `backend/engine/scenario.py` | ⚪ | Game Loop: Deployment → Round → Phase → End |

### 2.4 AI — поведение юнитов

| # | Файл | Статус | Назначение |
|---|------|--------|------------|
| 2.4.1 | `backend/ai/decision.py` | ⚪ | General AI Framework (greedy) |
| 2.4.2 | `backend/ai/ork_ai.py` | ⚪ | Ork AI |
| 2.4.3 | `backend/ai/tau_ai.py` | ⚪ | T'au AI |

### 2.5 State — игровое состояние

| # | Файл | Статус | Назначение |
|---|------|--------|------------|
| 2.5.1 | `backend/state/game_state.py` | ⚪ | Game State: позиции, раны, CP, VP |
| 2.5.2 | `backend/state/map.py` | ⚪ | 2D-карта (NumPy) + террейн + LoS |
| 2.5.3 | `backend/state/mission.py` | ⚪ | Миссии, метки целей, условия победы |

### 2.6 DB — SQLite

| # | Файл | Статус | Назначение |
|---|------|--------|------------|
| 2.6.1 | `backend/db/database.py` | ✅ | SQLite wrapper + migrate() |
| 2.6.2 | `backend/db/models.py` | ⚪ | (будущие) ORM-модели |

### 2.7 Billing — планы и подписки

| # | Файл | Статус | Назначение |
|---|------|--------|------------|
| 2.7.1 | `backend/billing/__init__.py` | ⚪ | Пакет billing |
| 2.7.2 | `backend/billing/plans.py` | 🏗 | UserFeatures.for_user() — Feature Gate |
| 2.7.3 | `backend/billing/stripe_stub.py` | 🏗 | Stripe-заглушка |
| 2.7.4 | `backend/billing/webhooks.py` | 🏗 | /api/webhooks/stripe, /api/subscribe |

### 2.8 Reporter — вывод

| # | Файл | Статус | Назначение |
|---|------|--------|------------|
| 2.8.1 | `backend/reporter/table.py` | ⚪ | Rich-таблицы в терминал |
| 2.8.2 | `backend/reporter/json_export.py` | ⚪ | JSON-экспорт результатов |

---

## 3️⃣ Web — Веб-интерфейс

```
web/
├── routes/         ← FastAPI роуты
├── templates/      ← Jinja2-шаблоны
├── static/         ← JS/CSS/SVG
└── partials/       ← HTMX-фрагменты
```

### 3.1 Routes

| # | Файл | Статус | Назначение |
|---|------|--------|------------|
| 3.1.1 | `web/routes/pages.py` | 🏗 | /, /team-builder, /scenario-setup, /pricing, /round-viewer |
| 3.1.2 | `web/routes/api.py` | 🏗 | /api/units/{faction}, /api/simulate, /api/health |
| 3.1.3 | `web/routes/auth.py` | ✅ | POST /register, /login; GET /logout, /api/me |

### 3.2 Templates

| # | Файл | Статус | Назначение |
|---|------|--------|------------|
| 3.2.1 | `web/templates/base.html` | ✅ | Layout (Tailwind + HTMX + Alpine) + auth + ads |
| 3.2.2 | `web/templates/index.html` | ✅ | Главная |
| 3.2.3 | `web/templates/team_builder.html` | 🏗 | Сбор армии |
| 3.2.4 | `web/templates/scenario_setup.html` | 🏗 | Выбор миссии, карты |
| 3.2.5 | `web/templates/round_viewer.html` | ⚪ | Результаты симуляции |
| 3.2.6 | `web/templates/auth/login.html` | ✅ | Форма входа |
| 3.2.7 | `web/templates/auth/register.html` | ✅ | Форма регистрации |
| 3.2.8 | `web/templates/pricing.html` | 🏗 | Free vs Premium |

### 3.3 Static

| # | Файл | Статус | Назначение |
|---|------|--------|------------|
| 3.3.1 | `web/static/team_builder.js` | 🏗 | Alpine.js: ростер, PTS, save/load |
| 3.3.2 | `web/static/icons/*.svg` (16) | ✅ | SVG-иконки категорий |

---

## 4️⃣ Docs — Документация

```
docs/
├── architecture/   ← архитектура
├── requirements/   ← требования
└── features/       ← feature-спецификации
```

### 4.1 Architecture

| # | Файл | Статус | Назначение |
|---|------|--------|------------|
| 4.1.1 | `docs/architecture/C4.md` | ✅ | C4: 4 уровня (+Auth, Billing, OAuth) |
| 4.1.2 | `docs/architecture/ADR.md` | ✅ | 11 архитектурных решений |
| 4.1.3 | `ROADMAP.md` | ✅ | Дорожная карта |
| 4.1.4 | `ROADMAP.html` | ✅ | Визуализация roadmap |

### 4.2 Requirements

| # | Файл | Статус | Назначение |
|---|------|--------|------------|
| 4.2.1 | `docs/requirements/SRS.md` | ✅ | 7 разделов требований |
| 4.2.2 | `docs/requirements/UX.md` | 📝 | UX-дизайн (draft) |

### 4.3 Features — Спецификации по фазам

| # | Файл | Статус | Назначение |
|---|------|--------|------------|
| 4.3.0 | `docs/features/README.md` | ✅ | Индекс всех feature-спецификаций |
| 4.3.1 | `docs/features/f1.1-unit-dataclass.md` | 📝 | Unit dataclass — расширение полей |
| 4.3.2 | `docs/features/f1.2-weapon-dataclass.md` | 📝 | Weapon dataclass — DiceExpr |
| 4.3.3 | `docs/features/f1.3-modifier-system.md` | 📝 | Modifier System — ±1, caps |
| 4.3.4 | `docs/features/f1.4-wiki-loader.md` | 📝 | Wiki Loader — парсинг .md |
| 4.3.5 | `docs/features/f1.5-dice-pool.md` | 📝 | Dice Pool — NumPy Monte Carlo |
| 4.3.6 | `docs/features/f1.6-combat-sequence.md` | 📝 | Combat Sequence — Hit→Wound→Save→Damage→FNP |
| 4.3.7 | `docs/features/f1.7-weapon-keywords.md` | 📝 | Weapon Keywords — Sustained, Lethal, Devastating |
| 4.3.8 | `docs/features/f1.8-tests.md` | 📝 | Tests — 5 боевых сценариев |
| 4.3.9 | `docs/features/f1.9-api-simulate.md` | 📝 | POST /api/simulate — Weapon×Target→JSON |
| 4.3.10 | `docs/features/f1.10-pmf-chart.md` | 📝 | PMF Chart — Chart.js bar chart |
| 4.3.11 | `docs/features/f1.11-round-viewer-stub.md` | 📝 | Round Viewer Stub — форма+результат |
| 4.3.12 | `docs/features/f1.12-multiattack.md` | 📝 | MultiAttack — несколько оружий+отряд |
| 4.3.13 | `docs/features/f2.1-game-state.md` | 📝 | Game State Dataclass |
| 4.3.14 | `docs/features/f2.2-2d-map.md` | 📝 | 2D Map — NumPy grid, terrain |
| 4.3.15 | `docs/features/f2.3-line-of-sight.md` | 📝 | LoS — Bresenham ray casting |
| 4.3.16 | `docs/features/f2.4-missions.md` | 📝 | Missions — objectives, scoring |
| 4.3.17 | `docs/features/f2.5-game-loop.md` | 📝 | Game Loop — 6 фаз, run_round() |
| 4.3.18 | `docs/features/f2.6-phase-transitions.md` | 📝 | Phase Transitions — priority, alternating |
| 4.3.19 | `docs/features/f2.7-battle-shock-cp-stratagems.md` | 📝 | Battle-shock, CP, Stratagems |
| 4.3.20 | `docs/features/f2.8-victory-points.md` | 📝 | VP tracking, end-game conditions |
| 4.3.21 | `docs/features/f2.9-roster-validation.md` | 📝 | Roster Validation — PTS, Warlord, caps |
| 4.3.22 | `docs/features/f2.10-roster-crud.md` | 📝 | Roster CRUD — SQLite save/load |
| 4.3.23 | `docs/features/f2.11-team-builder-ui.md` | 📝 | Team Builder UI — Alpine.js |
| 4.3.24 | `docs/features/f2.12-leader-compatibility.md` | 📝 | Leader Compatibility Checker |

---

## 5️⃣ Wiki — Данные юнитов

```
wiki/ → ../wiki/
```

| Раздел | Кол-во | Детали |
|--------|--------|--------|
| `factions/` | 27 | 3 группы + 24 фракции (все фракции 40k) |
| `units/orks/` | 62 | 55 entities + 2 attached + 5 wargear |
| `units/tau/` | 41 | 39 entities + 1 attached + 1 wargear |
| `units/mechanicus/` | 9 | 4 entities + 5 Legends |
| `detachments/orks/` | 11 | Все детачменты орков |
| `detachments/tau/` | 4 | Все детачменты тау |
| `detachments/mechanicus/` | 2 | Eradication Cohort + Haloscreed |
| `stratagems/core/` | 12 | 11 core + 1 Core Stratagems index |
| `stratagems/orks/` | 42 | Все стратагемы орков |
| `stratagems/tau/` | 19 | Все стратагемы тау |
| `stratagems/mechanicus/` | 12 | Все стратагемы AdMech |
| `enhancements/orks/` | 44 | Все энхансменты орков |
| `enhancements/tau/` | 16 | Все энхансменты тау |
| `enhancements/mechanicus/` | 8 | Все энхансменты AdMech |
| `rules/9th/` | 13 | Правила 9-й редакции |
| `rules/10th/` | 16 | Правила 10ed + Waaagh!, FTGG, Battle-shock... |
| `concepts/` | 15 | Детачменты соседних фракций (stubs) |
| `queries/` | 2 | Architecture (C4), другие |

---

## Сводка

| Секция | Всего файлов | ✅ Готово | 🏗 В работе | ⚪ Пусто |
|--------|-------------|-----------|------------|----------|
| Корень | 10 | 10 | 0 | 0 |
| Backend | 22 | 4 | 9 | 9 |
| Web | 37 | 19 | 8 | 1 |
| Docs | 30 | 8 | 0 | 22 |
| **Итого (код)** | **99** | **41** | **17** | **22** |
| Wiki | ~360 | ~360 | — | — |
