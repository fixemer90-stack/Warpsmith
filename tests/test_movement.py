"""Regression tests for Task 5.1 — charge destination and engagement identity."""

import pytest

from backend.engine.scenario import Scenario
from backend.state.game_state import (
    GameState,
    PlayerState,
    UnitState,
    create_empty_game,
)


def test_charge_never_occupies_enemy_cell() -> None:
    """Charge destination must never be the enemy unit's position."""
    game = create_empty_game("charge-test")
    game.map_width = 6
    game.map_height = 4

    p1 = PlayerState("p1", "P1", "orks")
    p2 = PlayerState("p2", "P2", "marines")
    game.players = {"p1": p1, "p2": p2}

    # Charger at (0, 2), enemy at (2, 2) — same Y, 2 cells apart
    charger = UnitState(
        unit_id="p1:Boyz:0",
        name="Boyz",
        faction="orks",
        position=(0, 2),
        current_wounds=4,
        max_wounds=4,
        models_remaining=1,
        models_total=1,
        leadership=6,
        objective_control=1,
    )
    enemy = UnitState(
        unit_id="p2:Tactical Squad:0",
        name="Tactical Squad",
        faction="marines",
        position=(2, 2),
        current_wounds=4,
        max_wounds=4,
        models_remaining=1,
        models_total=1,
        leadership=6,
        objective_control=1,
    )

    p1.units = {"p1:Boyz:0": charger}
    p2.units = {"p2:Tactical Squad:0": enemy}

    scenario = Scenario(game)

    # Run charge phase repeatedly with a fixed seed until we observe
    # successful charges — then verify position is never the enemy's cell.
    import random

    random.seed(42)
    charge_succeeded = False
    for _ in range(50):
        charger.has_charged = False
        charger.is_engaged = False
        charger.position = (0, 2)  # reset
        scenario._charge_phase()
        if charger.is_engaged:
            charge_succeeded = True
            # Charger must NOT occupy the enemy's cell
            assert charger.position != enemy.position, (
                f"Charger illegally occupies enemy cell at {enemy.position}"
            )
            # Charger must be adjacent (within 1 cell)
            assert abs(charger.position[0] - enemy.position[0]) <= 1
            assert abs(charger.position[1] - enemy.position[1]) <= 1
    assert charge_succeeded, "No successful charge observed after 50 attempts"


def test_charge_adjacent_cell_when_primary_occupied() -> None:
    """When the preferred adjacent cell is occupied, charge finds another."""
    game = create_empty_game("charge-occ-test")
    game.map_width = 6
    game.map_height = 4

    p1 = PlayerState("p1", "P1", "orks")
    p2 = PlayerState("p2", "P2", "marines")
    game.players = {"p1": p1, "p2": p2}

    # Charger at (0, 2), enemy at (2, 2)
    charger = UnitState(
        unit_id="p1:Boyz:0",
        name="Boyz",
        faction="orks",
        position=(0, 2),
        current_wounds=4,
        max_wounds=4,
        models_remaining=1,
        models_total=1,
        leadership=6,
        objective_control=1,
    )
    enemy = UnitState(
        unit_id="p2:Tactical Squad:0",
        name="Tactical Squad",
        faction="marines",
        position=(2, 2),
        current_wounds=4,
        max_wounds=4,
        models_remaining=1,
        models_total=1,
        leadership=6,
        objective_control=1,
    )
    # Occupier sits at (1, 2) — the closest adjacent cell to enemy from charger's side
    occupier = UnitState(
        unit_id="p2:Scout:0",
        name="Scout",
        faction="marines",
        position=(1, 2),
        current_wounds=4,
        max_wounds=4,
        models_remaining=1,
        models_total=1,
        leadership=6,
        objective_control=1,
    )

    p1.units = {"p1:Boyz:0": charger}
    p2.units = {"p2:Tactical Squad:0": enemy, "p2:Scout:0": occupier}

    scenario = Scenario(game)

    import random

    random.seed(42)
    charge_succeeded = False
    for _ in range(50):
        charger.has_charged = False
        charger.is_engaged = False
        charger.position = (0, 2)
        scenario._charge_phase()
        if charger.is_engaged:
            charge_succeeded = True
            # Must not occupy any other unit's cell
            assert not (
                charger.position == enemy.position or charger.position == occupier.position
            ), f"Charger occupies occupied cell at {charger.position}"
            assert abs(charger.position[0] - enemy.position[0]) <= 1
            assert abs(charger.position[1] - enemy.position[1]) <= 1
    assert charge_succeeded, "No successful charge to alternate cell observed"


