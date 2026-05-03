# Features â€” Ð”Ð¾ÐºÑƒÐ¼ÐµÐ½Ñ‚Ð°Ñ†Ð¸Ñ Ñ„Ð¸Ñ‡

ÐŸÐ¾Ð»Ð½Ñ‹Ð¹ Ð¸Ð½Ð´ÐµÐºÑ Ð²ÑÐµÑ… feature-ÑÐ¿ÐµÑ†Ð¸Ñ„Ð¸ÐºÐ°Ñ†Ð¸Ð¹ Ð¿Ð¾ Ñ„Ð°Ð·Ð°Ð¼ Ñ€Ð°Ð·Ñ€Ð°Ð±Ð¾Ñ‚ÐºÐ¸.
ÐšÐ°Ð¶Ð´Ñ‹Ð¹ Ñ„Ð°Ð¹Ð» ÑÐ¾Ð´ÐµÑ€Ð¶Ð¸Ñ‚: SMART-Ñ†ÐµÐ»ÑŒ, data model, implementation details, Ñ‚ÐµÑÑ‚Ñ‹.

---

## Phase 1: Combat Engine

**Ð¦ÐµÐ»ÑŒ:** `curl /api/simulate` â†’ JSON Ñ Ñ€Ð°ÑÐ¿Ñ€ÐµÐ´ÐµÐ»ÐµÐ½Ð¸ÐµÐ¼ ÑƒÑ€Ð¾Ð½Ð°.

| # | Ð¤Ð¸Ñ‡Ð° | Ð§Ð°ÑÑ‹ | ÐŸÑ€Ð¸Ð¾Ñ€Ð¸Ñ‚ÐµÑ‚ | Ð¡Ñ‚Ð°Ñ‚ÑƒÑ |
|---|------|------|-----------|--------|
| [F1.1](f1.1-unit-dataclass.md) | Unit Dataclass â€” Ñ€Ð°ÑÑˆÐ¸Ñ€ÐµÐ½Ð¸Ðµ Ð¿Ð¾Ð»ÐµÐ¹ | 2h | 1 | âœ… |
| [F1.2](f1.2-weapon-dataclass.md) | Weapon Dataclass â€” DiceExpr | 1h | 1 | âœ… |
| [F1.3](f1.3-modifier-system.md) | Modifier System â€” Â±1, caps, rerolls | 3h | 2 | âœ… |
| [F1.4](f1.4-wiki-loader.md) | Wiki Loader â€” Ð¿Ð°Ñ€ÑÐ¸Ð½Ð³ .md â†’ Unit/Weapon | 4h | 2 | âœ… |
| [F1.5](f1.5-dice-pool.md) | Dice Pool â€” NumPy D6 Monte Carlo | 2h | 2 | âœ… |
| [F1.6](f1.6-combat-sequence.md) | Combat Sequence â€” Hitâ†’Woundâ†’Saveâ†’Damageâ†’FNP | 4h | 3 | âœ… |
| [F1.7](f1.7-weapon-keywords.md) | Weapon Keywords â€” Sustained, Lethal, Devastating | 3h | 3 | âœ… |
| [F1.8](f1.8-tests.md) | Tests â€” Shoota vs Marine, HB vs Marine, Plasma | 2h | 4 | âœ… |
| [F1.9](f1.9-api-simulate.md) | POST /api/simulate â€” Weapon Ã— Target â†’ JSON | 2h | 4 | âœ… |
| [F1.10](f1.10-pmf-chart.md) | PMF Chart â€” Chart.js Ñ€Ð°ÑÐ¿Ñ€ÐµÐ´ÐµÐ»ÐµÐ½Ð¸Ðµ ÑƒÑ€Ð¾Ð½Ð° | 4h | 5 | âœ… |
| [F1.11](f1.11-round-viewer-stub.md) | Round Viewer Stub â€” Ñ„Ð¾Ñ€Ð¼Ð° + JSON | 2h | 5 | âœ… |
| [F1.12](f1.12-multiattack.md) | MultiAttack â€” Ð½ÐµÑÐºÐ¾Ð»ÑŒÐºÐ¾ Ð¾Ñ€ÑƒÐ¶Ð¸Ð¹ + Ð¾Ñ‚Ñ€ÑÐ´Ñ‹ | 3h | 5 | âœ… |

**Ð’ÑÐµÐ³Ð¾:** 12 features, ~30 Ñ‡Ð°ÑÐ¾Ð². âœ… 100%

