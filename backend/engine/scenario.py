"""Game loop scenario for Warhammer 40k battles."""

from __future__ import annotations

from typing import Optional

from ..model.unit import Unit
from ..state.game_state import GamePhase, GameState
from ..state.map import BattlefieldMap
from ..state.mission import Mission


class Scenario:
    """Manages the game loop for a Warhammer 40k battle."""

    def __init__(
        self,
        game_state: GameState,
        unit_models: dict[str, Unit] | None = None,
        battlefield: BattlefieldMap | None = None,
    ):
        self.state = game_state
        self.log = []  # Additional scenario-specific log
        self._unit_models = unit_models or {}  # unit_id → full Unit model (for combat engine)
        self.battlefield = battlefield  # for LoS checks

    def run_game(self, max_rounds: int | None = None) -> None:
        """Run the game until completion or max_rounds reached."""
        if max_rounds is not None:
            self.state.max_rounds = max_rounds

        while not self.state.is_game_over:
            self.run_round()

    def run_round(self) -> None:
        """Run a single game round (all phases)."""
        # Log round start
        self.state.game_log.append(f"Starting round {self.state.current_round}")

        # Run through all phases using the game state's phase transition
        # We'll go through all phases and let the game state handle transitions
        phases_completed = 0
        max_phases_per_round = 6  # COMMAND, MOVEMENT, SHOOTING, CHARGE, FIGHT, MORALE

        while phases_completed < max_phases_per_round and not self.state.is_game_over:
            # Execute current phase
            self._execute_phase(self.state.current_phase)
            phases_completed += 1

            # Move to next phase (this handles round advancement)
            if not self.state.is_game_over:
                self.state.next_phase()

    def _execute_phase(self, phase: GamePhase) -> None:
        """Execute logic for a specific phase."""
        self.state.game_log.append(f"Phase: {phase.value}")

        if phase == GamePhase.COMMAND:
            self._command_phase()
        elif phase == GamePhase.MOVEMENT:
            self._movement_phase()
        elif phase == GamePhase.SHOOTING:
            self._shooting_phase()
        elif phase == GamePhase.CHARGE:
            self._charge_phase()
        elif phase == GamePhase.FIGHT:
            self._fight_phase()
        elif phase == GamePhase.MORALE:
            self._morale_phase()

    def _command_phase(self) -> None:
        """Command phase logic: generate CP, check mission objectives, etc."""
        # Generate command points for each player
        for player in self.state.players.values():
            # Base CP generation: 1 CP per turn
            cp_gain = 1
            # Additional CP if player has a warlord
            if player.warlord_unit is not None:
                cp_gain += 1
            # Apply Leviathan cap: max 10 CP per player
            if player.command_points + cp_gain > 10:
                cp_gain = 10 - player.command_points
            player.command_points += cp_gain
            self.state.game_log.append(
                f"{player.name} gained {cp_gain} CP (total: {player.command_points})"
            )

        # Update mission scoring at end of Command phase
        if self.state.mission:
            vp_awarded = self.state.mission.calculate_victory_points()
            for player_id, vp in vp_awarded.items():
                if player_id in self.state.players:
                    self.state.players[player_id].victory_points += vp
                    self.state.game_log.append(
                        f"{self.state.players[player_id].name} gained {vp} VP from mission (total: {self.state.players[player_id].victory_points})"
                    )

    def _movement_phase(self) -> None:
        """Movement phase: normal move / advance / fall back for active player's units."""
        self.state.game_log.append("Movement phase: units may move")
        for player in self.state.players.values():
            for unit in player.units.values():
                if not unit.is_alive or unit.has_moved:
                    continue
                if unit.is_engaged:
                    # Fall Back — move away from engagement
                    # Simplified: move 3 cells away from current position
                    new_x = min(unit.position[0] + 3, self.state.map_width - 1)
                    new_y = unit.position[1]
                    if self.state.move_unit(unit.unit_id, (new_x, new_y)):
                        self.state.game_log.append(f"{unit.name} falls back to ({new_x}, {new_y})")
                else:
                    # Normal Move — simplified: move 1 cell toward center
                    center_x = self.state.map_width // 2
                    dx = (
                        1
                        if unit.position[0] < center_x
                        else (-1 if unit.position[0] > center_x else 0)
                    )
                    new_x = unit.position[0] + dx
                    new_y = unit.position[1]
                    if self.state.move_unit(unit.unit_id, (new_x, new_y)):
                        self.state.game_log.append(f"{unit.name} moves to ({new_x}, {new_y})")
                unit.has_moved = True

    def _shooting_phase(self) -> None:
        """Shooting phase: find targets in range, resolve damage via combat engine."""
        self.state.game_log.append("Shooting phase: units may shoot")
        import numpy as np

        for player in self.state.players.values():
            for unit in player.units.values():
                if not unit.is_alive or unit.has_shot or unit.is_engaged:
                    continue
                # Find opponent
                opponent_pid = next(
                    (pid for pid in self.state.players if pid != player.player_id), None
                )
                if opponent_pid is None:
                    continue
                opponent = self.state.players[opponent_pid]
                targets = []
                for target in opponent.units.values():
                    if not target.is_alive:
                        continue
                    dist = (
                        (unit.position[0] - target.position[0]) ** 2
                        + (unit.position[1] - target.position[1]) ** 2
                    ) ** 0.5
                    if dist > 12:
                        continue
                    # LoS check if battlefield is available
                    if self.battlefield is not None and not self.battlefield.has_los(
                        unit.position[0],
                        unit.position[1],
                        target.position[0],
                        target.position[1],
                    ):
                        continue
                    targets.append(target)
                if not targets:
                    continue
                # Target closest enemy
                target = min(
                    targets,
                    key=lambda t: (
                        (unit.position[0] - t.position[0]) ** 2
                        + (unit.position[1] - t.position[1]) ** 2
                    ),
                )
                # Resolve damage using combat engine if models available
                attacker_model = self._unit_models.get(unit.unit_id)
                defender_model = self._unit_models.get(target.unit_id)
                if attacker_model and defender_model and attacker_model.ranged_weapons:
                    from backend.engine.combat import simulate_unit_attack

                    result = simulate_unit_attack(
                        attacker=attacker_model,
                        defender=defender_model,
                        n_iterations=1000,
                        squad_size=unit.models_remaining,
                        distance=int(dist),
                    )
                    damage = int(result.total_stats.mean)
                    self.state.game_log.append(
                        f"{unit.name} shoots {target.name} — expected {result.total_stats.mean:.1f} dmg"
                    )
                else:
                    # Simplified damage fallback
                    damage = max(1, unit.models_remaining // 2)
                self.state.deal_damage(target.unit_id, damage)
                self.state.game_log.append(f"{unit.name} hits {target.name} for {damage} damage")
                unit.has_shot = True

    def _charge_phase(self) -> None:
        """Charge phase: roll 2D6, move into engagement if in range."""
        self.state.game_log.append("Charge phase: units may charge")
        import random

        for player in self.state.players.values():
            for unit in player.units.values():
                if not unit.is_alive or unit.has_charged or unit.is_engaged:
                    continue
                # Find closest enemy
                opponent_pid = next(
                    (pid for pid in self.state.players if pid != player.player_id), None
                )
                if opponent_pid is None:
                    continue
                opponent = self.state.players[opponent_pid]
                closest = min(
                    (t for t in opponent.units.values() if t.is_alive),
                    key=lambda t: (
                        (unit.position[0] - t.position[0]) ** 2
                        + (unit.position[1] - t.position[1]) ** 2
                    ),
                    default=None,
                )
                if closest is None:
                    continue
                dist = (
                    (unit.position[0] - closest.position[0]) ** 2
                    + (unit.position[1] - closest.position[1]) ** 2
                ) ** 0.5
                # Roll 2D6
                roll = random.randint(1, 6) + random.randint(1, 6)
                if roll >= dist:
                    # Charge succeeds — move into engagement
                    if self.state.move_unit(unit.unit_id, closest.position):
                        unit.is_engaged = True
                        self.state.game_log.append(
                            f'{unit.name} charges {closest.name} (rolled {roll} ≥ {dist:.0f})" – engaged!'
                        )
                else:
                    self.state.game_log.append(
                        f'{unit.name} fails charge (rolled {roll} < {dist:.0f})")'
                    )
                unit.has_charged = True

    def _fight_phase(self) -> None:
        """Fight phase logic: resolve fights with alternating activations."""
        self.state.game_log.append("Fight phase: units may fight")

        # Determine player order for Fight phase: non-priority player goes first
        player_ids = list(self.state.players.keys())
        if len(player_ids) < 2:
            # If only one player, just let them fight
            order = player_ids
        else:
            # Find which player has priority
            priority_player_id = None
            for pid, player in self.state.players.items():
                if player.command_priority:
                    priority_player_id = pid
                    break

            if priority_player_id is None:
                # Fallback: if no priority set, use arbitrary order
                order = player_ids
            else:
                # The non-priority player goes first in Fight phase
                non_priority_player_id = next(
                    pid for pid in player_ids if pid != priority_player_id
                )
                order = [non_priority_player_id, priority_player_id]

        # Continue alternating activations until no more units can fight
        progress = True
        while progress:
            progress = False
            for player_id in order:
                player = self.state.players[player_id]
                # Find an eligible unit for this player: engaged and not yet fought
                eligible_unit = None
                for unit in player.units.values():
                    if unit.is_engaged and not unit.is_fighting and unit.is_alive:
                        eligible_unit = unit
                        break

                if eligible_unit is not None:
                    # Resolve melee combat for this unit
                    self._resolve_melee_combat(eligible_unit)
                    # Mark the unit as having fought
                    eligible_unit.is_fighting = True
                    progress = True
                    self.state.game_log.append(f"{eligible_unit.name} fought in melee")

        # After Fight phase, reset is_fighting flags (though they will be reset again at start of next round)
        for player in self.state.players.values():
            for unit in player.units.values():
                unit.is_fighting = False

    def _resolve_melee_combat(self, attacking_unit) -> None:
        """Resolve melee combat for a unit.
        This is a simplified implementation - in reality this would use the combat engine.
        """
        # Find an enemy unit engaged with this unit
        enemy_unit = None
        for player in self.state.players.values():
            for unit in player.units.values():
                if (
                    unit.is_alive
                    and unit != attacking_unit
                    and unit.position == attacking_unit.position
                ):
                    enemy_unit = unit
                    break
            if enemy_unit:
                break

        if enemy_unit is None:
            # No enemy found to fight with
            return

        # Simple melee resolution: each unit does damage to the other
        # In reality, we would use Weapon skill, attacks, etc. from the combat engine
        # For now, we'll do a simple exchange of damage

        # Attacking unit damages enemy
        damage_to_enemy = 1  # Simplified: 1 damage per attack
        self.state.deal_damage(enemy_unit.unit_id, damage_to_enemy)
        self.state.game_log.append(
            f"{attacking_unit.name} hit {enemy_unit.name} for {damage_to_enemy} damage"
        )

        # Enemy unit damages attacking unit (if still alive)
        if enemy_unit.is_alive:
            damage_to_attacker = 1  # Simplified: 1 damage per attack
            self.state.deal_damage(attacking_unit.unit_id, damage_to_attacker)
            self.state.game_log.append(
                f"{enemy_unit.name} hit {attacking_unit.name} for {damage_to_attacker} damage"
            )

    def _morale_phase(self) -> None:
        """Morale phase logic: check for morale failures (Battle-shock)."""
        self.state.game_log.append("Morale phase: check for battle-shock")
        import random

        for player in self.state.players.values():
            for unit in player.units.values():
                if unit.is_alive and not unit.is_above_half_strength:
                    # Take battle-shock test
                    die1 = random.randint(1, 6)
                    die2 = random.randint(1, 6)
                    roll = die1 + die2

                    # Natural 1 on either die? Actually, spec says:
                    #   Natural 1 on either die = auto-fail
                    #   Natural 6 on both = auto-pass
                    # But the code in the spec uses:
                    #   if roll <= 2:  # snake eyes -> auto-fail
                    #   if roll >= 12:  # boxcars -> auto-pass
                    # We'll follow the code in the spec.
                    if roll == 2:  # snake eyes
                        unit.is_battle_shocked = True
                        self.state.game_log.append(
                            f"{unit.name} rolls {roll} (snake eyes) and fails Battle-shock"
                        )
                    elif roll == 12:  # boxcars
                        unit.is_battle_shocked = False
                        self.state.game_log.append(
                            f"{unit.name} rolls {roll} (boxcars) and passes Battle-shock"
                        )
                    else:
                        # Compare to leadership
                        if roll < unit.leadership:
                            unit.is_battle_shocked = True
                            self.state.game_log.append(
                                f"{unit.name} rolls {roll} < LD {unit.leadership} and fails Battle-shock"
                            )
                        else:
                            unit.is_battle_shocked = False
                            self.state.game_log.append(
                                f"{unit.name} rolls {roll} >= LD {unit.leadership} and passes Battle-shock"
                            )

    def get_state_summary(self) -> dict:
        """Get a summary of the current game state."""
        return self.state.get_game_summary()
