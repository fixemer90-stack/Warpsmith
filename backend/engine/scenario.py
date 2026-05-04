"""Game loop scenario for Warhammer 40k battles."""

from typing import Optional

from ..state.game_state import GamePhase, GameState
from ..state.mission import Mission


class Scenario:
    """Manages the game loop for a Warhammer 40k battle."""

    def __init__(self, game_state: GameState):
        self.state = game_state
        self.log = []  # Additional scenario-specific log

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
        """Movement phase logic: move units."""
        # In a real implementation, we would allow players to move their units
        # For now, we'll just log that movement phase occurred
        self.state.game_log.append("Movement phase: units may move")
        # Reset has_moved flags at start of phase? Actually, they are reset at start of round in next_phase
        # But we might want to prevent moving twice in a phase - we'll rely on the has_moved flag
        # For now, no automatic movement - players would decide via UI/API

    def _shooting_phase(self) -> None:
        """Shooting phase logic: resolve shooting attacks."""
        self.state.game_log.append("Shooting phase: units may shoot")
        # In a full implementation, we would iterate over units that can shoot and haven't shot yet
        # For each unit, resolve shooting attacks using the combat engine
        # We'll leave the actual shooting logic to be implemented based on player input
        # For now, we just note that shooting happened
        # Example of how it might work:
        # for player in self.state.players.values():
        #     for unit in player.units.values():
        #         if unit.is_alive and not unit.has_shot:
        #             # Resolve shooting for this unit
        #             # ... combat logic ...
        #             unit.has_shot = True

    def _charge_phase(self) -> None:
        """Charge phase logic: resolve charge moves."""
        self.state.game_log.append("Charge phase: units may charge")
        # Similar to shooting, but for charges

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
                non_priority_player_id = [pid for pid in player_ids if pid != priority_player_id][0]
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
                if unit.is_alive and unit != attacking_unit:
                    # Simplified engagement check - same position or adjacent
                    # In a real implementation, we'd use proper engagement rules
                    if unit.position == attacking_unit.position:
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