### Ð¡Ð²Ð¾Ð´ÐºÐ° Ð·Ð°Ð²Ð¸ÑÐ¸Ð¼Ð¾ÑÑ‚ÐµÐ¹ (Phase 1)

```mermaid
flowchart LR
    F11[F1.1] --> F14[F1.4]
    F12[F1.2] --> F14
    F14 --> F16[F1.6]
    F13[F1.3] --> F16
    F15[F1.5] --> F16
    F13 --> F17[F1.7]
    F16 --> F18[F1.8]
    F17 --> F18
    F16 --> F19[F1.9]
    F19 --> F110[F1.10]
    F110 --> F111[F1.11]
    F16 --> F112[F1.12]
```

### Ð ÐµÐºÐ¾Ð¼ÐµÐ½Ð´ÑƒÐµÐ¼Ñ‹Ð¹ Ð¿Ð¾Ñ€ÑÐ´Ð¾Ðº Ð¸Ð¼Ð¿Ð»ÐµÐ¼ÐµÐ½Ñ‚Ð°Ñ†Ð¸Ð¸

| Ð¨Ð°Ð³ | Ð¤Ð¸Ñ‡Ð¸ | ÐŸÐ¾Ñ‡ÐµÐ¼Ñƒ |
|-----|------|--------|
| 1 | **F1.1 + F1.2** â€” dataclasses | Ð£Ð¶Ðµ ÐµÑÑ‚ÑŒ, Ð´Ð¾Ñ€Ð°Ð±Ð¾Ñ‚Ð°Ñ‚ÑŒ |
| 2 | **F1.5** â€” Dice pool | ÐÐµÐ·Ð°Ð²Ð¸ÑÐ¸Ð¼ |
| 3 | **F1.4** â€” Wiki Loader | ÐÑƒÐ¶Ð½Ñ‹ F1.1/F1.2 |
| 4 | **F1.3** â€” Modifier system | ÐÑƒÐ¶ÐµÐ½ F1.5 |
| 5 | **F1.6** â€” Combat sequence | ÐÑƒÐ¶Ð½Ð¾ Ð²ÑÑ‘ Ð²Ñ‹ÑˆÐµ |
| 6 | **F1.7** â€” Keywords | Ð Ð°ÑÑˆÐ¸Ñ€ÑÐµÑ‚ F1.6 |
| 7 | **F1.8** â€” Tests | ÐŸÐ¾ÑÐ»Ðµ F1.6+F1.7 |
| 8 | **F1.9** â€” API | ÐŸÐ¾ÑÐ»Ðµ F1.6 |
| 9 | **F1.12** â€” MultiAttack | Ð Ð°ÑÑˆÐ¸Ñ€ÑÐµÑ‚ F1.6 |
| 10 | **F1.10+F1.11** â€” UI | ÐŸÐ¾ÑÐ»Ðµ F1.9 |

---

## Phase 2: Game System

**Ð¦ÐµÐ»ÑŒ:** Ð¡Ð¾Ð±Ñ€Ð°Ñ‚ÑŒ Ð´Ð²Ðµ Ð°Ñ€Ð¼Ð¸Ð¸, Ñ€Ð°ÑÑÑ‚Ð°Ð²Ð¸Ñ‚ÑŒ Ð½Ð° ÐºÐ°Ñ€Ñ‚Ðµ, Ð¿Ñ€Ð¾Ð¶Ð¸Ñ‚ÑŒ 1 Ñ€Ð°ÑƒÐ½Ð´.

