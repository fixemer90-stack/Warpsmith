---
title: T'au Empire
created: 2026-04-30
updated: 2026-04-30
type: entity
tags: [tau, xenos]
sources: []
edition: 10e
confidence: medium
ai:
  weights:
    kill_efficiency: 1.2
    charge_aggression: 0.3
    survival_risk: 1.0
    objective_value: 0.7
    threat_reduction: 1.0
  behaviors:
    - id: kauyon
      description: "Kauyon — Patient Hunter: fishing for 6s на раундах 3+"
      trigger:
        phase: shooting
        round_min: 3
        round_max: 5
        cooldown: 0
      effects:
        weights_override:
          kill_efficiency: 1.8
          survival_risk: 1.3
    - id: montka
      description: "Mont'ka — Killing Blow: +1 AP раунды 1-3"
      trigger:
        phase: shooting
        round_min: 1
        round_max: 3
        cooldown: 0
      effects:
        weights_override:
          kill_efficiency: 1.4
          charge_aggression: 0.6
    - id: for_the_greater_good
      description: 'For The Greater Good — overwatch при заряде в 6"'
      trigger:
        phase: charge
        round_min: 1
        round_max: 20
        cooldown: 1
      effects:
        weights_override:
          survival_risk: 1.5
  target_priority:
    monster: 1.3
    vehicle: 1.2
    character: 1.1
    infantry: 1.0
    battleline: 0.9
  deployment:
    front_line: ["battleline", "infantry"]
    mid_field: ["character", "elite", "battlesuit"]
    back_field: ["vehicle", "artillery", "fly"]
    reserve: ["deep-strike", "stealth"]

---

# T'au Empire

> *"For the Greater Good."*

