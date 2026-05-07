---
title: Shooting Phase — Known Gaps
created: 2026-05-05
type: feature-spec
status: backlog
related: [f3.5-autoplay, shooting-phase]
---

# Shooting Phase — Known Gaps

Результаты ревью реализации стрельбы (2026-05-05)对照 wiki/rules/10th/Shooting Phase.md.

## Missing Features

### 1. Big Guns Never Tire

**Wiki rule:** MONSTER и VEHICLE могут стрелять в Engagement Range (1"), но с -1 к попаданию Heavy оружием. Могут целиться только в отряды в своей зоне поражения.

**Current code:** `is_engaged` блокирует стрельбу для всех юнитов.

**Fix:** Разрешить стрельбу для MONSTER/VEHICLE если `is_engaged`, с -1 к BS для Heavy.

### 2. Look Out, Sir

**Wiki rule:** CHARACTER с ≤9 W не может быть целью, если в 3" есть дружественный отряд (из 3+ моделей, MONSTER или VEHICLE).

**Current code:** Не реализовано. Любой юнит может быть целью.

**Fix:** Перед выбором цели проверять, не защищён ли CHARACTER правилом Look Out, Sir.

### 3. Player Target Selection

**Wiki rule:** Игрок выбирает цели (visibility + range).

**Current code:** Автоматически выбирает ближайшую цель.

**Fix:** AI должен выбирать цель по приоритету (warlord, weakest, closest) а не только по расстоянию.

### 4. Weapon Selection

**Wiki rule:** Выбери оружие (все или часть).

**Current code:** Использует все оружие юнита.

**Fix:** AI должен выбирать оружие по эффективности (дальность, урон, тип цели).

### 5. Pistol in Engagement Range

**Wiki rule:** Pistols можно стрелять в Engagement Range.

**Current code:** `is_engaged` блокирует полностью.

**Fix:** Разрешить Pistols в Engagement Range.

## Priority

- P1: Big Guns Never Tire (влияет на баланс VEHICLE/MONSTER)
- P2: Look Out, Sir (влияет на targeting characters)
- P3: Player target selection (AI quality)
- P4: Weapon selection (AI quality)
- P5: Pistol in Engagement Range (edge case)

## References

- `wiki/rules/10th/Shooting Phase.md`
- `wiki/rules/10th/Making Attacks (10ed).md`
- `wiki/rules/10th/Weapon Keywords (10ed).md`
- `backend/engine/scenario.py` → `_shooting_phase()`
