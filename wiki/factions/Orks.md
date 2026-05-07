---
title: Orks
created: 2026-04-30
updated: 2026-04-30
type: entity
tags: [orks, xenos]
sources: [https://wahapedia.ru/wh40k10ed/factions/orks/]
edition: 10e
confidence: high
ai:
  weights:
    kill_efficiency: 1.0
    charge_aggression: 1.5
    survival_risk: 0.3
    objective_value: 0.6
    threat_reduction: 0.7
  behaviors:
    - id: waaagh
      description: "Waaagh! — призыв к тотальной атаке, бонус к заряду и ближнему бою"
      trigger:
        phase: command
        round_min: 2
        round_max: 3
        cooldown: 4
      effects:
        weights_override:
          charge_aggression: 2.5
          survival_risk: 0.1
    - id: ere_we_go
      description: "'Ere We Go — переброс заряда"
      trigger:
        phase: charge
        round_min: 1
        round_max: 20
        cooldown: 1
      effects:
        action_override: charge
  target_priority:
    monster: 1.2
    vehicle: 1.1
    character: 1.0
    infantry: 0.9
    battleline: 0.8
  deployment:
    front_line: ["battleline", "infantry"]
    mid_field: ["character", "elite"]
    back_field: ["vehicle", "artillery"]
    reserve: ["fly", "speed-freek"]

---

# Orks

> *"The Orks are the most belligerent and resourceful race in the galaxy. Rampaging across the void in their billions, the greenskins devastate everything in their path with their ramshackle weapons and war machines, taking brutish glee in wanton destruction and revelling in warfare for its own sake."*

Фракция Orks (орки) в Warhammer 40,000 10-й редакции — агрессивная армия ближнего боя с упором на численность, силу и WAAAGH!. Орки используют непрочную, но смертоносную технику, большие толпы пехоты и мощных персонажей-боссов.

## Army Rule: Waaagh!

**Waaagh!** — ключевое правило армии. Один раз за битву, в вашу фазу командования, вы можете объявить Waaagh!. До начала вашей следующей фазы командования действуют эффекты:

- **+1 к силе (S)** для атак ближнего боя моделей орков
- **+1 к движению (M)** для всех моделей орков (прибавляется к характеристике M)
- **Feel No Pain 5+** против всех ранений (для орков)
- Если объявлен **Speed Waaagh!** (в детачменте Kult of Speed), эффекты применяются только к моделям с ключевым словом **S** (Speed Freeks)

## Detachments

Орки имеют 11 детачментов:

| Детачмент | Правило | Стиль игры |
|-----------|---------|------------|
| [[War Horde]] | Get Stuck In — +1 к силе при заряде | Универсальный |
| [[Da Big Hunt]] | Da Hunt Is On — бонус против монстров/техники | Охота на крупных целей |
| [[Kult of Speed]] | Adrenaline Junkies — бонусы для быстрой техники | Механизированный |
| [[Dread Mob]] | Try Dat Button! — усиление ходячей техники | Ходячие крепости |
| [[Green Tide]] | Mob Mentality — бонусы за численность | Пехотная орда |
| [[Bully Boyz]] | Da Boss Is Watchin' — усиление Meganobz | Элитная пехота |
| [[Taktikal Brigade]] | Lissen 'Ere — тактическая гибкость | Комбинированный |
| [[More Dakka!]] | Dakka! Dakka! Dakka! — усиление стрельбы | Стрелковый |
| [[Freebooter Krew]] | Here Be Loot — бонусы за убийства | Пиратский |
| [[Kult of Speed]] | Turbo Boostas — особый Speed Waaagh! | Скоростной |
| [[Blitz Brigade]] | Eager for the Fight — ранний Waaagh! | Штурмовой |

## Units

### Characters
- [[Warboss]] — универсальный командир с мощным оружием ближнего боя
- [[Warboss In Mega Armour]] — тяжёлый командир с усиленной броней
- [[Beastboss]] — охотник на монстров верхом на звере
- [[Beastboss On Squigosaur]] — мобильный убийца на ящере
- [[Big Mek]] — техножрец, усиливающий технику
- [[Big Mek In Mega Armour]] — тяжёлый техножрец
- [[Big Mek With Shokk Attack Gun]] — техножрец со снайперским оружием
- [[Boss Snikrot]] — скрытный убийца, коммандос-лидер
- [[Deffkilla Wartrike]] — скоростной командир на трике
- [[Ghazghkull Thraka]] — верховный лидер орков, эпический герой
- [[Mek]] — младший техножрец
- [[Mozrog Skragbad]] — могучий зверь-всадник, эпический герой
- [[Painboss]] — зверь-лекарь
- [[Painboy]] — лекарь орков
- [[Wazdakka Gutsmek]] — эпический герой байкер
- [[Weirdboy]] — псайкер орков, черпающий силу Waaagh!
- [[Wurrboy]] — псайкер зверей
- [[Zodgrod Wortsnagga]] — особый грот-лидер

### Battleline
- [[Boyz]] — основная пехота орков (слота Choppa/Slugga или Shoota)
- [[Beast Snagga Boyz]] — охотники на зверей, анти-монстры

### Dedicated Transports
- [[Trukk]] — основной транспорт орков

### Other Units
- [[Battlewagon]] — тяжёлый транспорт
- [[Blitza-bommer]] — бомбардировщик
- [[Boomdakka Snazzwagon]] — лёгкая техника с тяжёлым вооружением
- [[Breaka Boyz]] — анти-техника пехота
- [[Burna Boyz]] — огнемётчики
- [[Burna-bommer]] — бомбардировщик с огнемётами
- [[Dakkajet]] — истребитель
- [[Deff Dread]] — ходячий дредноут с ближним боем
- [[Deffkoptas]] — лёгкие летающие байки
- [[Flash Gitz]] — элитная стрелковая пехота
- [[Gorkanaut]] — огромный ходячий робот (Gork)
- [[Gretchin]] — мелкие прислужники-гроты
- [[Hunta Rig]] — охотничья машина Beast Snagga
- [[Kill Rig]] — убийственная машина Beast Snagga
- [[Killa Kans]] — мини-дредноуты
- [[Kommandos]] — скрытные диверсанты
- [[Kustom Boosta-blasta]] — лёгкая пушка-техника
- [[Lootas]] — тяжёлая стрелковая пехота
- [[Meganobz]] — элитная пехота в mega armour
- [[Megatrakk Scrapjet]] — скоростной истребитель техники
- [[Mek Gunz]] — артиллерийские расчёты гротов
- [[Morkanaut]] — огромный ходячий робот (Mork)
- [[Nobz]] — элитная пехота, телохранители
- [[Rukkatrukk Squigbuggy]] — зверь-техника
- [[Shokkjump Dragsta]] — телепортирующаяся техника
- [[Squighog Boyz]] — кавалерия на squig
- [[Stompa]] — сверхтяжёлый ходячий робот
- [[Stormboyz]] — десантная пехота с реактивными ранцами
- [[Tankbustas]] — анти-техника пехота
- [[Warbikers]] — байкеры орков

## Faction Pack v1.3 — Обновления

Источник: `raw/papers/eng_22-04_wh40k_faction-pack_orks-hkgrrrimae-j5rdbqknu5.pdf`

### Errata

| Даташит | Что изменено |
|---------|-------------|
| Ghazghkull Thraka | Waaagh! Banner: LETHAL HITS дружественным ORKS в 12" от Makari |
| Warboss | Da Biggest and da Best: +4 A к melee при Waaagh! |
| Warboss in Mega Armour | Dead Brutal: 'uge choppa D3 при Waaagh! |
| Big Mek | Shokk-boosta: reroll Advance, move through terrain/models |
| Zodgrod Wortsnagga | Special Dose: +6" M при Waaagh! |
| Gretchin | Thievin' Scavengers: D6 за метку 4+ = 1 CP |
| Meganobz | Krumpin' Time: 5+ FNP при Waaagh! |
| Battlewagon | Transport 22 (12 с killkannon), Ghazghkull = 15 мест |
| Morkanaut | Big an' Shooty: +1 to Hit ranged при Waaagh! |
| Gorkanaut | Big an' Stompy: +1 to Hit melee при Waaagh! |
| Stompa | Transport 22, Ghazghkull = 15 мест |

### FAQ

- Waaagh!-зависимые способности работают даже если Waaagh! активирован через правило детачмента (напр. Bully Boyz)
- При уничтожении Bodyguard (Meganobz) Character теряет FNP
- Boss Snikrot: Overwatch НЕ работает при снятии, НО работает при установке (кроме Kommandos)
- Способности не работают внутри транспорта (если не указано иначе)
- [[Wazbom Blastajet]] — летающая крепость
- [[Gargantuan Squiggoth]] — Forge World, монстр-зверь

## Keywords

- **Faction Keywords:** XENOS, ORKS
- **Common Unit Keywords:** INFANTRY, CHARACTER, MOUNTED, BEAST, VEHICLE, MONSTER, WALKER, FLYER, TRANSPORT, DREADNOUGHT, TOWERING, SQUIG, GRETCHIN, NOB, MEGA ARMOUR, BOSS, SNEAKY, SPEED FREEK

## Balance Dataslate v3.4 Updates

> Source: Balance Dataslate v3.4 (2026), p.22

### Army Rule: Waaagh!
- **Change**: First paragraph now reads "once per battle, at the start of your **Command phase**, you can call a Waaagh!" (previously just "at the start of the battle round").

### Detachment Changes

#### Bully Boyz — Da Boss Is Watchin'
- **Change**: In a turn where you have **not** called a Waaagh!, if you have a Warboss model on the battlefield (or embarked), you can call a second Waaagh! this battle. This second Waaagh! only affects **Warboss, Nobz and Meganobz** units.

#### Da Big Hunt — Da Hunt Is On
- **Change**: Now selects a Monster, **Vehicle or Character** as your Prey (previously Monster or Vehicle only).
- **Dat One's Even Bigga!** (Stratagem): Now allows your unit to charge after Advancing or Falling Back, and re-roll charges against your Prey.

#### Green Tide — Mob Mentality
- **Change**: All Boyz units get a **6+ invulnerable save**. Boyz units with 10+ models get a **5+ invulnerable save**.
- **Tide of Muscle** (Stratagem): +1 to charge rolls; re-roll the charge if your unit has 10+ models.
- **Go Get 'Em!** (Stratagem): Your unit makes a D6" move after shooting; if 10+ models, re-roll the distance.

#### Kult of Speed — Adrenaline Junkies
- **Change**: Speed Freeks units can **shoot AND declare a charge** in a turn they Advanced or Fell Back (previously shoot only).

### Datasheet Changes

| Datasheet | Change |
|-----------|--------|
| **Boyz** | 20-model unit can attach **up to 2 Leaders** (one must be a Warboss). |
| **Battlewagon** | Transport capacity: 22 Orks Infantry (12 with killkannon). Mega Armour/Jump Pack = 2 slots. Ghazghkull = 4 slots. |
| **Deff Dread** | Piston-driven Brutality: on 2-5 = D3 MW; on 6 = D3+3 MW to one enemy unit within Engagement Range after a Charge. |
| **Hunta Rig / Kill Rig** | Keyword changed from **Vehicle** to **Monster**. Saw blades: A6, WS3+, S10, AP-2, D2. |
| **Ghazghkull Thraka** | Prophet of da Great Waaagh!: +1 to hit and wound in melee; **critical hits on 5+** if Waaagh! is active. Now leads **Boyz, Meganobz, Nobz**. |
| **Killa Kans** | Shooty Power Trip reworked: 1-2 = D3 MW to self; 3-4 = +1 S; 5-6 = +1 A. |
| **Kommandos** | New **Patrol Squad**: can split into two 5-model units at deployment. |
| **Meganobz** | Krumpin' Time: **Feel No Pain 5+** during the battle round you call a Waaagh!. |
| **Mek Gunz** | Bubblechukka: roll D6 **before selecting targets** to determine profile. |
| **Tankbustas, Breaka Boyz, Kommandos, Squighog Boyz** | Bomb Squigs: **once per battle**, after a Normal move, pick an enemy unit within 12" — on 3+, D3 MW. |