def test_charge_same_x_different_y_finds_adjacent() -> None:
    """When charger and enemy share X coordinate, charge finds a valid Y-adjacent cell."""
    game = create_empty_game("charge-samex-test")
    game.map_width = 6
    game.map_height = 4

    p1 = PlayerState("p1", "P1", "orks")
    p2 = PlayerState("p2", "P2", "marines")
    game.players = {"p1": p1, "p2": p2}

    # Same X (3), different Y — old code would land on enemy's cell
    charger = UnitState(
        unit_id="p1:Boyz:0",
        name="Boyz",
        faction="orks",
        position=(3, 0),
        current_wounds=4,
        max_wounds=4,
        models_remaining=1,
        models_total=1,
        leadership=6,
        objective_control=1,
    )
    enemy = UnitState(
        unit_id="p2:Tactical Squad:0",
        name="Tactical Squad",
        faction="marines",
        position=(3, 2),
        current_wounds=4,
        max_wounds=4,
        models_remaining=1,
        models_total=1,
        leadership=6,
        objective_control=1,
    )

    p1.units = {"p1:Boyz:0": charger}
    p2.units = {"p2:Tactical Squad:0": enemy}

    scenario = Scenario(game)

    import random

    random.seed(42)
    charge_succeeded = False
    for _ in range(50):
        charger.has_charged = False
        charger.is_engaged = False
        charger.position = (3, 0)
        scenario._charge_phase()
        if charger.is_engaged:
            charge_succeeded = True
            assert charger.position != enemy.position, (
                f"Charger occupies enemy cell: same X={enemy.position[0]}"
            )
            assert abs(charger.position[0] - enemy.position[0]) <= 1
            assert abs(charger.position[1] - enemy.position[1]) <= 1
    assert charge_succeeded, "No successful charge in same-X scenario"


def test_melee_targets_opponent_only() -> None:
    """_resolve_melee_combat only targets opponent units, not friendly."""
    game = create_empty_game("melee-test")
    game.map_width = 6
    game.map_height = 4

    p1 = PlayerState("p1", "P1", "orks")
    p2 = PlayerState("p2", "P2", "marines")
    game.players = {"p1": p1, "p2": p2}

    # Attacker at (1, 1), adjacent to own friendly at (1, 2) and enemy at (2, 1)
    attacker = UnitState(
        unit_id="p1:Boyz:0",
        name="Boyz",
        faction="orks",
        position=(1, 1),
        current_wounds=4,
        max_wounds=4,
        models_remaining=1,
        models_total=1,
        leadership=6,
        objective_control=1,
    )
    friendly = UnitState(
        unit_id="p1:Gretchin:0",
        name="Gretchin",
        faction="orks",
        position=(1, 2),
        current_wounds=4,
        max_wounds=4,
        models_remaining=1,
        models_total=1,
        leadership=4,
        objective_control=1,
    )
    enemy = UnitState(
        unit_id="p2:Tactical Squad:0",
        name="Tactical Squad",
        faction="marines",
        position=(2, 1),
        current_wounds=10,
        max_wounds=10,
        models_remaining=1,
        models_total=1,
        leadership=6,
        objective_control=1,
    )

    p1.units = {"p1:Boyz:0": attacker, "p1:Gretchin:0": friendly}
    p2.units = {"p2:Tactical Squad:0": enemy}

    scenario = Scenario(game)
    scenario._resolve_melee_combat(attacker)

    # Enemy should have taken damage (from melee exchange)
    assert enemy.current_wounds < enemy.max_wounds, (
        "Enemy unit should have taken damage from melee combat"
    )
    # Friendly should NOT have taken damage
    assert friendly.current_wounds == friendly.max_wounds, (
        "Friendly unit should NOT have been targeted in melee"
    )


