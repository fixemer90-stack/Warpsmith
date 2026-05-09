# API Endpoints — Warpsmith

**Статус:** актуализировано 2026-05-09 для v0.7.7

**Источник истины для деталей схем:** Swagger UI — http://127.0.0.1:8000/docs

**OpenAPI JSON:** http://127.0.0.1:8000/openapi.json

Этот файл — краткий индекс endpoint-ов: метод, путь, назначение и требование авторизации. Подробные request/response schemas не дублируются здесь; для них использовать Swagger.

## `/api` endpoints

| Метод | Путь | Назначение | Auth |
|-------|------|------------|------|
| GET | `/api/health` | Health check API, возвращает статус и версию приложения. | Нет |
| GET | `/api/factions` | Список доступных фракций из wiki registry: `id`, `label`. | Нет |
| GET | `/api/units?faction=` | Список юнитов, опционально по фракции; включает stats, `squad_size`, `can_be_warlord`, `is_leader`, weapons summary. | Нет |
| GET | `/api/units/browse?faction=&category=&pts_min=&pts_max=&search=&role=&sort_by=&sort_dir=&page=&per_page=` | Пагинированный каталог юнитов для Faction Browser с фильтрами, сортировкой, role flags и icon metadata. | Нет |
| GET | `/api/units/{unit_name}/detail` | Полная карточка юнита для modal UI: weapons, wargear, nob options, abilities, keywords, leader/transport metadata, `icon_tags`. | Нет |
| GET | `/api/detachments?faction=` | Список детачментов, опционально по фракции; краткое описание, rule preview, counts. | Нет |
| GET | `/api/detachments/{detachment_name}` | Полные данные детачмента: описание, detachment rule, stratagems, enhancements. | Нет |
| GET | `/api/map/tiles?width=&height=&map_id=&scenario=` | Grid/map tiles для battlefield preview/replay consumers: terrain tiles, deployment zones, units placeholder. | Нет |
| POST | `/api/simulate` | Monte Carlo симуляция выбранного weapon attack между attacker/defender units. | Нет |
| POST | `/api/simulate-unit` | Monte Carlo симуляция атаки всего юнита всеми weapons по defender unit. | Нет |
| GET | `/api/me` | JSON текущего пользователя или `null`; alias для Alpine/base header. | Optional JWT cookie |
| GET | `/api/rosters?public_only=` | Список ростеров текущего пользователя или public roster list при `public_only=true`. | JWT cookie |
| POST | `/api/rosters` | Создать roster; валидирует points, squad size, duplicate caps, Warlord requirement. | JWT cookie |
| POST | `/api/rosters/generate` | Сгенерировать AI roster по `faction`/`pts_limit`; должен быть save-and-play, с ровно одним Warlord. | Нет |
| POST | `/api/rosters/synergies` | Проверить roster synergies: leader/bodyguard, transport capacity, wiki `synergies`. | Нет |
| GET | `/api/rosters/{roster_id}` | Получить roster по id; owner или public roster. | JWT cookie |
| PUT | `/api/rosters/{roster_id}` | Обновить roster; owner-only, с той же validation logic что create. | JWT cookie |
| DELETE | `/api/rosters/{roster_id}` | Удалить roster; owner-only. | JWT cookie |
| POST | `/api/rosters/{roster_id}/duplicate` | Скопировать свой или public roster в roster list текущего пользователя. | JWT cookie |
| POST | `/api/auto-play?roster_a_id=&roster_b_id=&mission=&deployment=&max_rounds=&seed=` | Запустить полный AI-vs-AI бой, сохранить replay, вернуть `game_id`, result и replay log. | Нет |
| GET | `/api/replays` | Список сохранённых replay records из DB. | Нет |
| GET | `/api/replays/{game_id}` | Полный replay JSON для Round Viewer. | Нет |
| GET | `/api/results/{game_id}` | Replay + result summary для Result page; winner fallback рассчитывается из последнего VP state. | Нет |
| POST | `/api/subscribe` | Stub Stripe Checkout redirect на `/pricing`. | Нет / TODO user JWT |
| GET | `/api/subscribe/success` | Stub callback после оплаты, redirect на `/team-builder?upgraded=1`. | Нет |
| GET | `/api/billing/portal` | Stub Stripe Customer Portal redirect на `/account/billing`. | Нет / TODO user JWT |
| POST | `/api/webhooks/stripe` | Stub Stripe webhook handler. | TODO Stripe signature |

## Auth routes outside `/api`

| Метод | Путь | Назначение | Auth |
|-------|------|------------|------|
| GET | `/auth/login` | HTML форма входа. | Нет |
| POST | `/auth/login` | Login form submit; выдаёт JWT cookie и redirect на `/team-builder`. | Нет |
| GET | `/auth/register` | HTML форма регистрации. | Нет |
| POST | `/auth/register` | Register form submit; создаёт пользователя, выдаёт JWT cookie и redirect на `/team-builder`. | Нет |
| GET | `/auth/logout` | Удаляет auth cookie и redirect на `/`. | Cookie optional |
| GET | `/auth/me` | JSON текущего пользователя или `null`. | Optional JWT cookie |
| GET | `/auth/providers` | Список доступных OAuth providers для UI. | Нет |
| GET | `/auth/{provider}/login` | Начало OAuth flow: redirect на provider authorize URL. | Нет |
| GET | `/auth/{provider}/callback` | OAuth callback: проверка state, обмен code, link/create user, JWT cookie, redirect на `/`. | OAuth state/code |

## Page / health routes used by UI

| Метод | Путь | Назначение | Auth |
|-------|------|------------|------|
| GET | `/health` | Root-level health check для hosting/probes. | Нет |
| GET | `/` | Главная страница. | Нет |
| GET | `/team-builder` | Team Builder page. | Optional cookie/UI gate |
| GET | `/scenario-setup` | Scenario Setup page. | Optional cookie/UI gate |
| GET | `/my-rosters` | Saved rosters page. | Optional cookie/UI gate |
| GET | `/faction-browser` | Faction Browser page. | Нет |
| GET | `/pricing` | Pricing / subscription page. | Нет |
| GET | `/account/billing` | Billing account page. | Optional cookie/UI gate |
| GET | `/replays` | Replay list page. | Нет |
| GET | `/replay/{game_id}` | Replay viewer page alias. | Нет |
| GET | `/round-viewer/{scenario_id}` | Round Viewer page. | Нет |
| GET | `/result/{game_id}` | Result screen page. | Нет |
| GET | `/pmf-chart` | PMF chart page. | Нет |
| GET | `/favicon.ico` | Redirect на `/static/favicon.svg`. | Нет |
| GET | `/sentry-debug` | Debug endpoint that intentionally raises an error. | Dev/debug only |

## Maintenance notes

- Detailed schemas live in Swagger only: http://127.0.0.1:8000/docs.
- FastAPI currently registers `/api/detachments` and `/api/detachments/{detachment_name}` from both `web/routes/api.py` and `web/routes/api_detachments.py`. The public path is listed once above; route ownership should eventually be consolidated in `api_detachments.py`.
- Roster endpoints use JWT from the auth cookie via `get_current_user`; `/api/me` and `/auth/me` use optional auth and return `null` when anonymous.
- Billing endpoints are development stubs until real Stripe Checkout/Portal/Webhook verification is implemented.
