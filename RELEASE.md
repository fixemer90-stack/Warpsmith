# Release Policy — Warpsmith

Политика версионирования, ветвления и релизов.
см. [CHANGELOG.md](CHANGELOG.md) — история изменений по версиям.

---

## Версионирование: ZeroVer

```
v0.<PHASE>.<PATCH>
```

| Компонент | Что меняется | Пример |
|-----------|-------------|--------|
| `PHASE` | Номер фазы (0–7). Растёт при завершении фазы | v0.2.0 → v0.3.0 |
| `PATCH` | Багфиксы, мелкие доработки внутри фазы | v0.2.0 → v0.2.1 |

**Правила:**
- Пока продукт < 1.0 — MAJOR всегда 0 (ZeroVer)
- PHASE = номер фазы из ROADMAP.md (0 = Foundation, 1 = Combat Engine, 2 = Game System...)
- PATCH сбрасывается в 0 при переходе фазы
- v1.0.0 — первый стабильный релиз (после Phase 7 или по решению)

**История:**
- `v0.1.0` — Foundation (Phase 0)
- `v0.2.0` — Phase 0 завершена, Phase 1 начата
- `v0.2.1` — текущая patch release: F1.1–F1.5 (models, loader, modifiers, dice)

**Где хранится:**
- `pyproject.toml` — `version = "0.2.1"`
- Git tag — `v0.2.1`

---

## Ветки: GitHub Flow

```
main
  ├── feat/combat-engine
  ├── feat/2d-map
  ├── fix/dice-seed
  ├── docs/release-policy
  └── ...
```

### Правила

| Ветка | Назначение | Откуда | Куда PR |
|-------|-----------|--------|---------|
| `main` | Стабильная. Всегда готова к деплою | — | — |
| `feat/<name>` | Новая фича (одна feature-спецификация) | `main` | → `main` |
| `fix/<name>` | Багфикс | `main` | → `main` |
| `docs/<name>` | Документация | `main` | → `main` |
| `refactor/<name>` | Рефакторинг | `main` | → `main` |
| `test/<name>` | Тесты | `main` | → `main` |

**Запрещено:**
- Коммитить напрямую в `main` (исключение: hotfix с одобрения)
- Держать ветку дольше 3 дней без PR
- Ветвить от ветки — только от `main`

---

## Процесс релиза

### 1. Подготовка

```bash
# Убедиться, что main зелёный
git checkout main
ruff check .
mypy .
pytest tests/

# Обновить версию в pyproject.toml
# v0.2.1 → patch bump
# v0.2.0 → phase bump (когда Phase 1 завершена)
```

### 2. Чейнджлог

Обновить `CHANGELOG.md`:

```markdown
## v0.2.1 (2026-05-01)

### Added
- F1.5 Dice Pool — NumPy Monte Carlo engine
- F1.6 Combat Sequence — Hit→Wound→Save→Damage→FNP

### Fixed
- Seed reproducibility in DicePool
- Natural 1/6 logic in hit rolls
```

### 3. Тегирование

```bash
git tag -a v0.2.1 -m "v0.2.1 — Dice Pool + Combat Sequence"
git push origin v0.2.1
```

### 4. Релиз

- GitHub Release (если есть GitHub)
- Или ручной деплой с тега
- Changelog → Release Notes

### Когда релизить

| Триггер | Пример |
|---------|--------|
| Завершена feature-спецификация | F1.5 Dice Pool → PATCH+1 |
| Завершена фаза целиком | Phase 1 все 12 фич → PHASE+1, PATCH=0 |
| Критический багфикс | Вылетает combat sequence → PATCH+1 |
| Сплинтер | Накопилось 3+ фичи → PATCH+1 |

---

## Чейнджлог: Keep a Changelog

Формат: [Keep a Changelog](https://keepachangelog.com/)

```markdown
# Changelog — Warpsmith

## [0.2.1] — 2026-05-01
### Added
- F1.5 Dice Pool: DicePool class with NumPy D6, simulate(), compute_stats()
- F1.6 Combat Sequence: simulate_weapon_attack() full pipeline

## [0.2.0] — 2026-04-30
### Added
- Phase 0: Foundation completed
- JWT auth + OAuth (Google, VK)
- Wiki vault: 360+ pages
- Billing stubs + Feature Gate
- Team Builder UI scaffold