def test_same_name_mirrored_units_engage() -> None:
    """Same-name units on opposite sides engage independently via runtime IDs."""
    game = create_empty_game("mirror-test")
    game.map_width = 6
    game.map_height = 4

    p1 = PlayerState("p1", "P1", "orks")
    p2 = PlayerState("p2", "P2", "orks")
    game.players = {"p1": p1, "p2": p2}

    # Two Boyz units with same display name on opposite sides
    p1_boyz = UnitState(
        unit_id="p1:Boyz:0",
        name="Boyz",
        faction="orks",
        position=(1, 1),
        current_wounds=4,
        max_wounds=4,
        models_remaining=1,
        models_total=1,
        leadership=6,
        objective_control=1,
    )
    p2_boyz = UnitState(
        unit_id="p2:Boyz:0",
        name="Boyz",
        faction="orks",
        position=(2, 1),
        current_wounds=4,
        max_wounds=4,
        models_remaining=1,
        models_total=1,
        leadership=6,
        objective_control=1,
    )

    p1.units = {"p1:Boyz:0": p1_boyz}
    p2.units = {"p2:Boyz:0": p2_boyz}

    scenario = Scenario(game)

    import random

    random.seed(42)

    charge_succeeded = False
    for _ in range(50):
        p1_boyz.has_charged = False
        p1_boyz.is_engaged = False
        p1_boyz.position = (1, 1)
        scenario._charge_phase()
        if p1_boyz.is_engaged:
            charge_succeeded = True
            assert p1_boyz.position != p2_boyz.position, (
                "Charger illegally occupies enemy Boyz cell"
            )
            # Engagement is on p1:Boyz:0 → p2:Boyz:0, not just "Boyz vs Boyz"
            assert abs(p1_boyz.position[0] - p2_boyz.position[0]) <= 1
            assert abs(p1_boyz.position[1] - p2_boyz.position[1]) <= 1
    assert charge_succeeded, "Same-name mirrored units could not charge each other"


def test_charge_log_contains_runtime_ids() -> None:
    """Charge log entries MUST include runtime unit IDs, not rely on display names."""
    game = create_empty_game("log-test")
    game.map_width = 6
    game.map_height = 4

    p1 = PlayerState("p1", "P1", "orks")
    p2 = PlayerState("p2", "P2", "marines")
    game.players = {"p1": p1, "p2": p2}

    charger = UnitState(
        unit_id="p1:Nobz:0",
        name="Nobz",
        faction="orks",
        position=(0, 2),
        current_wounds=4,
        max_wounds=4,
        models_remaining=1,
        models_total=1,
        leadership=6,
        objective_control=1,
    )
    enemy = UnitState(
        unit_id="p2:Intercessor Squad:0",
        name="Intercessor Squad",
        faction="marines",
        position=(2, 2),
        current_wounds=4,
        max_wounds=4,
        models_remaining=1,
        models_total=1,
        leadership=6,
        objective_control=1,
    )

    p1.units = {"p1:Nobz:0": charger}
    p2.units = {"p2:Intercessor Squad:0": enemy}

    scenario = Scenario(game)

    import random

    random.seed(42)
    charge_logged = False
    for _ in range(50):
        charger.has_charged = False
        charger.is_engaged = False
        charger.position = (0, 2)
        scenario._charge_phase()
        # Find any charge logs
        charge_entries = [e for e in game.game_log if "charge" in e.lower() and "Nobz" in e]
        for entry in charge_entries:
            charge_logged = True
            # Must contain the runtime unit ID
            assert "p1:Nobz:0" in entry, f"Charge log missing charger runtime ID: {entry}"
            assert "p2:Intercessor Squad:0" in entry, (
                f"Charge log missing target runtime ID: {entry}"
            )
    assert charge_logged, "No charge log entries found"


def test_melee_resolves_adjacent_targets() -> None:
    """Melee combat resolves between adjacent engaged units."""
    game = create_empty_game("melee-adj-test")
    game.map_width = 6
    game.map_height = 4

    p1 = PlayerState("p1", "P1", "orks")
    p2 = PlayerState("p2", "P2", "marines")
    game.players = {"p1": p1, "p2": p2}

    attacker = UnitState(
        unit_id="p1:Boyz:0",
        name="Boyz",
        faction="orks",
        position=(1, 1),
        current_wounds=10,
        max_wounds=10,
        models_remaining=1,
        models_total=1,
        leadership=6,
        objective_control=1,
    )
    enemy = UnitState(
        unit_id="p2:Tactical Squad:0",
        name="Tactical Squad",
        faction="marines",
        position=(2, 1),
        current_wounds=10,
        max_wounds=10,
        models_remaining=1,
        models_total=1,
        leadership=6,
        objective_control=1,
    )

    p1.units = {"p1:Boyz:0": attacker}
    p2.units = {"p2:Tactical Squad:0": enemy}

    scenario = Scenario(game)
    initial_enemy_wounds = enemy.current_wounds

    # Direct call to melee combat
    scenario._resolve_melee_combat(attacker)

    # Enemy should have taken damage (melee resolved)
    assert enemy.current_wounds < initial_enemy_wounds, (
        f"Enemy took no damage from melee: {enemy.current_wounds} == {initial_enemy_wounds}"
    )

    # In the simplified fallback path (no unit models), attacker may also take
    # counter-damage. When unit models exist, it uses the combat engine.
    # Only assert attacker is still alive (not killed by counter).
    assert attacker.is_alive, "Attacker should survive melee exchange"


