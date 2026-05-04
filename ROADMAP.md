# Roadmap — Warpsmith

> Дорожная карта разработки. Версия 0.3.0
> **Статус:** Phase 0 ✅ | Phase 1 ✅ | Phase 2 ✅

---

## ✅ Phase 0: Foundation

```
[████████████████████] 100% · 12 features
```

### Features

| #    | Статус | Фича                                                    | Часы |
| ---- | ------ | ------------------------------------------------------- | ---- |
| 0.1  | ✅      | FastAPI scaffold + main.py + структура backend/web/docs | 4h   |
| 0.2  | ✅      | JWT auth · bcrypt · httponly cookie middleware          | 3h   |
| 0.3  | ✅      | Register / Login / Logout routes + формы                | 2h   |
| 0.4  | ✅      | OAuth Google + VK providers (Provider Interface)        | 4h   |
| 0.5  | ✅      | SQLite schema + migration (users, rosters, replays)     | 2h   |
| 0.6  | ✅      | Wiki vault: 360+ страниц (Orks, Tau, AdMech, rules)     | 20h  |
| 0.7  | ✅      | C4 · ADR (11) · SRS (7 разделов) · UX docs              | 6h   |
| 0.8  | ✅      | SVG Icons · ICON_MAP (16 категорий юнитов)              | 2h   |
| 0.9  | ✅      | base.html + Tailwind CDN + HTMX + Alpine.js             | 2h   |
| 0.10 | ✅      | Billing stubs · Feature Gate · Free/Premium tiers       | 3h   |
| 0.11 | ✅      | Balance Dataslate v3.4 — all faction updates applied    | 2h   |
| 0.12 | ✅      | Faction Packs: AdMech (26 стр.) + Ork Errata (v1.3)     | 4h   |

---

## ✅ Phase 1: Combat Engine

```
[████████████████████] 100% · 12 features
```

**Цель:** `curl /api/simulate` → JSON с распределением урона.

### Features

| # | Статус | Фича | Зависимости | Часы |
|---|---|--------|------|-------------|------|
| 1.1 | ✅ | Unit dataclass (M/T/SV/W/LD/OC, weapons, abilities) | Wiki schema | 2h |
| 1.2 | ✅ | Weapon dataclass (S/AP/D, keywords: Sustained, Lethal...) | — | 1h |
| 1.3 | ✅ | Modifier system (±1, rerolls, caps, +1 to hit/wound) | — | 3h |
| 1.4 | ✅ | Wiki Loader — парсинг .md frontmatter → Unit objects | SCHEMA.md | 4h |
| 1.5 | ✅ | Dice pool — NumPy D6 Monte Carlo engine | numpy | 2h |
| 1.6 | ✅ | Combat sequence: Hit → Wound → Save → Damage → FNP | dice, model | 4h |
| 1.7 | ✅ | Modifiers: Sustained Hits, Lethal, Devastating, Ignores Cover | combat | 3h |
| 1.8 | ✅ | Tests: Shoota vs Marine, HB vs Marine, Plasma overcharge | combat | 2h |
| 1.9 | ✅ | POST /api/simulate — Weapon × Target → JSON result | combat | 2h |
| 1.10 | ✅ | PMF chart — damage distribution graph (Chart.js) | api | 4h |
| 1.11 | ✅ | Round Viewer stub — отображение JSON результата | api | 2h |
| 1.12 | ✅ | MultiAttack — несколько оружий + отряды | combat | 3h |

---

## 🚧 Phase 2: Game System

```
[████████████████████] 100% · 12 features
```

**Цель:** Полный Game Loop с картой, миссиями, ростерами.

**Все 12 фич реализованы!**

### Features

| # | Статус | Фича | Часы |
|---|--------|------|------|
| 2.1 | ✅ | Game State dataclass: positions, wounds, CP, VP, round | 4h |
| 2.2 | ✅ | 2D Map: NumPy array, deploy zones, terrain types | 6h |
| 2.3 | ✅ | Line of Sight (LoS) — ray casting | 4h |
| 2.4 | ✅ | Missions: objectives, scoring, deployment rules | 3h |
| 2.5 | ✅ | Game Loop: Command → Movement → Shooting → Charge → Fight | 6h |
| 2.6 | 🟢 | Phase transitions, priority, alternating activations | 4h |
| 2.7 | 🟢 | Battle-shock, CP generation, stratagem resolution | 4h |
| 2.8 | 🟢 | Victory Points tracking and end-game conditions | 2h |
| 2.9 | 🟢 | Roster validation (PTS, Warlord, 3× cap) + GameSize enum | 3h |
| 2.10 | 🟢 | Roster CRUD: SQLite save/load/delete via /api/rosters | 2h |
| 2.11 | 🟢 | Team Builder UI: faction picker, unit modal, PTS bar | 8h |
| 2.12 | 🟢 | Leader compatibility checker | 3h |

---

## 🧠 Phase 3: AI & Automation

```
[████████░░░░░░░░░░] 42.9% · 3/7 features
```

**Цель:** Нажать "Simulate" → AI разыгрывает 5 раундов → replay.

### Features

