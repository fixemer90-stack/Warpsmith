---
title: Adeptus Mechanicus
slug: adeptus-mechanicus
created: 2026-05-01
updated: 2026-05-02
type: faction
faction_group: imperium
tags: [adeptus-mechanicus, imperium]
sources: [Faction Pack v1.1 (April 2026), https://wahapedia.ru/wh40k10ed/factions/adeptus-mechanicus/]
edition: 10e
status: complete
confidence: high
icon: skitarii
ai:
  weights:
    kill_efficiency: 1.0
    charge_aggression: 0.5
    survival_risk: 0.8
    objective_value: 0.7
    threat_reduction: 0.9
  behaviors:
    - id: protector_imperative
      description: "Protector Imperative — +1 BS, -1 M, приоритет стрельбы"
      trigger:
        phase: any
        round_min: 1
        round_max: 20
        cooldown: 2
      effects:
        weights_override:
          charge_aggression: 0.2
          kill_efficiency: 1.3
    - id: conqueror_imperative
      description: "Conqueror Imperative — +1 WS, +1 advance/charge"
      trigger:
        phase: any
        round_min: 1
        round_max: 20
        cooldown: 2
      effects:
        weights_override:
          charge_aggression: 1.3
          kill_efficiency: 0.8
    - id: canticle_shroudpsalm
      description: "Shroudpsalm — Cover bonus, держаться в террейне"
      trigger:
        phase: movement
        round_min: 1
        round_max: 20
        cooldown: 5
      effects:
        weights_override:
          survival_risk: 1.3
    - id: tech_priest_repair
      description: 'Tech-Priest ремонтирует Vehicle/Monster в радиусе 3"'
      trigger:
        phase: command
        round_min: 1
        round_max: 20
        cooldown: 1
      effects: {}
  target_priority:
    monster: 1.5
    vehicle: 1.3
    character: 1.0
    infantry: 0.8
    battleline: 0.6
  deployment:
    front_line: ["battleline", "infantry"]
    mid_field: ["character", "elite"]
    back_field: ["vehicle", "artillery", "walker"]
    reserve: ["fly", "deep-strike"]

---

# Adeptus Mechanicus

> *"From the Machine God's grace, all blessings flow."*

Фракция Adeptus Mechanicus (AdMech, Механикус) в Warhammer 40,000 10-й редакции — армия техножрецов Марса, использующих продвинутую технологию, кибернетические усовершенствования и армии Скитариев. Игровой стиль основан на переключении между атакующими и оборонительными протоколами Doctrina Imperatives, мощной стрельбе поддержки и синергии между персонажами и отрядами.

## Army Rule: Doctrina Imperatives

В начале каждого раунда выберите один из двух протоколов. Он действует до конца раунда на все отряды с правилом Doctrina Imperatives:

**Protector Imperative (Оборонительный):**
- Стрелковое оружие получает [HEAVY]
- +1 к Ballistic Skill для стрелкового оружия
- Вражеские атаки ближнего боя получают -1 к попаданию, если отряд имеет BATTLELINE или находится в 6" от дружественного BATTLELINE

**Conqueror Imperative (Атакующий):**
- Стрелковое оружие получает [ASSAULT]
- +1 к Weapon Skill для оружия ближнего боя
- Атаки получают +1 к AP, если отряд имеет BATTLELINE или находится в 6" от дружественного BATTLELINE

## Detachments

| Детачмент | Правило | Стиль игры |
|-----------|---------|------------|
| [[Rad-Zone Corps]] | Rad-bombardment — радиационный урон в начале битвы | Осада, контроль зон |
| [[Skitarii Hunter Cohort]] | Stealth Optimisation — -1 к попаданию, редеплой | Скитарий-стрелковый |
| [[Data-Psalm Conclave]] | Benedictions of the Omnissiah — баффы по выбору | Культ Механикус |
| [[Explorator Maniple]] | Acquisition At Any Cost — контроль точек | Механизированный |
| [[Cohort Cybernetica]] | Cyber-Psalm Programming — +2" Move, +1 OC роботам | Роботы Кастелан |
| [[Eradication Cohort]] | Murderous Imperative — переброс 1s (Faction Pack) | Агрессивный |
| [[Haloscreed Battle Clade]] | Noospheric Transference — Halo Override (Faction Pack) | Скоростной |

## Units

### Epic Heroes
- [[Belisarius Cawl]] — верховный техножрец Марса, эпический герой. M8" T8 SV2+ W10, 4++.
- [[Thulia Ghuld]] — Archmagos Terminus. M8" T8 SV2+ W10, 4++.
- [[X-101]] — легендарный сервитор-телохранитель.

### Characters
- [[Tech-Priest Dominus]] — мощный техножрец-командир, 4++, лидер Kataphron.
- [[Tech-Priest Manipulus]] — техножрец-баффер, +1 AP для CULT MECHANICUS.
- [[Tech-Priest Enginseer]] — полевой инженер, ремонт техники, лидер Servitors.
- [[Technoarcheologist]] — мастер древних технологий, блокирует резервы врага.
- [[Cybernetica Datasmith]] — программирует роботов Кастелан.
- [[Skitarii Marshal]] — командир Скитариев.
- [[Sydonian Skatros]] — снайпер-ходин на длинных ногах.

### Battleline
- [[Skitarii Rangers]] — стрелковая пехота Скитариев с гальваническими винтовками.
- [[Skitarii Vanguard]] — штурмовая пехота Скитариев с радиевыми карабинами.
- [[Hastarii Exterminators]] — элитные Скитарии с дуговыми бластерами (Faction Pack).
- [[Hastarii Fusiliers]] — элитные Скитарии с нейтронными фузилами (Faction Pack).

### Infantry
- [[Corpuscarii Electropriests]] — электро-жрецы, штурмовые разряды.
- [[Fulgurite Electro-priests]] — электро-жрецы, вампиризм.
- [[Kataphron Breachers]] — тяжёлая пехота, анти-техника.
- [[Kataphron Destroyers]] — тяжёлая пехота, огневая поддержка.
- [[Pteraxii Skystalkers]] — десантники с реактивными ранцами.
- [[Pteraxii Sterylizors]] — десантники-огнемётчики.
- [[Servitor Battleclade]] — боевые сервиторы (Faction Pack).
- [[Servitors]] — легендарные сервиторы-ретинеры.
- [[Sicarian Infiltrators]] — скрытные убийцы.
- [[Sicarian Ruststalkers]] — убийцы ближнего боя.
- [[Serberys Raiders]] — кавалерия-разведчики.
- [[Serberys Sulphurhounds]] — кавалерия-огнемётчики.

### Vehicles
- [[Ironstrider Ballistarii]] — скоростной шагоход-снайпер.
- [[Kastelan Robots]] — медленные, но мощные боевые роботы.
- [[Onager Dunecrawler]] — тяжёлый шагоход с разным вооружением.
- [[Skorpius Disintegrator]] — боевой танк.
- [[Sydonian Dragoons]] — лёгкие шагоходы-разведчики с тазерными копьями или радиевыми джеззалями.
- [[Archaeopter Fusilave]] — бомбардировщик.
- [[Archaeopter Stratoraptor]] — истребитель.
- [[Archaeopter Transvector]] — транспортный самолёт.

### Dedicated Transports
- [[Skorpius Dunerider]] — транспорт Скитариев.
- [[Terrax-pattern Termite]] — легендарный подземный транспорт.

## Faction Pack v1.1 — Обновления

Источник: `raw/papers/adeptus_mechanicus_faction_pack.txt`

### Новые юниты

| Даташит | Роль | Описание |
|---------|------|----------|
| Thulia Ghuld | Epic Hero | Archmagos Terminus, Supreme Commander |
| Hastarii Exterminators | Battleline | 5 Skitarii, arc blasters |
| Hastarii Fusiliers | Battleline | 5 Skitarii, neutron fusils |
| Servitor Battleclade | Other | 9 сервиторов, лидер для Kataphron |

### Новые детачменты

- **Eradication Cohort** — Murderous Imperative: Skitarii перебрасывают 1s to Hit (Protector) или to Wound (Conqueror)
- **Haloscreed Battle Clade** — Noospheric Transference: 1-3 отряда получают Halo Override + один из 4 баффов (+2" M, +1 T, заряд после Advance, Stealth)

## Keywords

- **Faction Keywords:** IMPERIUM, ADEPTUS MECHANICUS
- **Common Unit Keywords:** INFANTRY, CHARACTER, VEHICLE, MONSTER, BATTLELINE, FLYER, TRANSPORT, DEDICATED TRANSPORT, TOWERING, WALKER, SKITARII, CULT MECHANICUS, TECH-PRIEST, LEGIO CYBERNETICA, KASTELAN ROBOT, SICARIAN, PTERAXII, SERBERYS, KATAPHRON, ELECTRO-PRIEST, CORPUSCARII, FULGURITE, SYDONIAN, IRONSTRIDER, ONAGER, SKORPIUS, ARCHAEOCOPTER

## Balance Dataslate v3.4 Updates

> Source: Balance Dataslate v3.4 (2026), p.5

### Army Rule: Doctrina Imperatives — Revised

**Protector Imperative (new):**
- Ranged weapons gain [HEAVY]
- +1 BS for ranged weapons
- Enemy melee attacks suffer -1 to hit if the unit has BATTLELINE or is within 6" of a friendly BATTLELINE unit.

**Conqueror Imperative (new):**
- Ranged weapons gain [ASSAULT]
- +1 WS for melee weapons
- Attacks gain +1 AP if the unit has BATTLELINE or is within 6" of a friendly BATTLELINE unit.

### Datasheet Changes

| Datasheet | Change |
|-----------|--------|
| **Belisarius Cawl** | M8". Canticles of the Omnissiah. Invocation of Machine Vengeance: re-roll hits. Mantra of Discipline: gains BATTLELINE, +1 OC, +1 to Battle-shock. Shroudpsalm: Stealth aura 6". |
| **Onager Dunecrawler** | Neutron laser: 48", A3, BS4+, S16, AP-4, D6+2. Eradication beamer [BLAST, SUSTAINED HITS 1]. |
| **Ironstrider Ballistarii** | Twin cognis lascannon [SUSTAINED HITS 1, TWIN-LINKED]: 48", A2, BS4+, S12, AP-3, D6+1. |
| **Sicarian Infiltrators** | Taser goad [SUSTAINED HITS 2]: A3, WS4+, S6, AP-1, D1. |
| **Sicarian Ruststalkers** | Transonic blades [DEVASTATING WOUNDS, PRECISION]: A5, S5, AP-1, D1. |
| **Skorpius Disintegrator** | Ferrumite cannon: 48", A3, BS4+, S12, AP-3, D6+1. |

## See Also

- [[Imperium]] — faction group overview
- [[Tech-Priest]] — keyword explanation
- [[Doctrina Imperatives]] — army rule details
- [[Eradication Cohort]] — detachment page
- [[Haloscreed Battle Clade]] — detachment page
