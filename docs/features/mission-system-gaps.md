---
title: Mission System — Known Gaps
created: 2026-05-05
type: feature-spec
status: backlog
related: [f3.5-autoplay, mission-system]
---

# Mission System — Known Gaps

Результаты ревью системы миссий (2026-05-05). Вики не содержит правил миссий —对照 WH40k 10th edition CRB.

## Current Missions

| Mission | Scoring | Objectives | Issues |
|---------|---------|------------|--------|
| Only War | kill_points | 0 | Должен быть progressive (6 objectives) |
| Purge the Foe | kill_points | 0 | Нет Slay the Warlord бонуса |
| Take and Hold | standard | 5 | Объекты хардкод для 6x4 карты |

## Missing Features

### 1. Only War — Progressive Scoring

**WH40k 10ed rule:** 6 objectives на карте. VP = количество контролируемых объектов + бонус за "hold more". Половина VP начинается с Round 2.

**Current code:** kill_points (я изменил чтобы бой работал).

**Fix:** Вернуть progressive scoring с автоматическим размещением 6 объектов.

### 2. Slay the Warlord

**WH40k 10ed rule:** +1 VP за уничтожение вражеского Warlord.

**Current code:** Не реализовано.

**Fix:** Добавить проверку `unit.is_warlord` при уничтожении.

### 3. Dynamic Objective Placement

**Current code:** Объекты хардкод для 6x4 карты (Take and Hold).

**Fix:** Масштабировать объекты по размеру карты (как уже сделано для Only War).

### 4. Deployment Zones

**WH40k 10ed rules:**
- Dawn of War: 24" deploy zone, 12" gap
- Search and Destroy: 12" squares in corners
- Crucible of Battle: 12" from each short edge

**Current code:** Deployment zones используются из DeploymentType enum, но не точно соответствуют правилам.

### 5. Mission Selection UI

**Current code:** Миссия задаётся параметром в API.

**Fix:** UI для выбора миссии перед боем.

### 6. Secondary Objectives

**WH40k 10ed rule:** Помимо PRIMARY есть SECONDARY objectives (Behind Enemy Lines, Engage on All Fronts, etc.).

**Current code:** Не реализовано.

**Fix:** Добавить систему secondary objectives.

## Priority

- P1: Only War progressive scoring (core mission)
- P2: Slay the Warlord (simple bonus)
- P3: Dynamic objective placement (reusability)
- P4: Deployment zones accuracy
- P5: Mission selection UI
- P6: Secondary objectives (complex)

## References

- `wiki/rules/10th/Battle Round.md`
- `wiki/rules/10th/Command Phase.md`
- `backend/state/mission.py` → `_only_war()`, `_purge_the_foe()`, `_take_and_hold()`
- `backend/engine/scenario.py` → `_command_phase()` (VP scoring)
- WH40k 10th Edition CRB, Chapter 2: Mission Rules