|| # | Статус | Фича | Часы |
||----|--------|------|------|
|| 3.1 | ✅ | Greedy decision engine — target/action evaluation | 6h |
|| 3.2 | ✅ | Faction AI Profiles — wiki-driven (Orks, Tau, AdMech) | 4h |
|| 3.3 | ✅ | Deployment AI: zone placement logic | 3h |
|| 3.4 | ⚪ | Auto-play: AI vs AI full scenario | 6h |
|| 3.5 | ⚪ | Replay recording: JSON event log per round/phase | 3h |
|| 3.6 | ⚪ | Round viewer: step-by-step replay UI | 6h |
|| 3.7 | ⚪ | Result screen: kills, damage, VP timeline chart | 3h |
|---

## 🎨 Phase 4: Web UI Polish

```
[████████████████████] 100% · 8/8 features
```

**Цель:** Полноценное веб-приложение, готовое к пользователям.

### Features

| # | Статус | Фича | Часы |
|---|--------|------|------|
| 4.1 | ✅ | Faction browser + category/PTS filter | 4h |
| 4.2 | ✅ | Unit modal: squad size, loadout, wargear selection | 6h |
| 4.3 | ✅ | Detachment picker with rule preview | 3h |
| 4.4 | ✅ | Synergy hints: leader compatibility, transport capacity | 4h |
| 4.5 | ✅ | Canvas map: terrain tiles + deploy zones interactivity | 8h |
| 4.6 | ✅ | Progressive Disclosure: Beginner / Intermediate / Expert | 4h |
| 4.7 | ✅ | Tooltips on every stat (M/T/SV/W/LD/OC) | 3h |
|| 4.8 | ✅ | SVG icons integration in unit cards | 2h |

---

## ☁️ Phase 5: Production

```
[██░░░░░░░░░░░░░░░░] 28.6% · 2/7 features
```

**Цель:** Приложение на сервере, HTTPS, мониторинг.

### Features

| # | Статус | Фича | Часы |
|---|--------|------|------|
| 5.1 | ✅ | Dockerfile + docker-compose | 3h |
| 5.2 | ✅ | Deployment (Dokku / Railway / self-host) | 4h |
| 5.3 | ⚪ | Rate limiting (slowapi) | 1h |
| 5.4 | ⚪ | CORS hardening + CSP security headers | 1h |
| 5.5 | ⚪ | Logging (structlog) + Sentry error tracking | 2h |
| 5.6 | ⚪ | CI/CD: GitHub Actions (lint + test + deploy) | 4h |
| 5.7 | ⚪ | SQLite backup strategy + restore script | 1h |

---

## 💰 Phase 6: Monetization

```
[░░░░░░░░░░░░░░░░░░] 0% · 6 features
```

**Цель:** Первый платящий пользователь.

### Features

| # | Статус | Фича | Часы |
|---|--------|------|------|
| 6.1 | ⚪ | Stripe Checkout Session (live keys) | 4h |
| 6.2 | ⚪ | Stripe webhook — signature verification | 2h |
| 6.3 | ⚪ | Feature Gate в API: tier check на каждом эндпоинте | 3h |
| 6.4 | ⚪ | Upgrade banner + ad placeholder (Free tier) | 2h |
| 6.5 | ⚪ | Ad network integration (Carbon / EthicalAds) | 4h |
| 6.6 | ⚪ | Usage limits — max simulations/day for Free | 2h |

---

## 🚀 Phase 7: Expansion

```
[░░░░░░░░░░░░░░░░░░] 0% · 10 features
```

**Цель:** Новые фичи после MVP.

### Features

| # | Статус | Фича | Приоритет | Часы |
|---|--------|------|-----------|------|
| 7.1 | ⚪ | Fill remaining faction stubs (Chaos, Imperium) | Medium | — |
| 7.2 | ⚪ | Export: CSV/JSON для ростереров и реплеев | Low | 4h |
| 7.3 | ⚪ | Import: Battlescribe / NewRecruit roster | Medium | 8h |
| 7.4 | ⚪ | Community: публичные ростера, рейтинг, лайки | Low | 6h |
| 7.5 | ⚪ | Campaign mode: linked scenarios, persistent army | Low | 10h |
| 7.6 | ⚪ | Mobile responsive — адаптация под телефоны | Medium | 6h |
| 7.7 | ⚪ | i18n: английская локаль | Low | 8h |
| 7.8 | ⚪ | Custom AI personalities (aggressive / cautious) | Medium | 6h |
| 7.9 | ⚪ | Analytics: most used units, weapons, win rates | Low | 4h |
| 7.10 | ⚪ | Hot-seat mode: 2 players, same PC, alternating turns | Low | 8h |

---

## 📊 Сводка

| Фаза | Features | Часы | Статус | Milestone |
|------|----------|------|--------|-----------|
| **0. Foundation** | 12 | ~40ч | ✅ 100% | Скелет проекта + wiki |
| **1. Combat Engine** | 12 | ~60ч | ✅ 100% | `curl /api/simulate` → JSON + PMF |
| **2. Game System** | 12 | ~40ч | ✅ 100% | Полный Game Loop |
| **3. AI & Automation** | 7 | ~35ч | 🟢 43% |
| **4. Web UI Polish** | 8 | ~35ч | ✅ 100% |
| **5. Production** | 7 | ~15ч | 🟢 29% |
| **6. Monetization** | 6 | ~15ч | ⏳ 0% | Первый платящий |
| **7. Expansion** | 10 | ~40ч | ⏳ 0% | Новые фичи |
| **Итого** | **~75** | **~270ч** | | |
