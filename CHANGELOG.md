# Changelog — Warpsmith

Все заметные изменения проекта фиксируются в этом файле.

Формат: [Keep a Changelog](https://keepachangelog.com/)
Версионирование: ZeroVer `v0.<PHASE>.<PATCH>` — см. [RELEASE.md](RELEASE.md)

---

## [Unreleased] — 2026-05-03

### Added
- **F3.1 Greedy Decision Engine** — `backend/engine/ai/decision.py`: ActionType, Action, EvaluationContext, choose_action() с взвешенной оценкой (shoot/charge/move), генерация кандидатов по фазам, поддержка opponent_units_map для статов целей
- **Тесты F3.1** — `tests/test_ai_decision.py`: 26 тестов (дистанция, дальность, ожидаемый урон, генерация кандидатов, скоринг, choose_action, custom weights)
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
- Obsidian — удалены битые symlink venv/lib64, venv/bin/

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
