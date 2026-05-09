# Agent Rules — Warpsmith

Этот файл управляет поведением AI-агентов при работе над проектом.
Обновлён: 2026-05-09 (соответствует v0.7.7).

## Языки и стек

| Слой         | Язык             | Фреймворк                |
| ------------ | ---------------- | ------------------------ |
| Backend      | Python 3.12+     | FastAPI + Pydantic v2    |
| HTML-шаблоны | Jinja2           | Tailwind CSS (CDN)       |
| Интерактив   | JavaScript (ES6) | HTMX 2.x + Alpine.js 3.x |
| Карта | JavaScript (ES6) | Scenario Setup: strategic SVG battlefield_map.js; replay: Canvas |
| База данных  | SQL (SQLite 3)   | sqlite3 (stdlib)         |
| Симуляции    | Python           | NumPy 2.x (Monte Carlo)  |
| Тесты        | Python           | pytest + pytest-cov      |

**Зависимости:** fastapi, uvicorn[standard], jinja2, numpy, python-multipart,
PyJWT[crypto], bcrypt, httpx, python-dotenv, pyyaml, python-frontmatter,
structlog, sentry-sdk[fastapi], slowapi, htmy, pytest, pytest-asyncio, pytest-cov
**Dev:** ruff, mypy, pre-commit

## Структура проекта

