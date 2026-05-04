# Changelog — Warpsmith

Все заметные изменения проекта фиксируются в этом файле.

Формат: [Keep a Changelog](https://keepachangelog.com/)
Версионирование: ZeroVer `v0.<PHASE>.<PATCH>` — см. [RELEASE.md](RELEASE.md)

---

## 2026-05-04

### Added
- **F5.5 Logging (structlog) + Sentry error tracking** — `backend/logging_setup.py` (создано), `main.py` (патч — инициализация structlog + Sentry), `.env.example` (добавлен SENTRY_DSN, LOG_LEVEL) — структурированное JSON логирование в production, цветное в dev, логирование каждого HTTP-запроса с request_id, duration_ms, status_code, отправка необработанных исключений в Sentry
- **F5.6 CI/CD — GitHub Actions (lint + test + deploy)** — `.github/workflows/ci.yml` (lint: ruff + mypy, test: pytest с coverage > 80%, docker: build + push в GHCR), `.github/workflows/deploy.yml` (deploy: Dokku/Railway после успешного CI), `tests/test_coverage.py` (порог покрытия), обновлен `pyproject.toml` с `--cov-fail-under=80`
- **F5.2 Deployment** — `Procfile`, `app.json`, `deploy/dokku-setup.sh`, `deploy/railway.json`, `deploy/systemd.service`, `docs/deployment.md` — поддерживает 3 сценария: Dokku (git push + letsencrypt + volume), Railway (serverless + Dockerfile), self-host (systemd + nginx + certbot)
- **F4.6 Progressive Disclosure** — `web/static/progressive_disclosure.js`: Alpine.js контроллер с тремя режимами (Beginner/Intermediate/Expert), localStorage, CSS классы `mode-beginner/mode-intermediate/mode-expert` на `<body>`, переключатель B/I/E в хедере; unit cards показывают beginner-friendly/expert-only контент
- **Тесты F4.6** — `tests/test_progressive_disclosure.py`: 7 тестов (toggle, CSS, JS, mode-классы)
- **F4.7 Stat Tooltips** — `web/static/tooltips.js`: STAT_TOOLTIPS с 6 статами (M/T/SV/W/LD/OC), tooltipManager Alpine.js компонент с hover-попапом, auto-flip по краям экрана, glossary модалка по клику; `web/templates/partials/tooltip_definitions.html`; `data-stat` атрибуты на всех статах в team_builder
- **Тесты F4.7** — `tests/test_tooltips.py`: 10 тестов (JS включён, партиал, все 6 data-stat атрибутов)
- F4.8 SVG icons — `web/static/icons/legends.svg` (tombstone), `_unit_icons()` включает `legends` в priority, `icon_map.py` загружает все SVG динамически
- API `/api/detachments` — эндпоинт возвращает `rule_name`, `rule_description`, `stratagem_count`, `enhancement_count` для inline preview
|- Wiki YAML детачментов — `detachment_rule`, `stratagems`, `enhancements` добавлены в frontmatter 21 файла
- **F4.9 Generate Random Opponent** — `POST /api/rosters/generate` для AI-ростера. Добавлен в ROADMAP.md, Features_index.md, создана feature-спека `f4.9-generate-opponent.md`

### Changed
|- **Wiki → Monorepo (fix Railway deploy)** — wiki-хранилище (489 файлов, 35 MB) перемещено из внешнего `/mnt/d/Python/Balthier/wiki/` в `simulator/wiki/`. Данные теперь — часть репозитория, попадают в Docker-образ автоматически.
  - `.dockerignore`: удалена строка `wiki/` — **это была коренная причина пустого Railway**
  - `.gitignore`: `wiki/` больше не игнорируется (комментарий обновлён)
  - `backend/loader/registry.py`: убраны хардкодные пути `/mnt/d/Python/Balthier/wiki` и `/mnt/d/Python/Maksim/wiki`
  - `tests/test_docker.py`: проверка `.dockerignore` обновлена
  - Локально проверено: 160 юнитов, 23 детачмента, 3 фракции
- **Версия 0.6.0 → 0.6.6** — `pyproject.toml`, `README.md`, `AGENTS.md`, `DEV_INDEX.md`
- **AGENTS.md** — полный рерайт под v0.6.6: актуальная структура проекта, AI через F3.2 Faction AI Profiles (не ork_ai/tau_ai), wiki monorepo, Railway deploy, 18 SVG иконок, все JS-файлы
- **README.md** — переписан под Railway: убран `cd /mnt/d/Python/Balthier/simulator`, все ссылки на `warpsmith-production.up.railway.app`, Phase 3 → 71%, Phase 4 → 9 фич
- **F2.1 Game State doc** — приведён в соответствие с реальным кодом: `RosterState → PlayerState`, `players: dict` вместо `roster_a/roster_b`, `GamePhase` enum, `next_phase()` метод
- **F2.5 Game Loop doc** — переписан под актуальный GameState API. Статус: `done → wip`
- **F3.1 Decision Engine doc** — `EvaluationContext.opponent: RosterState` → `opponent_units: list[UnitState]`, Integration под `state.players`
- **F2.4 Missions doc** — `score_kill_points()` через `state.players[id]`, тесты под актуальный конструктор
- **F3.4 Deployment AI doc** — `place_units()` сигнатура под актуальный код, `warlord_unit_name`
- **F3.5 Autoplay doc** — переписан под реальное состояние: ✅/🟡/❌, разрыв старого API, TODO на завершение
- **ROADMAP.md** — Phase 4: 9/9 features (+F4.9), Features_index.md обновлён

### Fixed
|- **Auth 500 на Railway** — `/data/` директория не существовала. `database.py`: `connect()` создаёт родительскую директорию через `os.makedirs(exist_ok=True)`
|- **F4.2 Unit Modal** — создан `web/static/unit_modal.js`. HTML модалки расширен до полного datasheet: stats strip, squad stepper, wargear, weapons table, total cost
|- **F4.8 SVG Icons** — создан `web/templates/partials/unit_card.html`. Jinja2 globals `unit_icon`, `card_style`, `CATEGORY_COLORS` в main.py, pages.py, auth.py
|- **F3.5 Autoplay — импорты** — `DecisionEngine` (не существовал) → `choose_action`, `RosterState` → из `roster.py`, `BattlefieldMap` без `terrain` → с `np.full`
|- **F3.5 Autoplay — тесты** — `test_autoplay.py` переписан под актуальные `Weapon`, `Unit`, `Mission` API
|- **F3.5 RosterState** — добавлен `@dataclass RosterState` в `backend/state/roster.py`
|- **Generate Opponent — 405** — `/api/rosters/generate`: `POST` → `GET` (фронт вызывал `fetch` без `method: 'POST'`)
|- **F3.5 Autoplay AI vs AI** — `backend/engine/ai/autoplay.py` переписан: `run_auto_game(roster_a: RosterState, roster_b: RosterState, mission_name, config)`. Создаёт `GameState(players=...)`, использует `Scenario.run_round()` для game loop, `deploy_game()` для размещения. 16 тестов (было 5/12)
|- **F3.6 Replay Recording** — `backend/engine/replay.py` исправлен под актуальный `GameState` (`state.players` вместо `roster_a/b`), `UnitState` поля (`name`, `models_remaining`), tuple-позиции. 18 тестов (было 14 с 4 known-fail)
|- **Парсинг оружия (header-aware)** — `backend/loader/parser.py`: `_parse_weapons_from_markdown()` переписан на динамическое маппинг колонок по заголовкам таблицы. Поддержка русских/английских заголовков, 8/9 колонок, `N/A` skill (torrent), `—`/`-` во всех полях, dice-выражения в strength. Колонка `range` опциональна — если таблица использует `тип`/`type` вместо отдельной `Range`, range подставляется из неё. `_clean_range()`: `re.match` → `re.search` (извлекает число из `"Ranged 24"`). 0→406→410 оружий распарсено, 10 осталось (wiki data quality)
|- **Dockerfile single-stage** — убран мультистейдж, `build-essential`, `COPY --from=builder`. `FROM python:3.12-slim`, `pip install -e .` через manylinux wheels. Нет ABI mismatch
|- **PyJWT вместо python-jose** — `pyproject.toml`: `python-jose[cryptography]` → `PyJWT[crypto]>=2.8`. Код делает `import jwt`, а `python-jose` даёт `import jose` — это было причиной 500 на Railway
|- **`.dockerignore` — wiki excluded** — `*.md` заменено на `docs/`. Wiki (`.md` файлы) теперь копируется в Docker-образ
|- **`/api/rosters/generate` — 401** — роут был зарегистрирован ПОСЛЕ `/rosters/{roster_id}` (с auth). FastAPI матчил `generate` как `{roster_id}` → вызывал `get_roster()` с `Depends(get_current_user)`. Перемещён перед динамическим роутом
|- **`team_builder.js` — saveRoster** — переписан: валидация полей (`name`, `faction`, PTS), ошибки в `validationErrors` (inline, без `alert`), `errorData.detail.validation_errors` распаковывается корректно. Убран дубликат `detachment: ''`. `this.units` → `this._units`
|- **Auth bcrypt — Docker fix** — bcrypt C-расширение не загружалось на Railway: скомпилированный `.so` из builder-стадии не подходил runtime (различия libc между кэшированными слоями). Фикс: `pip install bcrypt` в runtime-стадии (manylinux wheel, не требует gcc)
|- Team Builder: дублирование заголовка, два селекта Detachment, `@change="loadUnits()"` → `@change="onFactionChange()"`
|- Detachment Picker: collapsed/expand, `detachment_picker.js` не подгружался
|- YAML parsing: апострофы в `'Ere We Go` и `'Ard as Nails`
|- WatchFiles reload отключён

### Implemented
|- **F2.5 Game Loop** — реализованы все 6 фаз в `backend/engine/scenario.py`:
  - Command: CP генерация, warlord bonus, VP scoring (было)
  - Movement: юниты двигаются к центру карты, Fall Back из engagement
  - Shooting: поиск целей в радиусе 12, при наличии unit_models — Monte Carlo combat engine (F1.6)
  - Charge: 2D6 roll, engagement при успехе
  - Fight: alternating activations, melee resolution
  - Morale: battle-shock тесты (2D6, snake eyes/boxcars)
  - `Scenario.__init__`: добавлен опциональный `unit_models: dict[str, Unit]` и `battlefield: BattlefieldMap` для LoS
|- **F2.3 Line of Sight** — Bresenham ray casting в `BattlefieldMap.has_los()`. IMPASSABLE terrain блокирует LoS, старт/финиш не проверяются, результаты кэшируются. Подключён к `Scenario._shooting_phase()`

## 2026-05-03

### Added
- **F3.2 Faction AI Profiles** — `backend/engine/ai/faction_ai.py`: FactionAIProfile, load_profile() из YAML ai: секции wiki/factions/*.md, get_weights() с учётом активных behaviors (Waaagh!, Kauyon, Mont'ka, Doctrina Imperatives), get_target_multiplier(), get_active_behavior_override(), choose_action_with_faction_ai() для интеграции с F3.1
- **Тесты F3.2** — `tests/test_faction_ai.py`: 18 тестов (загрузка профилей 3 фракций, активация behaviors, cooldown, target_priority, action_override, deployment)
- **F3.1 Greedy Decision Engine** — `backend/engine/ai/decision.py`: ActionType, Action, EvaluationContext, choose_action() с взвешенной оценкой (shoot/charge/move), генерация кандидатов по фазам, поддержка opponent_units_map для статов целей
- **F4.3 Detachment Picker with Rule Preview** — `backend/loader/registry.py` расширение с Detachment/Stratagem/Enhancement классами, `/api/detachments` endpoints, `web/templates/partials/detachment_picker.html`, `web/static/detachment_picker.js` с HTMX reactive loading и detail modal
- **F4.4 Synergy Hints: Leader Compatibility, Transport Capacity** — `/api/rosters/synergies` endpoint с SynergyCheck моделью, `web/templates/partials/synergy_panel.html`, `web/static/synergy_hints.js` с 500ms debouncing, визуальные индикаторы (dots/borders) в roster списке, wiki synergies из YAML
- **Тесты F3.1** — `tests/test_ai_decision.py`: 26 тестов (дистанция, дальность, ожидаемый урон, генерация кандидатов, скоринг, choose_action, custom weights)
- **Тесты F4.3** — `tests/test_detachment_picker.py`: 12 тестов (API endpoints, data structures, integration)
- **Тесты F4.4** — `tests/test_synergy_hints.py`: 12 тестов (synergy checks, transport capacity, visual indicators)
- GET /api/rosters/generate — эндпоинт для генерации случайного валидного ростера AI-оппонента (Warlord, 3x cap, Epic Hero unique, PTS budget)
- get_current_user_optional — опциональная аутентификация (возвращает None вместо 401)
- Scenario Setup UI — выбор ростера для Player 1 / Player 2, кнопка "Generate Random Opponent", выбор миссии/карты/очередности хода
- Epic Hero — отдельная категория в парсере и UI (выше Character)
- SVG иконки для юнитов — маппинг из YAML tags, несколько иконок на юнит (vehicle+fly), отображение после имени
- Kroot Hunting Pack — новый детачмент Tau (5 детачментов)
- Transport — приоритет выше Vehicle в категориях
- Legends — отдельная категория для Legends-юнитов
- Feature specs для Phase 3 (8 файлов), Phase 4 (8 файлов), Phase 5 (7 файлов)

### Changed
- **Phase 4: Web UI Polish** — 4/8 features реализованы (50%): F4.1 (Faction Browser), F4.2 (Unit Modal), F4.3 (Detachment Picker), F4.4 (Synergy Hints)
- **Архитектура AI: хардкод → wiki-driven**. F3.2, F3.3, F3.9 (Ork/Tau/AdMech AI) объединены в один [F3.2 Faction AI Profiles](docs/features/f3.2-faction-ai-profiles.md). Все поведенческие параметры читаются из YAML `ai:` секции wiki/factions/*.md. Новая фракция = новый .md, ноль строк Python.
- Версия: 0.4.0 → путь к 0.5.0 (Phase 3 начата)
- `_infer_category`: добавлены приоритеты epic-hero, transport, legends; Character не перекрывает Monster/Vehicle
- `can_be_warlord`: авто-определение из YAML tags + body keywords (47 кандидатов вместо 1)
- Wiki loader: поле `tags` добавлено в Unit dataclass и LIST_FIELDS
- Points: добавлены PTS для 21 не-Legends юнита (Orks: Beastboss 80, Big Mek 90, Breaka Boyz 140, Tankbustas 140 и др.; Tau: Broadside 80, Cadre Fireblade 50, Ethereal 50 и др.)
- `flyer.svg` → `fly.svg` (совпадение с YAML тегом)
- Save formula в decision engine: AP правильно ухудшает save; fail_save = (effective - 1)/6
- Wound table: корректная 10th edition (S ≥ 2T → 2+, S > T → 3+, S == T → 4+)

### Fixed
- `/api/units?faction=...` — баг: `result` объявлялся только внутри else-блока (500 при указании фракции)
- `/api/detachments?faction=adeptus-mechanicus` — маппинг faction ID → directory name через _faction_detachment_dir()
- main.py — роуты не грузились при импорте `main:app` (uvicorn) из-за вызова create_app() только в `if __name__`
- TemplateResponse — Starlette 1.0 сигнатура (request, name, context) вместо (name, context)
- Team Builder — gameSize пропадал при git merge (NaN pts); _units не был реактивным (категории не отображались)
---

## [0.4.0] — 2026-05-02

### Added
- **Phase 2: Game System завершена!**
- F2.8 Victory Points tracking and end-game conditions: VPTracker, GameResult, check_end_game with VP cap (100), army wipe, max rounds conditions; scoring functions (standard, progressive, kill_points)
- F2.11 Team Builder UI: faction picker, unit modal with squad size selection, real-time PTS bar, validation, save/load via /api/rosters
- F2.12 Leader Compatibility Checker: leader compatibility validation with rules for is_leader, leader_for list, max 2 leaders per unit, captain/lieutenant restrictions
- F2.1 Game State dataclass: `UnitState`, `PlayerState`, `GameState` с позициями, ранами, CP, VP, раундами
- F2.1 Методы для движения юнитов, повреждений, переходов фаз, определения победителя
- Тесты `tests/test_game_state.py` для управления состоянием игры
- F2.2 2D Map: `BattlefieldMap` с NumPy terrain array, deployment zones, objectives
- F2.2 Mission maps: Dawn of War, Spearhead с правильными зонами развертывания
- Тесты `tests/test_map.py` для карт, зон развертывания и pathfinding
- F2.3 Line of Sight: `LineOfSightCalculator` с ray casting алгоритмом
- F2.3 Методы: `has_line_of_sight()`, `can_shoot_at()`, `can_charge_at()`, cover detection
- Тесты `tests/test_line_of_sight.py` для видимости и стрельбы
- F2.4 Missions: система миссий с правилами высадки, условиями захвата точек и подсчётом VP
- F2.4 Три готовые миссии: Only War, Purge the Foe, Take and Hold
- F2.4 Тесты `tests/test_mission.py` для системы миссий
- F2.5 Game Loop: реализован игровой цикл с фазами Command → Movement → Shooting → Charge → Fight
- F2.5 Класс `Scenario` в `backend/engine/scenario.py` для управления игровым процессом
- F2.5 Тесты `tests/test_scenario.py` для игрового цикла
- F2.6 Phase Transitions: реализованы механизмы чередования активаций в фазе Fight и определение Command Priority
- F2.6 Добавлены поля `command_priority` в `PlayerState`, `is_engaged` и `is_fighting` в `UnitState`
- F2.6 Добавлен метод `_determine_command_priority` в `GameState` для swap-правил приоритета
- F2.6 Расширен `Scenario._fight_phase` с логикой чередующихся активаций
- F2.6 Тесты `tests/test_phase_transitions.py` для проверки приоритета и чередующихся активаций
- F2.7 Battle-shock, CP Generation, Stratagems: реализованы механизмы моральных тестов, генерации командных очков и фреймворк стратагем
- F2.7 Добавлено поле `is_battle_shocked` в `UnitState` и метод `is_above_half_strength`
- F2.7 Расширена генерация CP в `_command_phase`: +1 базовый +1 за warlord с лимитом Leviathan (10 CP)
- F2.7 Реализована логика battle-shock тестов в `_morale_phase` с правилами snake eyes/boxcars
- F2.7 Создан `backend/engine/stratagems.py` со фреймворком стратагем и базовыми стратагемами (Command Re-roll, Insane Bravery, Counter-Offensive, Tank Shock)
- F2.7 Тесты `tests/test_f2_7_battle_shock_cp_stratagems.py` для battle-shock, CP генерации и стратагем

### Changed
- Версия: 0.3.0 → 0.4.0 (Phase 2 завершена, начинается Phase 3)

---

## [0.2.1] — 2026-05-01

### Added
- F1.1 `Unit` dataclass: добавлены `invulnerable_save`, `feel_no_pain`, `wargear_options`, `transports`
- F1.1 `WargearSlot` dataclass для описания слотов варгира и вариантов выбора
- F1.1 методы `effective_toughness()`, `best_save()`, `max_wounds_in_squad()`
- Тесты `tests/test_unit.py` для `Unit` и `WargearSlot`
- F1.2 `DiceExpr` helpers: `parse_dice_expression()`, `resolve_dice()`, `dice_expr_to_str()`
- Тесты `tests/test_weapon.py` для dice expression parsing и нового `Weapon`
- F1.3 `backend/engine/modifiers.py`: модификаторы шагов боя, conditional checks, weapon tag mapping, reroll rules
- Тесты `tests/test_modifiers.py` для `apply_modifiers()`, `build_weapon_modifiers()` и `should_reroll()`
- F1.4 `backend/loader/parser.py`: парсинг frontmatter, markdown-таблиц и bullet weapon profiles в `Unit`/`Weapon`
- F1.4 `backend/loader/schema.py`: coercion helpers для wiki frontmatter
- F1.4 `backend/loader/registry.py`: загрузка даташитов, кэш через pickle, безопасная инициализация singleton registry
- Тесты `tests/test_parser.py` для frontmatter parsing, markdown weapon tables, registry cache и реального `Boyz.md`
- F1.5 `backend/engine/dice.py`: `DicePool`, `SimulationStats`, `compute_stats()` и batched Monte Carlo simulation helpers
- Тесты `tests/test_dice.py` для range checks, reproducibility, `simulate()` и агрегирования статистики
- F1.6 `backend/engine/combat.py`: `simulate_weapon_attack()`, `CombatResult` и полный pipeline Hit → Wound → Save → Damage → FNP
- Тесты `tests/test_combat.py` для `Shoota vs Marine`, `Heavy Bolter vs Marine`, natural 1/6 и `Feel No Pain`
- F1.7 `backend/engine/modifiers.py`: `TAG_TO_MODIFIERS`, `CriticalEffect`, `AntiKeyword`, `parse_anti_tag()` и critical keyword handling
- F1.7 `backend/engine/combat.py`: интеграция `sustained_hits`, `lethal_hits`, `devastating_wounds`, `blast`, `rapid_fire_*` и `anti_*`
- Тесты keyword-логики для crit effects, `anti_infantry`, `blast` и `rapid_fire`
- F1.8 Плазма-оружие: механика перезарядки (overcharge) для плазменных орудий
- Тесты `tests/test_combat.py` для сравнения обычной и перезаряженной плазмы
- F1.9 POST `/api/simulate`: эндпоинт для симуляции с PMF-ответом JSON
- F1.9 `/pmf-chart` страница с Chart.js визуализацией распределения урона
- Тесты `tests/test_pmf_chart.py` для страницы PMF chart
- F1.10 PMF chart — damage distribution graph (Chart.js) | интегрирован в /pmf-chart
- F1.11 Round Viewer stub — отображение JSON результата симуляции с историей раундов
- RELEASE.md: политика версионирования (ZeroVer), ветвления (GitHub Flow), релизов
- CHANGELOG.md: история изменений в формате Keep a Changelog

### Changed
- F1.1 `backend/model/unit.py`: добавлена валидация полей `Unit` через `__post_init__`
- F1.2 `Weapon` переписан со строкового формата на структурированный контракт: `type`, `range_max`, `attacks_dice`, `skill`, `damage_dice`, `tags`
- Проект переименован в **Warpsmith**
- ROADMAP.html: обновлён заголовок, прогресс (25%), Phase 0 расширена до 15 фич

## [0.2.0] — 2026-04-30

### Added
- **Phase 0: Foundation** — скелет проекта
- FastAPI scaffold + main.py + структура backend/web/docs
- JWT auth + bcrypt + httponly cookie middleware
- Register / Login / Logout routes + формы
- OAuth Google + VK providers
- SQLite schema + migration (users, rosters, replays)
- Wiki vault: 360+ страниц (Orks, Tau, AdMech, rules)
- C4 · ADR (11) · SRS (7 разделов) · UX docs
- SVG Icons · ICON_MAP (16 категорий юнитов)
- base.html + Tailwind CDN + HTMX + Alpine.js
- Billing stubs · Feature Gate · Free/Premium tiers
- Balance Dataslate v3.4 updates applied
- Faction Packs: AdMech (26 стр.) + Ork Errata
- Linting: ruff + mypy + pre-commit (новое)
- Feature docs: Phase 1 (12 спеки) + Phase 2 (12 спек)

### Changed
- Проект переименован в **Warpsmith**
- pyproject.toml: добавлены ruff, mypy, pre-commit конфиги