Империя Тау (T'au Empire) в Warhammer 40,000 10-й редакции — высокотехнологичная армия, специализирующаяся на стрельбе на дальних дистанциях, мобильности и координации (Markerlights). Ближний бой — слабость Тау.

## Army Rule: For The Greater Good (FTGG)

**Guided Fire** — ключевое правило армии. В фазу стрельбы вы можете выбрать один отряд как **Spotter** (наблюдатель) и один как **Guided** (наводимый):

- **Guided unit** получает +1 к броску на попадание (BS) при стрельбе по видимой для Spotter цели
- **Spotter unit** не может стрелять в этом ходу (кроме автономного оружия — Pistols, или если у отряда есть правило, разрешающее это)
- Отряд может быть Spotter только один раз за ход
- **Markerlight** (дроны/способности): некоторые отряды могут действовать как Spotter без потери стрельбы или улучшают эффект (+1 BS и игнорирование Cover)

## Detachments

| Детачмент | Правило | Стиль игры |
|-----------|---------|------------|
| [[Kauyon]] | Patient Hunter — с 3-го раунда Sustained Hits 1 (или 2 в 5+) | Засада, контроль дистанции |
| [[Mont'ka]] | Strike Swiftly — в 1-2 раундах Assault на всё оружие, +1AP в 9" | Агрессивный старт |
| [[Retaliation Cadre]] | Deadly Precision — +1S в 9" против ближайшей цели | Баттлсьюты |
| [[Auxiliary Cadre]] | United In Purpose — Kroot/Vespid получают FTGG | Смешанный |

## Units

### Characters
- [[Cadre Fireblade]] — офицер, усиливающий стрельбу Strike/Breacher
- [[Commander Farsight]] — эпический герой, Crisis командир (Farsight Enclaves)
- [[Commander Shadowsun]] — верховный командующий, Epic Hero, дроны-призраки
- [[Commander In Coldstar Battlesuit]] — быстрый командир, M14"
- [[Commander In Enforcer Battlesuit]] — прочный командир, SV2+
- [[Ethereal]] — духовный лидер, генерация CP, Invocations
- [[Darkstrider]] — Epic Hero, Pathfinder лидер
- [[Longstrike]] — Epic Hero, Hammerhead командир
- [[Aun'Shi]] — Epic Hero Ethereal с ближним боем
- [[Aun'Va]] — Epic Hero, Master of the Undying Spirit

### Battleline
- [[Breacher Team]] — штурмовая пехота, дробовики (Close-range blast)
- [[Strike Team]] — стрелковая пехота, Pulse Rifles/Carbines

### Infantry
- [[Pathfinder Team]] — разведчики, Markerlights, Rail Rifles/Ion Guns
- [[Stealth Battlesuits]] — скрытные баттлсьюты, Infiltrator, Markerlight
- [[Vespid Stingwings]] — летающая пехота (Auxiliary)
- [[Kroot Carnivores]] — ближний бой пехота (Auxiliary)
- [[Kroot Farstalkers]] — разведчики Kroot

### Battlesuits
- [[Crisis Battlesuits]] — универсальные баттлсьюты, 3 оружия
- [[Crisis Sunforge]] — анти-техника Crisis (Fusion Blasters)
- [[Crisis Fireknife]] — средняя дистанция Crisis (Missile Pods)
- [[Crisis Starscythe]] — ближняя дистанция Crisis (Burst Cannons/Flamers)
- [[Broadside Battlesuits]] — тяжёлые баттлсьюты, Rail Rifles/High-Yield Missiles
- [[Ghostkeel Battlesuit]] — одиночный баттлсьют, Stealth, Lone Operative
- [[Riptide Battlesuit]] — тяжёлый баттлсьют, Nova Reactor
- [[Stormsurge]] — сверхтяжёлый баттлсьют, Titanic, Artillery

### Vehicles
- [[Devilfish]] — транспорт APCs, Transport 12
- [[Hammerhead Gunship]] — основной танк, Railgun (S20 AP-5 D6+6) или Ion Cannon
- [[Sky Ray Gunship]] — ПВО/анти-техника, Seeker Missiles ×6

### Drones
- [[Tactical Drones]] — лёгкие летающие дроны, Markerlights
- [[Remora Stealth Drones]] — FW, Stealth Drones

### Aircraft
- [[Barracuda]] — FW, истребитель
- [[Tiger Shark]] — FW, тяжёлый транспорт/бомбер
- [[AX-1-0 Tiger Shark]] — тяжёлый истребитель с Heavy Rail Cannons

### Fortifications
- [[Tidewall Defence Line]] — укрепления

## Keywords

- **Faction Keywords:** XENOS, T'AU EMPIRE, FARSIGHT ENCLAVES (для Farsight units)
- **Common Unit Keywords:** INFANTRY, CHARACTER, BATTLESUIT, JET PACK, VEHICLE, TRANSPORT, FLY, DRONE, MOUNTED, TOWERING

## Balance Dataslate v3.4 Updates

> Source: Balance Dataslate v3.4 (2026), p.26

### Army Rule: For the Greater Good (FTGG) — Revised

The FTGG rule has been significantly reworked:

- **Observer selection**: At the start of your Shooting phase, select units with this ability to become **Observer units**.
- **Spotted units**: Each Observer selects one visible enemy unit as their **Spotted unit** (each enemy can only be Spotted once per phase).
- **Guided units**: Units with FTGG (excluding Observers) are **Guided** while targeting Spotted units.
- **Effect**: Guided units improve BS by 1. If the Observer has the **Markerlight** keyword, attacks gain **[IGNORES COVER]**.

### Detachment / Enhancement Changes

| Detachment | Enhancement | Change |
|------------|-------------|--------|
| **Kauyon** | Through Unity, Devastation | Observer units grant Guided units **[LETHAL HITS]** against their Spotted unit. Excludes Kroot Shaper models. |
| **Mont'ka** | Coordinated Exploitation | Observer units grant Guided units **[SUSTAINED HITS 1]** against their Spotted unit. Excludes Kroot Shaper models. |

#### Retaliation Cadre — Bonded Heroes

- **Change**: Battlesuit models get **+1 Strength** when targeting a unit within 12", and **+1 Armour Penetration** as well when within 9".

### Datasheet Changes

| Datasheet | Change |
|-----------|--------|
| **Firesight Team** | Precise Targeting: re-roll the **Hit roll** against Spotted units. |
| **Pathfinder Team** | Target Uploaded: **+1 BS** and **[IGNORES COVER]** against Spotted units. |
| **Riptide** | Ion accelerator reworked: Standard — 72", A6, BS4+, S9, AP-2, D3. Supercharge — [HAZARDOUS], S10, AP-3, D4. |
| **Stealth Battlesuits** | Forward Observers: Guided units re-roll **Hit rolls of 1 and Wound rolls of 1** against the Spotted unit. |