```
simulator/
├── main.py                   ← точка входа FastAPI
├── pyproject.toml            ← зависимости
├── ROADMAP.md                ← дорожная карта (7 фаз, ~81 фича, ~329h)
├── AGENTS.md                 ← этот файл
├── CHANGELOG.md              ← Keep a Changelog
├── DEV_INDEX.md              ← хаб разработчика
├── wiki/                     ← ~490 .md — данные в репозитории (monorepo)
│   ├── units/{faction}/      ← юниты (orks, tau, mechanicus)
│   ├── factions/             ← AI профили фракций
│   ├── detachments/{faction}/← детачменты
│   ├── enhancements/{faction}/← энхансменты
│   └── stratagems/           ← стратагемы
│
├── backend/
│   ├── auth/                 ← JWT, bcrypt, Cookie helpers
│   │   ├── __init__.py       ← User, create_jwt, hash_password, get_current_user
│   │   └── providers/        ← OAuth провайдеры
│   │       ├── base.py       ← OAuthProvider (ABC), PROVIDER_REGISTRY
│   │       ├── google.py     ← Google OAuth (OIDC)
│   │       ├── vk.py         ← VK OAuth (VK ID)
│   │       └── routes.py     ← /auth/{provider}/login, /callback, /providers
│   │
│   ├── billing/              ← Платежи и подписки
│   │   ├── plans.py          ← UserFeatures Feature Gate (Free/Premium)
│   │   ├── stripe_stub.py    ← Stripe заглушка для разработки
│   │   └── webhooks.py       ← /api/webhooks/stripe, /api/subscribe
│   │
│   ├── loader/               ← парсинг вики (.md → Python)
│   │   ├── registry.py       ← WikiRegistry (сканирование + кэш, Detachment/Stratagem/Enhancement)
│   │   ├── icon_map.py       ← ICON_MAP: 18 категорий, цвета, сортировка
│   │   └── parser.py         ← parse_unit() — YAML frontmatter → Unit
│   │
│   ├── model/                ← Data models
│   │   └── unit.py           ← Unit, Weapon dataclasses
│   │
│   ├── engine/               ← Симуляция боя
│   │   ├── dice.py           ← NumPy D6 pool
│   │   ├── combat.py         ← Hit → Wound → Save → Damage → FNP
│   │   ├── modifiers.py      ← ±1, Sustained, Lethal, Devastating, rerolls
│   │   ├── scenario.py       ← Game Loop (5 фаз): Command→Movement→Shooting→Charge→Fight
│   │   └── ai/               ← AI-поведение
│   │       ├── decision.py   ← Greedy Decision Engine (F3.1)
│   │       ├── deployment.py ← Zone placement AI (F3.4)
│   │       ├── faction_ai.py ← Wiki-driven FactionAIProfile
│   │       └── autoplay.py   ← AI vs AI full scenario (F3.5)
│   │
│   ├── state/                ← Игровое состояние
│   │   ├── game_state.py     ← Позиции, раны, CP, VP, GamePhase (5 members)
│   │   ├── map.py            ← 2D-карта (NumPy) + террейн + LoS
│   │   ├── mission.py        ← Миссии, метки целей, условия победы
│   │   └── roster.py         ← RosterState, validate_roster()
│   │
│   ├── db/                   ← SQLite persistence
│   │   └── database.py       ← SQLite wrapper + migrate() — auto-creates /data/ dir
│   │
│   └── reporter/             ← Вывод результатов
│       ├── table.py          ← Rich-таблицы в терминал
│       └── json_export.py    ← JSON-экспорт
│
├── web/
│   ├── routes/               ← FastAPI роуты
│   │   ├── pages.py          ← HTML: /, /team-builder, /scenario-setup, /pricing, /faction-browser, /replays, /my-rosters
│   │   ├── api.py                    ← core: /api/units, /api/simulate, /api/map, /api/health, /api/factions
│   │   ├── api_detachments.py        ← /api/detachments
│   │   ├── api_rosters.py            ← /api/rosters, /api/rosters/generate, /api/rosters/synergies (единственный owner roster CRUD)
│   │   ├── api_replays.py            ← /api/auto-play, /api/replays, /api/results
│   │   └── auth.py                   ← /register, /login, /logout, /api/me
│   │
│   ├── templates/            ← Jinja2-шаблоны
│   │   ├── base.html         ← Layout + auth header + B/E toggle + upgrade banner + ad
│   │   ├── index.html        ← Главная
│   │   ├── team_builder.html ← Сбор армии (полная модалка со статами/варгиром/оружием)
│   │   ├── scenario_setup.html← Выбор сторон, миссии, карты
│   │   ├── faction_browser.html
│   │   ├── round_viewer.html ← Пошаговый реплей (Canvas + Alpine)
│   │   ├── result.html       ← Итог битвы (Chart.js VP timeline, фазы, убийства)
│   │   ├── replays.html      ← Список реплеев
│   │   ├── my_rosters.html   ← CRUD сохранённых ростеров
│   │   ├── pricing.html      ← Free vs Premium
│   │   ├── auth/
│   │   │   ├── login.html
│   │   │   └── register.html
│   │   └── partials/         ← HTMX-фрагменты
│   │       ├── detachment_picker.html
│   │       ├── synergy_panel.html
│   │       ├── battlefield_map.html
│   │       ├── tooltip_definitions.html
│   │       ├── unit_card.html
│   │       └── unit_modal.html
│   │
│   └── static/
│       ├── team_builder.js          ← Alpine.js: ростер, PTS, save/load
│       ├── unit_modal.js            ← UnitModal mixin (F4.2)
│       ├── synergy_hints.js         ← SynergyHints controller (F4.4)
│       ├── detachment_picker.js     ← DetachmentPicker controller (F4.3)
│       ├── battlefield_map.js       ← Strategic SVG map (F4.14)
│       ├── scenario_setup.js        ← Отправка симуляции
│       ├── progressive_disclosure.js← B/E mode toggle (F4.6)
│       ├── my_rosters.js            ← CRUD операции с ростерами
│       ├── replay_viewer.js         ← Canvas + step-by-step реплей
│       ├── result_chart.js          ← Chart.js VP график + таблица фаз
│       ├── tooltips.js              ← STAT_TOOLTIPS + tooltipManager (F4.7)
│       ├── unit_card.css            ← Стили карточек юнитов
│       └── icons/*.svg              ← 18 категорийных иконок
│
├── docs/
│   ├── architecture/
│   │   ├── C4.md             ← 4 уровня контейнеров (+Auth, Billing, OAuth)
│   │   └── ADR.md            ← 11 архитектурных решений
│   └── features/
│       └── Features_index.md ← указатель на все feature-спеки (Phase 1–7, 77 фич)
│
└── tests/                    ← 41 файл, 451+ тестов
```

## Правила разработки

