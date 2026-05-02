# Changelog — Warpsmith

Все заметные изменения проекта фиксируются в этом файле.

Формат: [Keep a Changelog](https://keepachangelog.com/)
Версионирование: ZeroVer `v0.<PHASE>.<PATCH>`

---

## [0.3.0] — 2026-05-02

### Added
- F1.12 MultiAttack: `simulate_unit_attack()` для юнитов с несколькими оружиями
- F1.12 `simulate_squad_attack()` для симуляции атак отрядов
- F1.12 POST `/api/simulate-unit`: эндпоинт для симуляции атаки юнита
- Тесты `tests/test_combat.py` для multi-weapon и squad attacks
- **Phase 1: Combat Engine полностью завершён!**

### Changed
- Версия: 0.2.1 → 0.3.0 (Phase 1 завершена, начинается Phase 2)

## [Unreleased]

### Added
- **Phase 2: Game System начат!**
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
