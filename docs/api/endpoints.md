# API — Warpsmith

Документация по API симулятора.

**Swagger UI (интерактивная):** http://127.0.0.1:8000/docs
**OpenAPI JSON:** http://127.0.0.1:8000/openapi.json

## Эндпоинты

| Метод | Путь | Назначение | Auth |
|-------|------|-----------|------|
| GET | `/api/health` | Health check | нет |
| GET | `/api/factions` | Список фракций | нет |
| GET | `/api/units?faction=` | Юниты фракции | нет |
| GET | `/api/detachments?faction=` | Детачменты фракции | нет |
| POST | `/api/simulate` | Симуляция атаки оружием | нет |
| POST | `/api/simulate-unit` | Симуляция атаки юнита | нет |
| POST | `/api/rosters` | Создать ростер | JWT |
| GET | `/api/rosters` | Список ростереров | JWT |
| GET | `/api/rosters/{id}` | Ростер по id | JWT |
| DELETE | `/api/rosters/{id}` | Удалить ростер | JWT |

Подробнее — в Swagger: http://127.0.0.1:8000/docs
