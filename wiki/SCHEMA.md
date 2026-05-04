# Wiki Schema

## Domain
Warhammer 40k — табличный варгейм. Симулятор боёв по правилам Warhammer 40k (10-я редакция и ранее). Фракции, юниты, оружие, профили, правила, стратагемы, психические силы и механики боя.

## Conventions
- File names: lowercase, hyphens, no spaces (e.g., `space-marine-tactical.md`)
- Every wiki page starts with YAML frontmatter (see below)
- Use `[[wikilinks]]` to link between pages (minimum 2 outbound links per page)
- When updating a page, always bump the `updated` date
- Every new page must be added to `index.md` under the correct section
- Every action must be appended to `log.md`
- **Provenance markers:** На страницах, синтезирующих 3+ источника, ставь `^[raw/articles/source-file.md]` в конце параграфов, чьи утверждения из конкретного источника.

### Atomicity (Атомарность)
- **Одна сущность/концепт = одна страница.** Никогда не разбивай одну сущность на несколько файлов и не смешивай разные концепции на одной странице.
- **Без дублирования.** Если факт уже есть на одной странице, не повторяй его на другой — ссылайся через `[[викиссылку]]`.
- **Никакого перекрёстного копирования.** Способности/правила, общие для нескольких юнитов, описываются на своей странице и подключаются через ссылки.
- **Композиция через ссылки.** Сложное правило собирается из атомарных страниц, как из кирпичиков.

### AI-Friendly (Дружелюбность к ИИ)
- **Предсказуемая структура.** Все страницы одного типа следуют одинаковому шаблону разделов (см. ниже Entity/Concept/Comparison Pages).
- **Машиночитаемый frontmatter.** Все страницы ОБЯЗАТЕЛЬНО имеют полный YAML frontmatter — без пропущенных полей.
- **Понятные пути.** Файлы лежат в предсказуемых папках:
  ```
  wiki/
  ├── factions/           # Страницы фракций + групп (Imperium.md, Space Marines.md...)
  ├── units/
  │   ├── orks/           # Даташиты юнитов орков
  │   ├── tau/            # Даташиты юнитов тау
  │   └── ...             # Будут добавлены по мере наполнения
  ├── detachments/
  │   ├── orks/           # Детачменты орков
  │   ├── tau/            # Детачменты тау
  │   └── ...             # Будут добавлены по мере наполнения
  ├── rules/
  │   ├── 9th/            # Правила 9-й редакции
  │   └── 10th/           # Правила 10-й редакции (будет добавлено)
  ├── stratagems/         # Стратагемы по фракциям (+ core/)
  │   ├── core/           # Core Stratagems (общие для всех)
  │   ├── orks/
  │   └── tau/
  ├── enhancements/       # Энхансменты (усиления) по фракциям
  │   ├── orks/
  │   └── tau/
  ├── raw/                # Сырые источники (articles/, papers/)
  ├── comparisons/        # Сравнения
  └── queries/            # Сохранённые запросы
  ```
- **Явные связи.** Каждая страница содержит минимум 2 `[[викиссылки]]` на связанные страницы — никаких неявных зависимостей.
- **Консистентные теги.** Только из таксономии в SCHEMA.md. Новый тег = сначала добавить в таксономию.
- **Плоская структура.** Максимум 2 уровня вложенности: `units/orks/`, `detachments/orks/`. Категории (units, detachments, concepts) — плоские внутри себя.
- **Имена файлов = title.** Файлы называются точно как `title:` в frontmatter (пробелы, заглавные буквы). Это нужно для Obsidian: `[[Mek Gunz]]` → `Mek Gunz.md`. Концепты с русскими title — тоже называются по-русски. Никакого kebab-case.

## Frontmatter

```yaml
---
title: Page Title
created: YYYY-MM-DD
updated: YYYY-MM-DD
type: entity | faction | faction-group | stratagem | enhancement | wargear | attached-model | keyword | concept | comparison | query | summary | profile
icon: character | battleline | elite | infantry | vehicle | transport | walker | monster | dreadnought | titanic | speed-freek | flyer | artillery | psyker | medic | epic-hero
tags: [from taxonomy below]
# For faction pages:
faction_group: imperium | chaos | xenos
sources: [raw/articles/source-name.md]
edition: 10e           # редакция правил
# Optional:
confidence: high | medium | low
contested: true
contradictions: [other-page-slug]
---
```

### raw/ Frontmatter

```yaml
---
source_url: https://example.com/article
ingested: YYYY-MM-DD
sha256: <hex digest of the body below frontmatter>
---
```