### 1. Код
- **Python:** PEP 8, строгие type hints (`def foo(bar: str) -> int:`)
- **FastAPI:** Pydantic v2 для валидации request/response
- **🚫 НИКАКОГО ХАРДКОДА где есть угроза масштабирования:**
  - Списки фракций, детачментов, стратагем — только из вики или API.
    Никогда не хардкодить в HTML или Python-словарях.
  - Если данные живут в вики (`.md` файлы) — читать оттуда.
    Единственное исключение — label для отображения (можно
    генерировать из id через `.replace("-", " ").title()`).
  - Новый функционал должен добавляться через контент (wiki),
    а не через изменение кода.
  - `web/templates/` — никаких хардкодных `<option>`, `<template x-if>`
    для списков. Только `x-for` с данными из `/api/*`.
- **SQLite:** raw SQL через `sqlite3` (stdlib). DB_PATH на Railway — `/data/simulator.db` с Volume
- **JS:** ES6, без TypeScript
- **Warlord для ростеров:** если в ростере несколько Character/Warlord-capable юнитов, Team Builder и API требуют ровно один явный `is_warlord: true`; в roster panel рядом с eligible юнитами есть кнопка `👑`, при добавлении второго eligible юнита прежний implicit выбор сбрасывается, Save disabled до клика по одной короне; флаг хранится в `units` JSON вместе с loadout/weapons/pts.
- **Generated opponent:** `/api/rosters/generate` обязан возвращать save-and-play ростер: `squad_size` из YAML `unit.squad_size["min"]`, ровно один Warlord, points в лимите, Scenario Setup редиректит по top-level `game_id`.
- **Terrain 10e:** F2.13 — упрощённый baseline. Для новых terrain/cover/LoS задач сначала читать `wiki/raw/papers/Terrain.md` и `docs/features/f2.18-terrain-mechanics-10e.md`: ruins блокируют LoS через footprint, woods дают cover/not fully visible без полного LoS block, barricades дают 2" engagement только через barricade, Plunging Fire даёт AP -1 с высоты >6".

### 2. Тесты
- **pytest** для всех backend-компонентов
- Каждый модуль engine/ имеет отдельный test-файл
- `pytest tests/ -q` — 454 теста, 41 файл, 3 skipped
- Перед запуском: `rm -f *.db-shm *.db-wal` (SQLite WAL recovery)
- Monte Carlo тесты: `numpy.random.seed(42)` для воспроизводимости

### 3. Данные
- **Единственный источник правды:** `simulator/wiki/` (YAML frontmatter + markdown) — часть репозитория
- Wiki → читается через WikiRegistry при старте → in-memory кэш
- **Миграции БД:** raw SQL в `Database.migrate()` (CREATE TABLE IF NOT EXISTS)
- **Кэш:** pickle-файл Registry для быстрого старта
- **squad_size** в YAML frontmatter: `{min: N, max: M, step: S}` — стоимость points указана за минимальный состав
- **tags** в YAML frontmatter: список категорий юнита (infantry, vehicle, character, battleline, fly, etc.)