def test_melee_damage_log_format() -> None:
    """Melee damage log uses 'hits ... for ... damage' format with runtime IDs."""
    game = create_empty_game("melee-log-test")
    game.map_width = 6
    game.map_height = 4

    p1 = PlayerState("p1", "P1", "orks")
    p2 = PlayerState("p2", "P2", "marines")
    game.players = {"p1": p1, "p2": p2}

    attacker = UnitState(
        unit_id="p1:Nobz:0",
        name="Nobz",
        faction="orks",
        position=(1, 1),
        current_wounds=10,
        max_wounds=10,
        models_remaining=1,
        models_total=1,
        leadership=6,
        objective_control=1,
    )
    enemy = UnitState(
        unit_id="p2:Assault Intercessors:0",
        name="Assault Intercessors",
        faction="marines",
        position=(2, 1),
        current_wounds=10,
        max_wounds=10,
        models_remaining=1,
        models_total=1,
        leadership=6,
        objective_control=1,
    )

    p1.units = {"p1:Nobz:0": attacker}
    p2.units = {"p2:Assault Intercessors:0": enemy}

    scenario = Scenario(game)
    initial_log_len = len(game.game_log)
    scenario._resolve_melee_combat(attacker)

    # Find melee damage log entries (not charge logs)
    melee_logs = [e for e in game.game_log[initial_log_len:] if "hits" in e and "damage" in e]
    assert len(melee_logs) >= 1, (
        f"No melee damage log found; logs: {game.game_log[initial_log_len:]}"
    )

    for entry in melee_logs:
        # Must use "hits ... for ... damage" pattern
        assert "hits" in entry and "for" in entry and "damage" in entry, (
            f"Log missing 'hits ... for ... damage' pattern: {entry}"
        )
        # Must carry runtime unit IDs via identity tags
        assert "p1:Nobz:0" in entry or "p2:Assault Intercessors:0" in entry, (
            f"Log missing runtime ID: {entry}"
        )


def test_melee_attribution_not_name_based() -> None:
    """Melee combat attribution uses runtime unit IDs, not display names as keys."""
    game = create_empty_game("melee-attrib-test")
    game.map_width = 6
    game.map_height = 4

    p1 = PlayerState("p1", "P1", "orks")
    p2 = PlayerState("p2", "P2", "orks")
    game.players = {"p1": p1, "p2": p2}

    # Two units with SAME display name on opposite sides
    attacker = UnitState(
        unit_id="p1:Boyz:0",
        name="Boyz",
        faction="orks",
        position=(1, 1),
        current_wounds=10,
        max_wounds=10,
        models_remaining=1,
        models_total=1,
        leadership=6,
        objective_control=1,
    )
    enemy = UnitState(
        unit_id="p2:Boyz:0",
        name="Boyz",
        faction="orks",
        position=(2, 1),
        current_wounds=10,
        max_wounds=10,
        models_remaining=1,
        models_total=1,
        leadership=6,
        objective_control=1,
    )

    p1.units = {"p1:Boyz:0": attacker}
    p2.units = {"p2:Boyz:0": enemy}

    scenario = Scenario(game)
    initial_log_len = len(game.game_log)
    scenario._resolve_melee_combat(attacker)

    melee_logs = [e for e in game.game_log[initial_log_len:] if "hits" in e and "damage" in e]
    assert len(melee_logs) >= 1, "No melee damage log"

    for entry in melee_logs:
        # Runtime IDs disambiguate same-named units
        assert "actor_id=p1:Boyz:0" in entry or "target_id=p2:Boyz:0" in entry, (
            f"Log missing disambiguating runtime ID for same-named units: {entry}"
        )


if __name__ == "__main__":
    pytest.main([__file__])