## Tag Taxonomy

### Factions
- Imperium: space-marines, adeptas-sororitas, adeptus-custodes, adeptus-mechanicus, adeptus-titanicus, astra-militarum, grey-knights, imperial-agents, imperial-knights
- Chaos: chaos-space-marines, chaos-daemons, chaos-knights, death-guard, emperors-children, thousand-sons, world-eaters
- Xenos: orks, aeldari, drukhari, tyranids, necrons, tau, leagues-of-votann, genestealer-cults, t-au-empire

### Unit Types
- infantry, battleline, vehicle, monster, swarm, character, epic-hero, transport, flyer, titanic

### Stratagems
- core-stratagem, detachment-stratagem, battle-tactic, strategic-ploy, epic-deed, wargek, psychic-aktion

### Enhancements
- enhancement, warlord-trait, relic

### Wargear
- melee-weapon, ranged-weapon, pistol, grenade, wargear, relic

### Attached Models
- attached-model, leader, squad-upgrade

### Keywords
- keyword, army-rule, core-rule, faction-keyword, unit-keyword

### Mechanics
- core-rules: movement-phase, shooting-phase, charge-phase, fight-phase, morale-phase, command-phase, battle-round, battle-format, mission
- special-rules: lethal-hits, sustained-hits, devastating-wounds, precision, feel-no-pain, invulnerable-save
- modifiers: hit-modifier, wound-modifier, damage-modifier, save-modifier

### Tactics
- stratagems, psychic-powers, detachment-abilities, army-rules

### Meta
- comparison, timeline, simulation, point-values, datasheet, profile

## Page Thresholds
- **Create a page** when an entity/concept appears in 2+ источников OR централен для одного источника
- **Add to existing page** when a source mentions something already covered
- **DON'T create a page** for passing mentions or minor details
- **Split a page** when it exceeds ~200 lines
- **Archive a page** when fully superseded — move to `_archive/`, remove from index

## Entity Pages (в `factions/` или `units/<faction>/`)
Одна страница на заметную сущность:
- **`type: entity`** — полноценный юнит, который можно взять в ростер ([[Warboss]], [[Boyz]], [[Crisis Battlesuits]])
- **`type: attached-model`** — модель, которая является частью даташита другого юнита ([[Makari]] — часть [[Ghazghkull Thraka]], [[Nob on Smasha Squig]])
- **`type: wargear`** — оружие или снаряжение ([[Power Klaw]], [[Kustom Force Field]], [[Smart Missile System]])
- **`type: keyword`** — ключевое слово или роль ([[Kaptin]], [[Beast Snagga]])

Структура:
- Обзор / что это
- Ключевые характеристики (M, T, SV, W, LD, OC для юнитов; S, AP, D для оружия)
- Особые правила и способности
- Связи с другими страницами ([[wikilinks]])
- Принадлежность к фракции ([[wikilinks]])

## Stratagem Pages (в `stratagems/` или `stratagems/core/`)
Одна страница на каждую стратагему:
- **Тип:** `type: stratagem`
- CP cost (количество CP)
- Когда используется (фаза / момент)
- Для кого (фракция / детачмент)
- Эффект (что делает)
- Keywords (core-stratagem / detachment-stratagem, battle-tactic / strategic-ploy...)
- Принадлежность к детачменту ([[wikilinks]]) или core ([[Core Stratagems]])

```yaml
---
title: Command Re-roll
type: stratagem
cp: 1
when: Any phase
target: Any unit
effect: Re-roll one hit, wound, damage, save, or advance roll
tags: [core-stratagem, battle-tactic]
---
```

## Enhancement Pages (в `enhancements/<faction>/`)
Одна страница на каждое усиление:
- **Тип:** `type: enhancement`
- CP cost
- Эффект (изменение статов, новая способность)
- Кому доступно (детачмент)
- Принадлежность к детачменту ([[wikilinks]])

## Concept Pages (в `rules/<edition>/`)
Одна страница на механику или тему:
- Определение / объяснение правила
- Как работает в симуляторе
- Связанные понятия ([[wikilinks]])
- Дополнительные правила из разных редакций

## Comparison Pages
Сравнение юнитов/оружия/фракций:
- Что сравнивается и зачем
- Параметры сравнения (таблицы)
- Вердикт

## Update Policy
When new information conflicts with existing content:
1. Check edition/dates — newer editions supersede older ones
2. If genuinely contradictory, note both positions with dates and edition
3. Mark in frontmatter: `contradictions: [page-name]`
4. Flag for user review in lint report
