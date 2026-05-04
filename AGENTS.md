# Agent Rules — Warpsmith

Этот файл управляет поведением AI-агентов при работе над проектом.
Обновлён: 2026-05-04 (соответствует v0.7.0).

## Языки и стек

| Слой | Язык | Фреймворк |
|------|------|-----------|
| Backend | Python 3.12+ | FastAPI + Pydantic v2 |
| HTML-шаблоны | Jinja2 | Tailwind CSS (CDN) |
| Интерактив | JavaScript (ES6) | HTMX 2.x + Alpine.js 3.x |
| Карта | JavaScript (ES6) | Canvas API (vanilla) |
| База данных | SQL (SQLite 3) | sqlite3 (stdlib) |
| Симуляции | Python | NumPy 2.x (Monte Carlo) |
| Тесты | Python | pytest + pytest-cov |

**Зависимости:** fastapi, uvicorn, jinja2, numpy, python-multipart, python-jose[cryptography],
bcrypt, httpx, python-dotenv, pyyaml, python-frontmatter, pytest, pytest-cov

## Структура проекта

```
simulator/
├── main.py                   ← точка входа FastAPI
├── pyproject.toml            ← зависимости
├── ROADMAP.md                ← дорожная карта (7 фаз, ~75 фич)
├── AGENTS.md                 ← этот файл
├── DEV_INDEX.md              ← хаб разработчика
├── wiki/                     ← ~490 .md — данные в репозитории (monorepo)
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
│   │   ├── scenario.py       ← Game Loop: Deployment → Round → End
│   │   └── ai/               ← AI-поведение
│   │       ├── decision.py   ← Greedy Decision Engine (F3.1)
│   │       ├── deployment.py ← Zone placement AI (F3.4)
│   │       ├── faction_ai.py ← Wiki-driven FactionAIProfile (F3.2 — deprecates ork/tau/admech AI)
│   │       └── autoplay.py   ← AI vs AI full scenario (F3.5)
│   │
│   ├── state/                ← Игровое состояние
│   │   ├── game_state.py     ← Позиции, раны, CP, VP
│   │   ├── map.py            ← 2D-карта (NumPy) + террейн + LoS
│   │   └── mission.py        ← Миссии, метки целей, условия победы
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
│   │   ├── pages.py          ← HTML: /, /team-builder, /scenario-setup, /pricing, /faction-browser
│   │   ├── api.py            ← JSON: /api/units, /api/rosters, /api/simulate, /api/detachments, /api/map/tiles, /api/rosters/synergies
│   │   └── auth.py           ← /register, /login, /logout, /api/me
│   │
│   ├── templates/            ← Jinja2-шаблоны
│   │   ├── base.html         ← Layout + auth header + B/I/E toggle + upgrade banner + ad
│   │   ├── index.html        ← Главная
│   │   ├── team_builder.html ← Сбор армии (полная модалка со статами/варгиром/оружием)
│   │   ├── scenario_setup.html
│   │   ├── faction_browser.html
│   │   ├── round_viewer.html
│   │   ├── pricing.html      ← Free vs Premium
│   │   ├── auth/
│   │   │   ├── login.html
│   │   │   └── register.html
│   │   └── partials/         ← HTMX-фрагменты
│   │       ├── detachment_picker.html
│   │       ├── synergy_panel.html
│   │       ├── canvas_map.html
│   │       ├── tooltip_definitions.html
│   │       └── unit_card.html
│   │
│   └── static/
│       ├── team_builder.js          ← Alpine.js: ростер, PTS, save/load
│       ├── unit_modal.js            ← UnitModal mixin (F4.2)
│       ├── synergy_hints.js         ← SynergyHints controller (F4.4)
│       ├── detachment_picker.js     ← DetachmentPicker controller (F4.3)
│       ├── canvas_map.js            ← CanvasMap controller (F4.5)
│       ├── progressive_disclosure.js ← B/I/E mode toggle (F4.6)
│       ├── tooltips.js              ← STAT_TOOLTIPS + tooltipManager (F4.7)
│       ├── unit_card.css            ← Стили карточек юнитов
│       └── icons/*.svg              ← 18 категорийных иконок
│
├── docs/
│   ├── architecture/
│   │   ├── C4.md             ← 4 уровня контейнеров (+Auth, Billing, OAuth)
│   │   └── ADR.md            ← 11 архитектурных решений
│   └── features/
│       └── Features_index.md ← указатель на все feature-спеки (Phase 1–7)
│
└── tests/                    ← 29 файлов, ~340 тестов
    ├── test_combat.py
    ├── test_faction_ai.py
    ├── test_ai_decision.py
    ├── test_detachment_picker.py
    ├── test_synergy_hints.py
    ├── test_tooltips.py
    ├── test_progressive_disclosure.py
    ├── test_unit_modal.py
    ├── test_docker.py
    └── ...
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
- **SQLite:** raw SQL через `sqlite3` (stdlib). DB_PATH на Railway — `/data/simulator.db`
- **JS:** ES6, без TypeScript

### 2. Тесты
- **pytest** для всех backend-компонентов
- Каждый модуль engine/ имеет отдельный test-файл
- `pytest tests/ --cov=backend/engine` — coverage > 80%
- Monte Carlo тесты: `numpy.random.seed(42)` для воспроизводимости

### 3. Данные
- **Единственный источник правды:** `simulator/wiki/` (YAML frontmatter + markdown) — часть репозитория
- Wiki → читается через WikiRegistry при старте → in-memory кэш
- **Миграции БД:** raw SQL в `Database.migrate()` (CREATE TABLE IF NOT EXISTS)
- **Кэш:** pickle-файл Registry для быстрого старта

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
- Карта — `<canvas>` с позиционированием (canvas_map.js)
- **Progressive Disclosure** — B/I/E режим через CSS-классы `mode-beginner/mode-intermediate/mode-expert`
- **SVG иконки** — inline через Jinja2 helpers `unit_icon()` и `card_style()`

### 6. Добавление новой фракции
1. Создать `wiki/factions/<Name>.md` — описание фракции + YAML `ai:` секция с weights/behaviors
2. Создать `wiki/units/<faction>/<Unit Name>.md` — каждый юнит
3. Создать `wiki/detachments/<faction>/<Detachment>.md` — каждый детачмент (с YAML detachment_rule, stratagems, enhancements)
4. Создать `wiki/enhancements/<faction>/<Enhancement>.md` — энхансменты
5. **Код менять не нужно** — AI загружается через `load_profile()` из YAML `ai:` секции, юниты/детачменты — через WikiRegistry

### 7. Деплой
- **Production:** Railway (`warpsmith-production.up.railway.app`)
- Dockerfile + multi-stage build, wiki входит в образ автоматически
- `DB_PATH=/data/simulator.db` — SQLite на Railway (ephemeral, воссоздаётся при перезапуске)
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
