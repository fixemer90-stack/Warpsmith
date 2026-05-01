# Battle Simulator — Warhammer 40k

Симулятор-калькулятор боёв по правилам Warhammer 40,000 10-й редакции.

Использует [вики](https://github.com/) как источник данных о юнитах, правилах и фракциях.

## Быстрый старт

```bash
# Клонирование
git clone <repo-url>
cd simulator

# Установка зависимостей
pip install -e .

# Запуск
python main.py "10 Boyz vs 5 Strike Team" --edition 10e
```

## Структура проекта

```
simulator/
├── backend/          # Движок симуляции (Python)
│   ├── loader/       # Парсер вики
│   ├── engine/       # Последовательность атак, Monte Carlo
│   ├── model/        # Unit, Weapon, Ability dataclasses
│   └── reporter/     # rich-таблицы, JSON-экспорт
├── ui/               # Пользовательский интерфейс
│   └── terminal/     # CLI (click/rich)
├── docs/             # Документация
│   ├── architecture/ # C4-диаграммы, ADR
│   └── requirements/ # SRS, use cases
├── tests/            # pytest
└── pyproject.toml    # Зависимости и метаданные
```

## Статус

- [ ] Wiki Loader
- [ ] Combat Engine
- [ ] CLI
- [ ] Monte Carlo Runner
- [ ] Reporter

## Лицензия

MIT