| # | Ð¤Ð¸Ñ‡Ð° | Ð§Ð°ÑÑ‹ | ÐŸÑ€Ð¸Ð¾Ñ€Ð¸Ñ‚ÐµÑ‚ | Ð¡Ñ‚Ð°Ñ‚ÑƒÑ |
|---|------|------|-----------|--------|
| [F2.1](f2.1-game-state.md) | Game State Dataclass | 4h | 1 | âœ… |
| [F2.2](f2.2-2d-map.md) | 2D Map â€” NumPy grid, terrain, deploy zones | 6h | 1 | âœ… |
| [F2.3](f2.3-line-of-sight.md) | Line of Sight â€” Bresenham ray casting | 4h | 2 | âœ… |
| [F2.4](f2.4-missions.md) | Missions â€” objectives, scoring, deployment | 3h | 2 | âœ… |
| [F2.5](f2.5-game-loop.md) | Game Loop â€” 6 Ñ„Ð°Ð·, run_round() | 6h | 2 | âœ… |
| [F2.6](f2.6-phase-transitions.md) | Phase Transitions â€” priority, alternating activations | 4h | 3 | âœ… |
| [F2.7](f2.7-battle-shock-cp-stratagems.md) | Battle-shock, CP, Stratagems | 4h | 3 | âœ… |
| [F2.8](f2.8-victory-points.md) | Victory Points â€” tracking, end-game | 2h | 3 | âœ… |
| [F2.9](f2.9-roster-validation.md) | Roster Validation â€” PTS, Warlord, caps | 3h | 4 | âœ… |
| [F2.10](f2.10-roster-crud.md) | Roster CRUD â€” SQLite save/load/delete | 2h | 4 | âœ… |
| [F2.11](f2.11-team-builder-ui.md) | Team Builder UI â€” Alpine.js, PTS bar | 8h | 5 | âœ… |
| [F2.12](f2.12-leader-compatibility.md) | Leader Compatibility Checker | 3h | 5 | âœ… |

**Ð’ÑÐµÐ³Ð¾:** 12 features, ~45 Ñ‡Ð°ÑÐ¾Ð². âœ… 100%

---

## Phase 3: AI & Automation

**Ð¦ÐµÐ»ÑŒ:** ÐÐ°Ð¶Ð°Ñ‚ÑŒ "Simulate" â†’ AI Ñ€Ð°Ð·Ñ‹Ð³Ñ€Ñ‹Ð²Ð°ÐµÑ‚ 5 Ñ€Ð°ÑƒÐ½Ð´Ð¾Ð² â†’ replay.

| # | Ð¤Ð¸Ñ‡Ð° | Ð§Ð°ÑÑ‹ | ÐŸÑ€Ð¸Ð¾Ñ€Ð¸Ñ‚ÐµÑ‚ | Ð¡Ñ‚Ð°Ñ‚ÑƒÑ |
|---|------|------|-----------|--------|
| [F3.1](f3.1-greedy-decision-engine.md) | Greedy decision engine â€” target/action evaluation | 6h | 1 | âœ… |
| [F3.2](f3.2-faction-ai-profiles.md) | Faction AI Profiles â€” wiki-driven (Orks, Tau, AdMech) | 4h | 2 | ðŸŸ¢ |
| [F3.4](f3.4-deployment-ai.md) | Deployment AI: zone placement logic | 3h | 3 | âœ… |
| [F3.4](f3.5-autoplay.md) | Auto-play: AI vs AI full scenario | 6h | 3 | â³ |
| [F3.5](f3.6-replay-recording.md) | Replay recording: JSON event log per round/phase | 3h | 4 | â³ |
| [F3.6](f3.7-round-viewer.md) | Round viewer: step-by-step replay UI | 6h | 5 | â³ |
| [F3.7](f3.8-result-screen.md) | Result screen: kills, damage, VP timeline chart | 3h | 5 | â³ |

**Ð’ÑÐµÐ³Ð¾:** 7 features, ~35 Ñ‡Ð°ÑÐ¾Ð². ðŸŸ¢ 14% (1/7 done)

