"""Game loop scenario for Warhammer 40k battles."""

from typing import Optional
from ..state.game_state import GameState, GamePhase
from ..state.mission import Mission


class Scenario:
    """Manages the game loop for a Warhammer 40k battle."""
    
    def __init__(self, game_state: GameState):
        self.state = game_state
        self.log = []  # Additional scenario-specific log
    
    def run_game(self, max_rounds: Optional[int] = None) -> None:
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
            # Simplified: each player gets 1 CP per turn (can be modified by abilities, etc.)
            player.command_points += 1
            self.state.game_log.append(f"{player.name} gained 1 CP (total: {player.command_points})")
        
        # Update mission scoring at end of Command phase
        if self.state.mission:
            vp_awarded = self.state.mission.calculate_victory_points()
            for player_id, vp in vp_awarded.items():
                if player_id in self.state.players:
                    self.state.players[player_id].victory_points += vp
                    self.state.game_log.append(f"{self.state.players[player_id].name} gained {vp} VP from mission (total: {self.state.players[player_id].victory_points})")
    
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
        """Fight phase logic: resolve fights."""
        self.state.game_log.append("Fight phase: units may fight")
        # Resolve melee combat
    
    def _morale_phase(self) -> None:
        """Morale phase logic: check for morale failures."""
        self.state.game_log.append("Morale phase: check for battle-shock")
        # Check for units that need to take morale tests
    
    def get_state_summary(self) -> dict:
        """Get a summary of the current game state."""
        return self.state.get_game_summary()