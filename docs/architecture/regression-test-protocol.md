---
title: "Regression Test Protocol"
slug: regression-test-protocol
status: accepted
date: 2026-05-06
priority: 1
---
# Warpsmith — Протокол регрессионного тестирования

**Версия:** v0.6.6
**Дата:** 2026-05-06
**Покрытие:** 431 автоматических + ручные сценарии

---

## 1. Быстрый запуск (smoke test)

```bash
cd /mnt/d/Python/Balthier/simulator

# 1. Линтинг
ruff check . && ruff format --check .

# 2. Полный прогон тестов
.venv/bin/python -m pytest tests/ -x -q --tb=short

# 3. Запуск сервера + health check
.venv/bin/python -c "import uvicorn; uvicorn.run('main:app', host='127.0.0.1', port=8000, reload=False)" &
sleep 3
curl -s http://127.0.0.1:8000/api/health
# → {"status":"ok","version":"0.3.0"}
```

**Критерий:** 0 ошибок ruff, 431+ тестов passed, `/api/health` отвечает.

---

## 2. Автоматические тесты по модулям

### Phase 1 — Combat Engine

| Модуль | Файл тестов | Что проверяется | Крит. |
|--------|------------|-----------------|-------|
| Dice Pool | `test_dice.py` | NumPy D6 Monte Carlo, распределение | ✅ |
| Modifiers | `test_modifiers.py` | ±1 caps, rerolls | ✅ |
| Combat Sequence | `test_combat.py` | Hit→Wound→Save→Damage→FNP | ✅ |
| Weapon Keywords P1 | `test_weapon_keywords.py` | Sustained, Lethal, Devastating | ✅ |
| **Weapon Keywords P2** | `test_weapon_keywords_phase2.py` | Blast, Heavy, Torrent, Melta, Rapid Fire, Lance, One Shot, Precision, Pistol | ✅ |
| PMF Chart | `test_pmf.py` | Распределение урона | ✅ |

```bash
.venv/bin/python -m pytest tests/test_dice.py tests/test_modifiers.py \
  tests/test_combat.py tests/test_weapon_keywords.py \
  tests/test_weapon_keywords_phase2.py -v --tb=short
```

### Phase 2 — Game System

| Модуль | Файл тестов | Что проверяется | Крит. |
|--------|------------|-----------------|-------|
| Game State | `test_game_state.py` | UnitState, move_unit, deal_damage | ✅ |
| 2D Map | `test_map.py` | Grid, terrain, deploy zones | ✅ |
| Line of Sight | `test_los.py` | Bresenham ray casting | ✅ |
| Missions | `test_missions.py` | Objectives, VP scoring | ✅ |
| Game Loop | `test_game_loop.py` | 6 фаз, run_round | ✅ |
| AI Decision | `test_ai_decision.py` | choose_action, score_shoot | ✅ |
| AI Deployment | `test_deployment.py` | Zone placement | ✅ |
| Roster CRUD | `test_rosters.py` | Create/Read/Update/Delete | ✅ |

```bash
.venv/bin/python -m pytest tests/test_game_state.py tests/test_map.py \
  tests/test_los.py tests/test_missions.py tests/test_game_loop.py \
  tests/test_ai_decision.py tests/test_rosters.py -v --tb=short
```

### Phase 3 — AI & Automation

| Модуль | Файл тестов | Что проверяется | Крит. |
|--------|------------|-----------------|-------|
| Auto-play | `test_autoplay.py` | AI vs AI full scenario | ✅ |
| Replay | `test_replay.py` | Запись/чтение replays | ✅ |
| Faction AI | `test_faction_ai.py` | Ork/Tau/AdMech profiles | ✅ |

```bash
.venv/bin/python -m pytest tests/test_autoplay.py tests/test_replay.py \
  tests/test_faction_ai.py -v --tb=short
```

### Phase 4 — Web UI

