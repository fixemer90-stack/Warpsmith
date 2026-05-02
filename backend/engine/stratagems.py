"""Stratagem framework for Warhammer 40k battles."""

from dataclasses import dataclass, field
from typing import Callable, Optional, Dict, Any
from ..state.game_state import GameState, UnitState, PlayerState


@dataclass
class Stratagem:
    """A stratagem that can be used during the game."""
    name: str
    cp_cost: int
    phase: str  # "any", "command", "movement", "shooting", "charge", "fight", "morale"
    description: str
    effect_fn: Callable[[GameState, Optional[UnitState], Dict[str, Any]], GameState]
    condition_fn: Optional[Callable[[GameState, Optional[UnitState]], bool]] = None

    def is_available(self, state: GameState, phase: str, target: Optional[UnitState] = None) -> bool:
        """Check if this stratagem is available to use in the given phase."""
        if self.phase not in ("any", phase):
            return False
        if self.condition_fn is not None:
            return self.condition_fn(state, target)
        return True


class StratagemRegistry:
    """Registry for all available stratagems."""
    
    def __init__(self):
        self._stratagems: Dict[str, Stratagem] = {}
    
    def register(self, stratagem: Stratagem) -> None:
        """Register a stratagem."""
        self._stratagems[stratagem.name] = stratagem
    
    def get(self, name: str) -> Optional[Stratagem]:
        """Get a stratagem by name."""
        return self._stratagems.get(name)
    
    def available(self, state: GameState, phase: str) -> list[Stratagem]:
        """List of stratagems available in the given phase (without considering targets)."""
        return [s for s in self._stratagems.values() if s.phase in ("any", phase)]
    
    def execute(self, state: GameState, name: str, target: Optional[UnitState] = None, **kwargs) -> GameState:
        """Execute a stratagem by name."""
        stratagem = self.get(name)
        if stratagem is None:
            raise ValueError(f"Stratagem '{name}' not found")
        
        # Check if the stratagem is available in the current phase
        # Note: We don't have the current phase here, so we assume the caller knows.
        # In practice, the Scenario should check the phase before allowing execution.
        
        # Check CP cost
        # We need to know which player is using the stratagem. 
        # For simplicity, we assume the stratagem is used by the active player? 
        # But the spec doesn't specify. We'll leave CP deduction to the caller for now.
        # Actually, the spec's example does the CP deduction inside the execute method.
        # We'll follow the spec: deduct CP from the active player? But we don't have active_player in GameState?
        # We do have active_player in GameState.
        
        # However, the spec's example uses state.active_roster() which we don't have.
        # We'll change: we'll require the caller to specify which player is using the stratagem?
        # Or we assume the stratagem is used by the player whose turn it is? 
        # Let's look at the spec: 
        #   roster = state.active_roster()
        #   if roster.cp < s.cp_cost:
        #       raise ValueError(f"Not enough CP: need {s.cp_cost}, have {roster.cp}")
        #   roster.cp -= s.cp_cost
        #
        # We don't have active_roster. We have active_player (a player_id) and players dict.
        #
        # We'll adjust: we'll use the active_player from the GameState to determine who is using the stratagem.
        # If there is no active_player, we cannot determine who is using the stratagem.
        #
        # For now, we'll assume that the stratagem is used by the active_player, and we'll deduct CP from that player.
        # If active_player is None, we'll raise an error.
        
        if state.active_player is None:
            raise ValueError("No active player set; cannot determine who is using the stratagem")
        
        player = state.players.get(state.active_player)
        if player is None:
            raise ValueError(f"Active player {state.active_player} not found")
        
        if player.command_points < stratagem.cp_cost:
            raise ValueError(f"Not enough CP: need {stratagem.cp_cost}, have {player.command_points}")
        
        # Deduct CP
        player.command_points -= stratagem.cp_cost
        
        # Execute the effect
        return stratagem.effect_fn(state, target, **kwargs)


# Global stratagem registry
stratagem_registry = StratagemRegistry()


def _init_core_stratagems():
    """Initialize core stratagems (simplified versions)."""
    # Command Re-roll: re-roll any one dice roll.
    # We don't have a dice rolling context here, so we'll leave it as a placeholder.
    def command_re_roll_effect(state: GameState, target: Optional[UnitState], **kwargs) -> GameState:
        # In a real implementation, we would affect the current dice roll.
        # For now, we just log that it was used.
        state.game_log.append("Command Re-roll stratagem used (placeholder)")
        return state
    
    stratagem_registry.register(Stratagem(
        name="Command Re-roll",
        cp_cost=1,
        phase="any",
        description="Re-roll any one dice roll.",
        effect_fn=command_re_roll_effect,
    ))
    
    # Insane Bravery: auto-pass Battle-shock test.
    def insane_bravery_effect(state: GameState, target: Optional[UnitState], **kwargs) -> GameState:
        if target is not None:
            target.is_battle_shocked = False
            state.game_log.append(f"{target.name} uses Insane Bravery to auto-pass Battle-shock")
        else:
            state.game_log.append("Insane Bravery stratagem used (no target)")
        return state
    
    stratagem_registry.register(Stratagem(
        name="Insane Bravery",
        cp_cost=1,
        phase="morale",
        description="Auto-pass Battle-shock test.",
        effect_fn=insane_bravery_effect,
    ))
    
    # Counter-Offensive: fight first in Fight phase after opponent activation.
    # This is complex to implement without a full fight phase activation system.
    # We'll leave it as a placeholder that logs.
    def counter_offensive_effect(state: GameState, target: Optional[UnitState], **kwargs) -> GameState:
        state.game_log.append("Counter-Offensive stratagem used (placeholder)")
        return state
    
    stratagem_registry.register(Stratagem(
        name="Counter-Offensive",
        cp_cost=2,
        phase="fight",
        description="Fight first in Fight phase after opponent activation.",
        effect_fn=counter_offensive_effect,
        # Condition: only usable in Fight phase
        condition_fn=lambda state, target: state.current_phase.value == "fight",
    ))
    
    # Tank Shock: Vehicle charges -> D6 mortal wounds.
    # We don't have vehicle detection, so we'll leave it as a placeholder.
    def tank_shock_effect(state: GameState, target: Optional[UnitState], **kwargs) -> GameState:
        if target is not None:
            state.game_log.append(f"{target.name} uses Tank Shock (placeholder)")
        else:
            state.game_log.append("Tank Shock stratagem used (placeholder)")
        return state
    
    stratagem_registry.register(Stratagem(
        name="Tank Shock",
        cp_cost=1,
        phase="charge",
        description="Vehicle charges -> D6 mortal wounds.",
        effect_fn=tank_shock_effect,
        # Condition: only usable on vehicles (we don't have vehicle detection, so always allow for now)
        condition_fn=lambda state, target: True,
    ))


# Initialize core stratagems on import
_init_core_stratagems()