### 4. Git
- Репозиторий: `fixemer90-stack/Warpsmith` на GitHub
- Коммиты: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`
- Ветки: `main`, `feat/<name>`, `fix/<name>`, `docs/<name>`
- Версионирование: ZeroVer `v0.<PHASE>.<PATCH>` (см. RELEASE.md)
- Push с Windows/WSL — пользователь пушит вручную
- `.gitignore`: `__pycache__/`, `.env`, `*.db`, `.test-credentials`

### 5. Фронт
- **HTMX** — partial updates (hx-post, hx-get, hx-target)
- **Alpine.js** — реактивное состояние (x-data, x-model, x-init, x-if)
- **Tailwind** — через CDN, никаких билдов
- Scenario Setup карта — SVG battlefield map с mission objectives, roster units и 6″/12″ scale (`battlefield_map.js`)
- **Progressive Disclosure** — 2 режима: Beginner (полные названия) / Expert (сокращения M,T,SV,W,LD,OC)
  CSS-классы `.mode-beginner` / `.mode-expert` на body
- **SVG иконки** — inline через Jinja2 helpers `unit_icon()` и `card_style()`
- **PTS формула:** `ptsPerModel = unit.points / squad_size.min`.
  `totalCost = (ptsPerModel + loadoutPts) × squadSize + nobPts`.
  Итог сохраняется в ростере как pts, `totalPts = sum(pts)`.
- **icon_tags:** API возвращает ВСЕ tags юнита без фильтрации (user explicitly rejected dedup).

### 6. Game Loop (10th Edition)
```
5 фаз: Command → Movement → Shooting → Charge → Fight
```
- **Command:** CP generation (+1/player), battle-shock tests (встроены, нет отдельной Morale фазы), VP scoring
- **Movement:** Normal Move (M"), Advance (+D6", нельзя стрелять/заряжаться), Fall Back (отход, нельзя стрелять/заряжаться)
- **Shooting:** выбор цели по дальности оружия + LoS, faction target_priority bias
- **Charge:** 2D6 ≥ расстояние до ближайшего врага. Melee-юниты никогда не Advancят
- **Fight:** alternating activations, упрощённый melee (1 damage per attack)

### 7. Movement AI
- Юниты назначаются на объективы (ближайший к юниту)
- Melee-юниты **пропускают** объективы если `charge_aggression > 1.0` в faction profile → идут на врага
- Оставшиеся без назначения → ближайший враг
- Движение останавливается за 1.5 клетки от врага (не входит в Engagement Range)
- Ranged-юниты всегда держат точки

### 8. PTS валидация (бэкенд)
`validate_roster()` проверяет:
- PTS лимит (points / minSquad × squadSize)
- Squad size в пределах `unit.squad_size.{min, max}`
- 3 копии юнита (6 для Battleline)
- Уникальность Epic Heroes
- Наличие Warlord
- Непустой ростер

### 9. Добавление новой фракции
1. Создать `wiki/factions/<Name>.md` — описание фракции + YAML `ai:` секция с weights/behaviors
2. Создать `wiki/units/<faction>/<Unit Name>.md` — каждый юнит
3. Создать `wiki/detachments/<faction>/<Detachment>.md` — каждый детачмент (с YAML detachment_rule, stratagems, enhancements)
4. Создать `wiki/enhancements/<faction>/<Enhancement>.md` — энхансменты
5. **Код менять не нужно** — AI загружается через `load_profile()` из YAML `ai:` секции, юниты/детачменты — через WikiRegistry

### 10. Деплой
- **Production:** Railway (`warpsmith-production.up.railway.app`)
- Dockerfile, wiki входит в образ автоматически
- **DB_PATH=/data/simulator.db** — SQLite на Railway. Необходим Volume, смонтированный в `/data` для персистентности
- `HOSTING=true` — production-режим (Secure cookie, без reload)
- Ветка по умолчанию: `main` (Railway тянет из неё)

## Архитектура (C4 Level 2)

```mermaid
graph TB
    subgraph Browser["🌐 Браузер"]
        HTML["Jinja2 HTML"]
        HTMX["HTMX"]
        ALPINE["Alpine.js"]
        STORAGE["localStorage"]
    end

    subgraph Backend["⚙️ FastAPI"]
        AUTH["🔐 Auth: JWT + OAuth"]
        API["📡 JSON API"]
        BILL["💳 Billing + Feature Gate"]
        ENGINE["⚙️ Combat + Game Loop"]
        AI["🧠 AI Engine (FactionAIProfile)"]
        LOADER["📥 Wiki Loader (monorepo)"]
    end

    subgraph Data["🗄 Data"]
        WIKI["📚 simulator/wiki/ .md"]
        DB["SQLite /data/simulator.db"]
    end

    subgraph External["🌍 External"]
        OAUTH["🔑 Google/VK"]
        STRIPE["💳 Stripe"]
        RAILWAY["🚂 Railway (prod)"]
    end

    HTML -->|HTMX| API
    ALPINE -->|fetch| API
    API --> AUTH
    API --> BILL
    API --> ENGINE
    ENGINE --> AI
    LOADER --> WIKI
    AUTH --> DB
    BILL --> DB
    AUTH -->|OAuth| OAUTH
    BILL -->|Webhook| STRIPE
    APP -->|Docker| RAILWAY
```

## Роли и доступ (Authorization)

| Ресурс | Free | Premium | Guest |
|--------|------|---------|-------|
| Team Builder | ✅ 1 roster | ✅ unlimited | ✅ localStorage |
| Simulation | ✅ basic AI | ✅ full AI | ❌ |
| Export | ❌ | ✅ | ❌ |
| Public rosters | view only | create + view | view only |
| Ads | ✅ shown | ❌ hidden | ✅ shown |
| Priority | queue | instant | queue |