| Модуль | Файл тестов | Что проверяется | Крит. |
|--------|------------|-----------------|-------|
| Unit Modal | `test_unit_modal.py` | Squad size, wargear | ✅ |
| Detachment Picker | `test_detachment_picker.py` | Выбор детачмента | ✅ |
| Synergy Hints | `test_synergy_hints.py` | Leader/Transport совместимость | ✅ |
| Tooltips | `test_tooltips.py` | STAT_TOOLTIPS рендеринг | ✅ |
| Progressive Disclosure | `test_progressive_disclosure.py` | B/I/E переключение | ✅ |
| Docker | `test_docker.py` | Dockerfile + Railway | ✅ |

```bash
.venv/bin/python -m pytest tests/test_unit_modal.py \
  tests/test_detachment_picker.py tests/test_synergy_hints.py \
  tests/test_tooltips.py tests/test_progressive_disclosure.py -v --tb=short
```

---

## 3. Ручное регрессионное тестирование

> **Порядок:** сверху вниз. Каждый шаг = 1 проверка. Отмечать ✅/❌.

### 3.1. Стартовая страница

| # | Действие | Ожидаемый результат |
|---|----------|---------------------|
| R1 | Открыть `/` | Загружается главная страница |
| R2 | Навбар: ссылки Team Builder, Browser, Scenario, Pricing | Все кликабельны |
| R3 | B/I/E переключатель | Меняет видимость beginner/intermediate/expert элементов |

### 3.2. Регистрация и вход

| # | Действие | Ожидаемый результат |
|---|----------|---------------------|
| R4 | `/auth/register` → заполнить → Register | Редирект на `/team-builder`, cookie установлен |
| R5 | `/auth/logout` | Cookie удалён, редирект на `/` |
| R6 | `/auth/login` → ввести те же данные | Редирект на `/team-builder` |
| R7 | `/auth/register` с уже существующим email | Ошибка 409 |

### 3.3. Team Builder

| # | Действие | Ожидаемый результат |
|---|----------|---------------------|
| R8 | Выбрать Orks → видны категории + юниты | Список юнитов обновляется |
| R9 | Клик на Boyz → модалка | Показывает статы, оружие, squad size ± |
| R10 | Изменить squad size → + / − | PTS в модалке пересчитывается |
| R11 | Add to Roster | Юнит появляется в правой панели |
| R12 | Добавить Warboss + Gretchin + Trukk | PTS bar обновляется |
| R13 | Save Roster | Alert "Roster saved successfully", форма сброшена |
| R14 | Save Roster с превышением PTS | Ошибка валидации в красном блоке |

### 3.4. Faction Browser

| # | Действие | Ожидаемый результат |
|---|----------|---------------------|
| R15 | `/faction-browser` | Список фракций |
| R16 | Выбрать фракцию → фильтр | Показывает юниты выбранной фракции |
| R17 | Иконки категорий | Отображаются inline SVG |

### 3.5. Scenario Setup + Generate Opponent + Auto-play

| # | Действие | Ожидаемый результат |
|---|----------|---------------------|
| R18 | `/scenario-setup` | Дропдауны Player 1, Player 2, Generate |
| R19 | Выбрать Player 1 ростер | Показывает "Test Orks (orks, 2000pts)" |
| R20 | Нажать «🎲 Generate Random Opponent» | Появляется "✅ AI ... Army (faction, pts) — AI generated" |
| R21 | Юниты на карте | 23+ units на canvas map |
| R22 | Нажать «🎲 Start Simulation» | Редирект на `/round-viewer/auto_...` |
| R23 | Round viewer показывает раунды | Заголовок "🎬 Replay: auto_...", кнопки Round ▶ |

### 3.6. Round Viewer / Replay

| # | Действие | Ожидаемый результат |
|---|----------|---------------------|
| R24 | Кнопка «Round ▶» | Переход к следующему раунду |
| R25 | Кнопка «Event ▷» | Переход к следующему событию |
| R26 | VP отображаются | Счёт для обоих игроков |
| R27 | Battlefield canvas | Юниты отрисованы на карте |

### 3.7. API endpoints (curl)

