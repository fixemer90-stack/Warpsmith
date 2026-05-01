"""Data models for WH40k units, weapons, and abilities."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Weapon:
    name: str
    range: str  # e.g. "24\"" or "Melee"
    attacks: str  # e.g. "3" or "D6"
    skill: str  # e.g. "4+" for BS or WS
    strength: int
    ap: int  # Armour Penetration (negative value, e.g. -2)
    damage: str  # e.g. "1" or "D3" or "D6+2"
    abilities: list[str] = field(default_factory=list)
    is_ranged: bool = True


@dataclass
class Unit:
    name: str
    faction: str
    category: str  # Character, Battleline, Vehicle, Infantry, etc.
    movement: int  # M — Movement in inches
    toughness: int  # T
    save: int  # SV — Save (e.g. 3 means 3+)
    wounds: int  # W
    leadership: int  # LD (e.g. 6 means 6+)
    objective_control: int  # OC
    ranged_weapons: list[Weapon] = field(default_factory=list)
    melee_weapons: list[Weapon] = field(default_factory=list)
    abilities: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    faction_keywords: list[str] = field(default_factory=list)
    points: int = 0
    model_count: tuple[int, int] = (1, 1)  # (min, max) models per unit
    is_epic_hero: bool = False
    can_be_warlord: bool = False
    is_leader: bool = False
    leader_for: list[str] = field(default_factory=list)
    edition: str = "10e"
