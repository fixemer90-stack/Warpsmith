# Warpsmith — Wiki Index

**Версия:** 10th Edition | **Всего файлов:** 480 `.md` | **Обновлён:** 2026-05-09

---

**Навигация:** [INDEX.md](/mnt/d/Python/Balthier/INDEX.md) ← · → [DEV_INDEX.md](/mnt/d/Python/Balthier/simulator/DEV_INDEX.md)

## 📂 Структура вики

```
wiki/
├── factions/           ← общие страницы фракций
├── units/              ← даташиты юнитов
│   ├── orks/            88 файлов (81 загружается парсером)
│   ├── tau/            41 файл  (40 загружаются)
│   └── mechanicus/     39 файлов (39 загружаются)
├── detachments/        ← детачменты
│   ├── orks/           10
│   ├── tau/             5
│   └── mechanicus/      7
├── stratagems/         ← стратагемы
│   ├── core/           13
│   ├── orks/           42
│   ├── tau/            19
│   └── mechanicus/     42
├── enhancements/       ← энхансменты
│   ├── orks/           44
│   ├── tau/            16
│   └── mechanicus/     28
├── rules/              ← правила редакций
│   ├── 10th/           23  (Waaagh!, FTGG, Battle-shock...)
│   └── 9th/            12
├── concepts/           ← концепты (16 stubs)
├── queries/            ← 1 (C4 architecture query)
├── comparisons/        ← пусто
└── raw/                ← 2 (исходные данные)
```

## 🧭 Навигация по фракциям

| Фракция | Юнитов | Детачментов | Стратагем | Энхансментов |
|---------|--------|-------------|-----------|--------------|
| Orks | 88 (81 loaded) | 10 | 42 | 44 |
| T'au Empire | 41 (40 loaded) | 5 | 19 | 16 |
| Adeptus Mechanicus | 39 (39 loaded) | 7 | 42 | 28 |

## 📄 Ключевые файлы

| Файл | Описание |
|------|----------|
| `factions/Orks.md` | Общая страница фракции Orks |
| `factions/T'au Empire.md` | Общая страница фракции T'au |
| `factions/Adeptus Mechanicus.md` | Общая страница AdMech |
| `stratagems/core/stratagem-index.md` | Индекс core стратагем |
| `rules/10th/Waaagh!.md` | Арми-правило орков |
| `rules/10th/For The Greater Good.md` | Арми-правило тау |
| `rules/10th/Battle-shock.md` | Battle-shock тесты |
| `rules/10th/Benefit of Cover.md` | Правила укрытий |

## 🔗 Связанные документы

| Документ | Где |
|----------|-----|
| Общий индекс проекта | `/mnt/d/Python/Balthier/INDEX.md` |
| Хаб разработчика | `../DEV_INDEX.md` |
| Архитектура | `../docs/architecture/C4.md` |
| Feature-спеки | `../docs/features/` |

## ⚠️ Формат файлов

Каждый `.md` файл содержит:
- YAML frontmatter (`title`, `type`, `faction`, `tags`, `edition`)
- Markdown тело с таблицами профилей
- `[[wikilinks]]` для перекрёстных ссылок
- Тактические заметки на русском языке