```bash
# R28: Health
curl -s http://127.0.0.1:8000/api/health
# → {"status":"ok","version":"0.3.0"}

# R29: Units
curl -s http://127.0.0.1:8000/api/units?faction=orks | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d.get('units',[])))"
# → >0

# R30: Generate roster (без авторизации)
curl -s -X POST http://127.0.0.1:8000/api/rosters/generate \
  -H "Content-Type: application/json" \
  -d '{"pts_limit":1000}' | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['roster']['total_pts'])"
# → число < 1000

# R31: Simulate
curl -s -X POST http://127.0.0.1:8000/api/simulate \
  -H "Content-Type: application/json" \
  -d '{"attacker":"Boyz","weapon":"Shoota","target":"Space Marine"}' | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('expected_damage', 'error'))"
# → число > 0

# R32: Factions
curl -s http://127.0.0.1:8000/api/factions | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d.get('factions',[])))"
# → >0
```

### 3.8. Auth API

| # | Действие | Ожидаемый результат |
|---|----------|---------------------|
| R33 | `GET /api/me` без куки | `null` |
| R34 | `GET /api/me` с JWT-кукой | `{"email":"...","display_name":"...","tier":"free"}` |
| R35 | `GET /api/rosters` без куки | 401 (или guest roster) |

---

## 4. Критические пути (must not break)

Эти сценарии должны проходить **перед каждым деплоем**.

### CP1: Team Builder → Save → Scenario → Auto-play → Replay

```
1. Залогиниться
2. Team Builder: создать ростер (Orks, 2000pts, 4+ юнитов)
3. Save → success
4. Scenario Setup: выбрать ростер Player 1
5. Generate Random Opponent → success
6. Start Simulation → редирект на round-viewer
7. Replay показывает 2+ раундов
8. VP > 0 у обоих игроков
```

### CP2: Combat Engine Accuracy

```bash
.venv/bin/python -m pytest tests/test_combat.py tests/test_weapon_keywords.py \
  tests/test_weapon_keywords_phase2.py -v
# Все тесты должны пройти — это гарантирует что математика боя не сломана
```

### CP3: API без регрессий

```bash
curl -s http://127.0.0.1:8000/api/health | grep '"status":"ok"'
curl -s http://127.0.0.1:8000/api/units | grep '"units"'
curl -s http://127.0.0.1:8000/api/factions | grep '"factions"'
curl -s -X POST http://127.0.0.1:8000/api/rosters/generate -H "Content-Type: application/json" -d '{}' | grep '"roster"'
```

### CP4: Ростер CRUD

```bash
.venv/bin/python -m pytest tests/test_rosters.py -v
# Create, Read, Update, Delete — все 4 операции
```

---

## 5. Регрессионный чек-лист (перед деплоем)

| # | Проверка | Авто/Ручное | Статус |
|---|----------|------------|--------|
| 1 | `ruff check .` | Авто | ☐ |
| 2 | `ruff format --check .` | Авто | ☐ |
| 3 | `pytest tests/ -q` → 431+ passed | Авто | ☐ |
| 4 | Сервер запускается без ошибок | Ручное | ☐ |
| 5 | `/api/health` → 200 | Ручное | ☐ |
| 6 | Team Builder → Save ростер | Ручное | ☐ |
| 7 | Generate Random Opponent | Ручное | ☐ |
| 8 | Auto-play → Round Viewer | Ручное | ☐ |
| 9 | Replay прокрутка раундов | Ручное | ☐ |
| 10 | Login/Register/Logout | Ручное | ☐ |
| 11 | API: units, factions, simulate, generate | Ручное | ☐ |
| 12 | `docker build` (если деплой) | Авто | ☐ |

---

## 6. Частота

| Уровень | Когда | Время |
|---------|-------|-------|
| **Smoke** (линт + 10 тестов) | Каждый коммит | ~5 сек |
| **Unit** (все 431 тестов) | Перед PR | ~30 сек |
| **Regression** (ручные R1-R35) | Перед деплоем | ~15 мин |
| **Critical Paths** (CP1-CP4) | Перед деплоем | ~5 мин |

---

## 7. Известные проблемы (не регрессии)

| Проблема | Статус |
|----------|--------|
| `datetime.utcnow()` deprecation в auth | ⚠️ warning, не блокирует |
| Alpine.js tooltip NULL warnings на scenario_setup | ⚠️ cosmetic |
| `canStart` возвращает объект вместо boolean | ⚠️ работает из-за JS coercion |
| SQLite WAL файлы после git-операций | ⚠️ фиксится `rm *.db-shm *.db-wal` |