**Deprecated files (Ð·Ð°Ð¼ÐµÐ½ÐµÐ½Ñ‹):**
- [F3.2 â€” Ork AI](f3.2-ork-ai.md) (deprecated â†’ superseded by F3.2 Faction AI Profiles)
- [F3.3 â€” T'au AI](f3.3-tau-ai.md) (deprecated â†’ superseded by F3.2 Faction AI Profiles)
- [F3.9 â€” AdMech AI](f3.9-admech-ai.md) (deprecated â†’ superseded by F3.2 Faction AI Profiles)

### Ð ÐµÐºÐ¾Ð¼ÐµÐ½Ð´ÑƒÐµÐ¼Ñ‹Ð¹ Ð¿Ð¾Ñ€ÑÐ´Ð¾Ðº Ð¸Ð¼Ð¿Ð»ÐµÐ¼ÐµÐ½Ñ‚Ð°Ñ†Ð¸Ð¸

| Ð¨Ð°Ð³ | Ð¤Ð¸Ñ‡Ð¸ | ÐŸÐ¾Ñ‡ÐµÐ¼Ñƒ |
|-----|------|--------|
| 1 | **F3.1** â€” Greedy decision engine | Ð¯Ð´Ñ€Ð¾ AI, Ð³Ð¾Ñ‚Ð¾Ð²Ð¾ âœ… |
| 2 | **F3.2** â€” Faction AI Profiles | Ð§Ð¸Ñ‚Ð°ÐµÑ‚ Ð¿Ñ€Ð¾Ñ„Ð¸Ð»Ð¸ Ð¸Ð· wiki, Ð±ÐµÐ· Ñ…Ð°Ñ€Ð´ÐºÐ¾Ð´Ð° |
| 3 | **F3.3** â€” Deployment AI | ÐÑƒÐ¶ÐµÐ½ Ð´Ð»Ñ Ð¿Ð¾Ð»Ð½Ð¾Ð³Ð¾ Ñ†Ð¸ÐºÐ»Ð° |
| 4 | **F3.4** â€” Auto-play | Ð˜Ð½Ñ‚ÐµÐ³Ñ€Ð°Ñ†Ð¸Ñ Ð²ÑÐµÑ… ÐºÐ¾Ð¼Ð¿Ð¾Ð½ÐµÐ½Ñ‚Ð¾Ð² |
| 5 | **F3.5** â€” Replay recording | Ð›Ð¾Ð³Ð¸Ñ€Ð¾Ð²Ð°Ð½Ð¸Ðµ Ñ€ÐµÐ·ÑƒÐ»ÑŒÑ‚Ð°Ñ‚Ð¾Ð² |
| 6 | **F3.6 + F3.7** â€” Round viewer + Result screen | UI Ð´Ð»Ñ Ð¿Ñ€Ð¾ÑÐ¼Ð¾Ñ‚Ñ€Ð° Ñ€ÐµÐ¿Ð»ÐµÐµÐ² |

---

## Phase 4: Web UI Polish

**Ð¦ÐµÐ»ÑŒ:** ÐŸÐ¾Ð»Ð½Ð¾Ñ†ÐµÐ½Ð½Ð¾Ðµ Ð²ÐµÐ±-Ð¿Ñ€Ð¸Ð»Ð¾Ð¶ÐµÐ½Ð¸Ðµ, Ð³Ð¾Ñ‚Ð¾Ð²Ð¾Ðµ Ðº Ð¿Ð¾Ð»ÑŒÐ·Ð¾Ð²Ð°Ñ‚ÐµÐ»ÑÐ¼.

| # | Ð¤Ð¸Ñ‡Ð° | Ð§Ð°ÑÑ‹ | ÐŸÑ€Ð¸Ð¾Ñ€Ð¸Ñ‚ÐµÑ‚ | Ð¡Ñ‚Ð°Ñ‚ÑƒÑ |
|---|------|------|-----------|--------|
| [F4.1](f4.1-faction-browser.md) | Faction browser with category/PTS filter | 4h | 1 | âœ… |
| [F4.2](f4.2-unit-modal.md) | Unit modal: squad size, loadout, wargear selection | 6h | 1 | âœ… |
| [F4.3](f4.3-detachment-picker.md) | Detachment picker with rule preview | 3h | 2 | âœ… |
| [F4.4](f4.4-synergy-hints.md) | Synergy hints: leader compatibility, transport capacity | 4h | 2 | âœ… |
| [F4.5](f4.5-canvas-map.md) | Canvas map: terrain tiles + deploy zones interactivity | 8h | 3 | âœ… |
| [F4.6](f4.6-progressive-disclosure.md) | Progressive Disclosure: Beginner/Intermediate/Expert modes | 4h | 4 | â³ |
| [F4.7](f4.7-stat-tooltips.md) | Tooltips on every stat (M/T/SV/W/LD/OC) | 3h | 4 | â³ |
| [F4.8](f4.8-svg-icons.md) | SVG icons integration in unit cards | 2h | 5 | âœ… |

**Ð’ÑÐµÐ³Ð¾:** 8 features, ~35 Ñ‡Ð°ÑÐ¾Ð². âœ… 75% (6/8 done)

### Ð¡Ð²Ð¾Ð´ÐºÐ° Ð·Ð°Ð²Ð¸ÑÐ¸Ð¼Ð¾ÑÑ‚ÐµÐ¹ (Phase 4)

```mermaid
flowchart LR
    F41[F4.1] --> F42[F4.2]
    F42 --> F44[F4.4]
    F41 --> F43[F4.3]
    F44 --> F46[F4.6]
    F42 --> F47[F4.7]
    F46 --> F47
    F41 --> F48[F4.8]
    F42 --> F48
    subgraph P0["Phase 0.8"]
        ICONS["SVG Icons + ICON_MAP"]
    end
    subgraph P2["Phase 2"]
        F211["F2.11 Team Builder UI"]
        F212["F2.12 Leader Compatibility"]
    end
    ICONS --> F48
    F211 --> F41
    F212 --> F44
```

### Ð ÐµÐºÐ¾Ð¼ÐµÐ½Ð´ÑƒÐµÐ¼Ñ‹Ð¹ Ð¿Ð¾Ñ€ÑÐ´Ð¾Ðº Ð¸Ð¼Ð¿Ð»ÐµÐ¼ÐµÐ½Ñ‚Ð°Ñ†Ð¸Ð¸

| Ð¨Ð°Ð³ | Ð¤Ð¸Ñ‡Ð¸ | ÐŸÐ¾Ñ‡ÐµÐ¼Ñƒ |
|-----|------|--------|
| 1 | **F4.1** â€” Faction browser | Ð‘Ð°Ð·Ð° Ð´Ð»Ñ Ð²ÑÐµÐ³Ð¾ UI, Ð½ÑƒÐ¶Ð½Ð¾ ÑÐ½Ð°Ñ‡Ð°Ð»Ð° |
| 2 | **F4.2** â€” Unit modal | Ð—Ð°Ð²Ð¸ÑÐ¸Ñ‚ Ð¾Ñ‚ F4.1, ÑÐ´Ñ€Ð¾ Ð²Ð·Ð°Ð¸Ð¼Ð¾Ð´ÐµÐ¹ÑÑ‚Ð²Ð¸Ñ |
| 3 | **F4.3** â€” Detachment picker | ÐÐµÐ·Ð°Ð²Ð¸ÑÐ¸Ð¼ Ð¿Ð¾ÑÐ»Ðµ F4.1 |
| 4 | **F4.8** â€” SVG icons | Ð‘Ñ‹ÑÑ‚Ñ€Ð°Ñ Ð¿Ð¾Ð±ÐµÐ´Ð°, Ñ€Ð°Ð·Ð½Ð¾ÑÐ¸Ñ‚ÑÑ Ð¿Ð¾ Ð²ÑÐµÐ¼ ÐºÐ°Ñ€Ñ‚Ð¾Ñ‡ÐºÐ°Ð¼ |
| 5 | **F4.4** â€” Synergy hints | ÐÑƒÐ¶Ð½Ñ‹ F4.2, F2.12 |
| 6 | **F4.7** â€” Stat tooltips | Ð Ð°ÑÐ¿Ñ€ÐµÐ´ÐµÐ»ÑÐµÑ‚ÑÑ Ð¿Ð¾ Ð²ÑÐµÐ¼ ÑÑ‚Ñ€Ð°Ð½Ð¸Ñ†Ð°Ð¼ |
| 7 | **F4.6** â€” Progressive Disclosure | ÐœÐµÐ½ÑÐµÑ‚ Ð¿Ð¾Ð²ÐµÐ´ÐµÐ½Ð¸Ðµ Ð²ÑÐµÑ… Ð¾ÑÑ‚Ð°Ð»ÑŒÐ½Ñ‹Ñ… UI |
| 8 | **F4.5** â€” Canvas map | Ð¡Ð°Ð¼Ñ‹Ð¹ Ð±Ð¾Ð»ÑŒÑˆÐ¾Ð¹, Ð¼Ð¾Ð¶Ð½Ð¾ Ð´ÐµÐ»Ð°Ñ‚ÑŒ Ð¿Ð°Ñ€Ð°Ð»Ð»ÐµÐ»ÑŒÐ½Ð¾ |

---

## Phase 5: Production

**Ð¦ÐµÐ»ÑŒ:** ÐŸÑ€Ð¸Ð»Ð¾Ð¶ÐµÐ½Ð¸Ðµ Ð½Ð° ÑÐµÑ€Ð²ÐµÑ€Ðµ, HTTPS, Ð¼Ð¾Ð½Ð¸Ñ‚Ð¾Ñ€Ð¸Ð½Ð³.

| # | Ð¤Ð¸Ñ‡Ð° | Ð§Ð°ÑÑ‹ | ÐŸÑ€Ð¸Ð¾Ñ€Ð¸Ñ‚ÐµÑ‚ | Ð¡Ñ‚Ð°Ñ‚ÑƒÑ |
|---|------|------|-----------|--------|
| [F5.1](f5.1-dockerfile-compose.md) | Dockerfile + docker-compose | 3h | 1 | âœ… |
| [F5.2](f5.2-deployment.md) | Deployment (Dokku / Railway / self-host) | 4h | 1 | âœ… |
| [F5.3](f5.3-rate-limiting.md) | Rate limiting (slowapi) | 1h | 2 | â³ |
| [F5.4](f5.4-cors-csp-security.md) | CORS hardening + CSP security headers | 1h | 2 | â³ |
| [F5.5](f5.5-logging-sentry.md) | Logging (structlog) + Sentry error tracking | 2h | 3 | â³ |
| [F5.6](f5.6-cicd-github-actions.md) | CI/CD: GitHub Actions (lint + test + deploy) | 4h | 3 | â³ |
| [F5.7](f5.7-sqlite-backup.md) | SQLite backup strategy + restore script | 1h | 4 | â³ |

**Ð’ÑÐµÐ³Ð¾:** 7 features, ~16 Ñ‡Ð°ÑÐ¾Ð². ðŸŸ¢ 29% (2/7 done)

### Ð ÐµÐºÐ¾Ð¼ÐµÐ½Ð´ÑƒÐµÐ¼Ñ‹Ð¹ Ð¿Ð¾Ñ€ÑÐ´Ð¾Ðº Ð¸Ð¼Ð¿Ð»ÐµÐ¼ÐµÐ½Ñ‚Ð°Ñ†Ð¸Ð¸

| Ð¨Ð°Ð³ | Ð¤Ð¸Ñ‡Ð¸ | ÐŸÐ¾Ñ‡ÐµÐ¼Ñƒ |
|-----|------|--------|
| 1 | **F5.1** â€” Dockerfile + compose | ÐžÑÐ½Ð¾Ð²Ð° Ð´Ð»Ñ Ð´ÐµÐ¿Ð»Ð¾Ñ |
| 2 | **F5.2** â€” Deployment | Ð Ð°Ð·Ð²ÐµÑ€Ð½ÑƒÑ‚ÑŒ Ð¿Ñ€Ð¸Ð»Ð¾Ð¶ÐµÐ½Ð¸Ðµ |
| 3 | **F5.3** â€” Rate limiting | Ð—Ð°Ñ‰Ð¸Ñ‚Ð° Ð¾Ñ‚ Ð±Ð¾Ñ‚Ð¾Ð² |
| 4 | **F5.4** â€” CORS + CSP | Ð‘ÐµÐ·Ð¾Ð¿Ð°ÑÐ½Ð¾ÑÑ‚ÑŒ |
| 5 | **F5.5** â€” Logging + Sentry | ÐœÐ¾Ð½Ð¸Ñ‚Ð¾Ñ€Ð¸Ð½Ð³ |
| 6 | **F5.6** â€” CI/CD | ÐÐ²Ñ‚Ð¾Ð¼Ð°Ñ‚Ð¸Ð·Ð°Ñ†Ð¸Ñ |
| 7 | **F5.7** â€” SQLite backup | ÐÐ°Ð´Ñ‘Ð¶Ð½Ð¾ÑÑ‚ÑŒ Ð´Ð°Ð½Ð½Ñ‹Ñ… |

---

## Ð¡Ð²Ð¾Ð´ÐºÐ°

| Ð¤Ð°Ð·Ð° | Features | Ð§Ð°ÑÑ‹ | Ð¡Ñ‚Ð°Ñ‚ÑƒÑ |
|------|----------|------|--------|
| **Phase 1** â€” Combat Engine | 12 | ~30h | âœ… 100% |
| **Phase 2** â€” Game System | 12 | ~45h | âœ… 100% |
| **Phase 3** â€” AI & Automation | 7 | ~35h | ðŸŸ¢ 29% |
| **Phase 4** â€” Web UI Polish | 8 | ~35h | âœ… 75% |
| **Phase 5** â€” Production | 7 | ~16h | ðŸŸ¢ 29% |
| **Phase 6** â€” Monetization | 6 | ~15h | â³ 0% |
| **Phase 7** â€” Expansion | 10 | ~40h | â³ 0% |
| **Ð˜Ñ‚Ð¾Ð³Ð¾** | **~62** | **~216h** | |
