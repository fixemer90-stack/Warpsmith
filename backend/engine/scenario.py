"""Game loop scenario for Warhammer 40k battles."""

from __future__ import annotations

import contextlib
from typing import Optional

from ..model.unit import Unit
from ..state.game_state import GAME_PHASE_ORDER, GamePhase, GameState
from ..state.map import BattlefieldMap
from ..state.mission import Mission, VPTracker, apply_scoring, check_end_game
from ..state.runtime_id import format_event_identity


class Scenario:
    """Manages the game loop for a Warhammer 40k battle."""

    def __init__(
        self,
        game_state: GameState,
        unit_models: dict[str, Unit] | None = None,
        battlefield: BattlefieldMap | None = None,
        faction_ai_profiles: dict[str, object] | None = None,
    ):
        self.state = game_state
        self.log = []  # Additional scenario-specific log
        self._unit_models = unit_models or {}  # unit_id → full Unit model (for combat engine)
        self.battlefield = battlefield  # for LoS checks
        self.vp_tracker = VPTracker()  # Per-round VP history (F2.8)
        self._faction_profiles = faction_ai_profiles or {}  # faction_id → FactionAIProfile
        self._active_faction_weights: dict[str, dict] = {}  # player_id → active weights per round

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

        # Run through all phases using the shared canonical phase order.
        phases_completed = 0
        phases_per_round = len(GAME_PHASE_ORDER)

        while phases_completed < phases_per_round and not self.state.is_game_over:
            self._execute_phase(self.state.current_phase)
            phases_completed += 1

            # Move to next phase (this handles round advancement)
            if not self.state.is_game_over:
                self.state.next_phase()

        # Check end-game conditions after all phases
        if self.state.mission:
            result = check_end_game(
                self.state, self.state.mission, self.vp_tracker, self.state.current_round
            )
            if result is not None:
                self.state.game_log.append(
                    f"Game over! Winner: {result.winner}, reason: {result.reason}"
                )
                # Override is_game_over if VP tracker says game should end
                # (is_game_over already handles this via VP≥10 or round check)

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

    def _command_phase(self) -> None:
        """Command phase logic: generate CP, check mission objectives, etc."""
        # Clear battle-shock from previous round (per 10ed: effects end at start of Command phase)
        for player in self.state.players.values():
            for unit in player.units.values():
                unit.is_battle_shocked = False

        # Clear engagement for units no longer within 1" of any enemy
        for player in self.state.players.values():
            opponent_pid = next(
                (pid for pid in self.state.players if pid != player.player_id), None
            )
            if opponent_pid is None:
                continue
            opponent = self.state.players[opponent_pid]
            for unit in player.units.values():
                if not unit.is_engaged:
                    continue
                still_engaged = any(
                    (unit.position[0] - e.position[0]) ** 2
                    + (unit.position[1] - e.position[1]) ** 2
                    <= 1.5
                    for e in opponent.units.values()
                    if e.is_alive
                )
                if not still_engaged:
                    unit.is_engaged = False

        # Generate command points for each player (10ed: 1 CP per Command Phase, no warlord bonus)
        for player in self.state.players.values():
            cp_gain = 1
            # Apply cap: max 10 CP per player
            if player.command_points + cp_gain > 10:
                cp_gain = 10 - player.command_points
            player.command_points += cp_gain
            self.state.game_log.append(
                f"{player.name} gained {cp_gain} CP (total: {player.command_points})"
            )

            # Update mission scoring at end of Command phase
        if self.state.mission:
            apply_scoring(self.state, self.state.mission, self.vp_tracker)

        # Battle-shock tests (10ed: tested during Command phase for units below half-strength)
        self._battle_shock_tests()

        # Activate faction AI behaviors for this round
        for player_id, profile in self._faction_profiles.items():
            if player_id in ("1", "2"):
                with contextlib.suppress(Exception):
                    from backend.engine.ai.faction_ai import get_weights

                    weights = get_weights(profile, GamePhase.COMMAND, self.state.current_round)
                    self._active_faction_weights[player_id] = weights
            # Also update PlayerState.victory_points for backwards compat
            for i, player_id in enumerate(self.state.players):
                pn = i + 1  # 1-indexed
                vp_gained = self.vp_tracker.round_vp(pn, self.state.current_round)
                if vp_gained:
                    player = self.state.players[player_id]
                    player.victory_points += vp_gained
                    self.state.game_log.append(
                        f"{player.name} gained {vp_gained} VP (total: {player.victory_points})"
                    )

    def _movement_phase(self) -> None:
        """Movement phase: Normal Move / Advance / Fall Back / Remain Stationary.

        Per 10ed rules (wiki/rules/10th/Movement Phase.md):
          - Normal Move: up to M\" toward target; can shoot & charge.
          - Advance: Normal Move + D6; cannot shoot or charge.
          - Fall Back: if engaged, retreat toward deployment zone; cannot shoot or charge.
          - Remain Stationary: hold position; can shoot/charge normally.

        AI prioritisation: units distribute across all 3 objectives evenly.
        Unassigned units move toward nearest enemy.
        """
        import random

        self.state.game_log.append("Movement phase: units may move")

        for player in self.state.players.values():
            # ── Objective distribution ──
            # Collect objectives and alive units for this player
            mission = self.state.mission
            objectives = []
            if mission and mission.config.objectives:
                objectives = [(obj.x, obj.y) for obj in mission.config.objectives]

            alive_units = [u for u in player.units.values() if u.is_alive and not u.has_moved]

            # Assign each unit to a target (objective or enemy)
            unit_targets: dict[str, tuple[int, int] | None] = {}
            assigned_objs = set()

            if objectives:
                # For each objective, assign the closest unit
                # Melee units skip objectives if faction prefers aggression
                obj_remaining = list(range(len(objectives)))
                assigned_units = set()

                # Check faction preference: aggressive (Orks) → melee hunts enemies
                profile = self._faction_profiles.get(player.faction)
                is_aggressive = (
                    profile is not None and profile.weights.get("charge_aggression", 1.0) > 1.0
                )

                for _ in range(len(alive_units)):
                    best_unit = None
                    best_obj = None
                    best_dist = float("inf")

                    for unit in alive_units:
                        if unit.unit_id in assigned_units:
                            continue
                        # Aggressive factions: melee units skip objectives → hunt enemies
                        if is_aggressive:
                            model = self._unit_models.get(unit.unit_id)
                            if model and self._is_melee_focused(unit, model):
                                continue
                        for oi in obj_remaining:
                            ox, oy = objectives[oi]
                            d = (unit.position[0] - ox) ** 2 + (unit.position[1] - oy) ** 2
                            if d < best_dist:
                                best_dist = d
                                best_unit = unit
                                best_obj = oi

                    if best_unit is not None and best_obj is not None:
                        unit_targets[best_unit.unit_id] = objectives[best_obj]
                        assigned_units.add(best_unit.unit_id)
                        assigned_objs.add(best_obj)
                        obj_remaining.remove(best_obj)
                    else:
                        break

            # Remaining unassigned units → nearest enemy (always, even without objectives)
            for unit in alive_units:
                if unit.unit_id not in unit_targets:
                    enemy = self._find_closest_enemy(unit, player.player_id)
                    if enemy:
                        unit_targets[unit.unit_id] = enemy.position
                    else:
                        unit_targets[unit.unit_id] = (
                            self.state.map_width // 2,
                            self.state.map_height // 2,
                        )

            # ── Execute movement ──
            for unit in alive_units:
                if not unit.is_alive or unit.has_moved:
                    continue

                model = self._unit_models.get(unit.unit_id)
                move_stat = max(1, model.movement) if model else 6

                # Determine action
                target = unit_targets.get(unit.unit_id)
                action = self._pick_movement_action(unit, target, move_stat, player.player_id)

                if action == "remain_stationary":
                    self.state.game_log.append(f"{unit.name} remains stationary")
                    unit.has_moved = True
                    continue

                if action == "fall_back":
                    self._fall_back(unit, player.player_id, move_stat)
                    continue

                # Normal Move or Advance
                move_cells = move_stat
                if action == "advance":
                    d6 = random.randint(1, 6)
                    move_cells += d6
                    self.state.game_log.append(f'{unit.name} Advances (M+{d6}={move_cells}")')

                self._move_toward(unit, target, move_cells, player.player_id)

                if action == "advance":
                    unit.has_advanced = True

            # Mark all alive units as moved (even those that couldn't move)
            for unit in alive_units:
                unit.has_moved = True

    # ── Movement helpers ──

    def _find_closest_enemy(self, unit, own_player_id: str):
        """Return closest alive enemy unit or None."""
        closest = None
        closest_dist = float("inf")
        for op in self.state.players.values():
            if op.player_id == own_player_id:
                continue
            for eu in op.units.values():
                if eu.is_alive:
                    d = (unit.position[0] - eu.position[0]) ** 2 + (
                        unit.position[1] - eu.position[1]
                    ) ** 2
                    if d < closest_dist:
                        closest_dist = d
                        closest = eu
        return closest

    def _distance(self, a: tuple[int, int], b: tuple[int, int]) -> float:
        return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5

    def _enemy_distance(self, pos: tuple[int, int], own_player_id: str) -> float:
        """Distance to nearest enemy unit from position."""
        best = float("inf")
        for op in self.state.players.values():
            if op.player_id == own_player_id:
                continue
            for eu in op.units.values():
                if eu.is_alive:
                    d = self._distance(pos, eu.position)
                    if d < best:
                        best = d
        return best

    def _pick_movement_action(self, unit, target, move_stat: int, own_player_id: str) -> str:
        """Pick MovementAction for AI unit based on context.

        Rules (10ed):
          - Engaged units MUST Fall Back or Remain Stationary.
          - Units on objective may Remain Stationary to hold it.
          - Far from target → bias toward Advance (ranged) or Normal Move (melee).
          - Close to target → Normal Move or Remain Stationary.
          - Melee units NEVER Advance (must preserve ability to charge).
        """
        import random

        # Mandatory: engaged units must fall back
        if unit.is_engaged:
            return "fall_back"

        # Already on target → hold position
        if target and unit.position == target:
            return random.choice(["remain_stationary", "normal_move"])

        # Determine if unit is melee-focused
        model = self._unit_models.get(unit.unit_id)
        is_melee = self._is_melee_focused(unit, model)

        # Distance-based weighting
        dist_to_target = self._distance(unit.position, target) if target else float("inf")

        if dist_to_target > move_stat:
            if is_melee:
                # Melee units: Normal Move (80%), Remain Stationary (20%) — never Advance
                return random.choices(
                    ["normal_move", "remain_stationary"],
                    weights=[80, 20],
                    k=1,
                )[0]
            # Ranged units: Advance (60%) or Normal Move (40%)
            return random.choices(["advance", "normal_move"], weights=[60, 40], k=1)[0]
        else:
            # Close to target
            if is_melee:
                # Melee: Normal Move (80%), Remain Stationary (20%) — prefer positioning for charge
                return random.choices(
                    ["normal_move", "remain_stationary"],
                    weights=[80, 20],
                    k=1,
                )[0]
            # Ranged: Normal Move (70%), Remain Stationary (20%), Advance (10%)
            return random.choices(
                ["normal_move", "remain_stationary", "advance"],
                weights=[70, 20, 10],
                k=1,
            )[0]

    def _is_melee_focused(self, unit, model) -> bool:
        """Check if unit is primarily a melee combatant."""
        if model is None:
            return False
        # No ranged weapons → definitely melee
        if not model.ranged_weapons:
            return True
        # More melee attacks than ranged → melee-focused
        if model.melee_weapons:
            melee_atks = sum(w.attacks_dice[0] for w in model.melee_weapons)
            ranged_atks = sum(w.attacks_dice[0] for w in model.ranged_weapons)
            return melee_atks > ranged_atks
        return False

    def _move_toward(
        self, unit, target: tuple[int, int] | None, move_cells: int, own_player_id: str
    ) -> None:
        """Move unit toward target, up to move_cells cells.

        Stops 1 cell before any enemy (cannot enter Engagement Range).
        """
        if target is None or move_cells <= 0:
            unit.has_moved = True
            return

        # Direction vector
        dx = target[0] - unit.position[0]
        dy = target[1] - unit.position[1]
        dist = (dx**2 + dy**2) ** 0.5

        if dist <= 0:
            # Already at target
            self.state.game_log.append(f"{unit.name} is already at target {target}")
            unit.has_moved = True
            return

        # Normalise
        dir_x = dx / dist
        dir_y = dy / dist

        # Best position: as close to target as possible while staying 1 cell from enemies
        best_x, best_y = unit.position
        best_score = 0.0  # progress toward target

        for step in range(1, move_cells + 1):
            cx = round(unit.position[0] + dir_x * step)
            cy = round(unit.position[1] + dir_y * step)

            # Bounds check
            if not (0 <= cx < self.state.map_width and 0 <= cy < self.state.map_height):
                break

            # Engagement Range check: stay ≥ 1 cell from any enemy
            # (charge phase will move to adjacent cell to engage)
            if self._enemy_distance((cx, cy), own_player_id) < 1.0:
                break

            # Occupied check
            if self.state.get_unit_at_position(cx, cy) is not None:
                break

            # Progress toward target
            new_dist = ((cx - target[0]) ** 2 + (cy - target[1]) ** 2) ** 0.5
            score = dist - new_dist  # positive = getting closer

            if score > best_score:
                best_score = score
                best_x, best_y = cx, cy

        if (best_x, best_y) != unit.position:
            # Directly update position (move_unit checks validation again)
            if self.state.move_unit(unit.unit_id, (best_x, best_y)):
                # move_unit logs, but we add context
                pass
            else:
                self.state.game_log.append(f"{unit.name} could not move to ({best_x}, {best_y})")
        else:
            self.state.game_log.append(f"{unit.name} found no valid path toward {target}")

    def _fall_back(self, unit, own_player_id: str, move_stat: int) -> None:
        """Fall Back: retreat toward own deployment zone, away from enaging enemy.

        Per 10ed: Normal Move away. Cannot shoot or charge this turn.
        """
        import random

        # Determine "safe" direction: toward own deployment zone (bottom or top)
        # Player IDs: "1"/"p1" = bottom, "2"/"p2" = top
        own_zone_y = 0 if own_player_id in ("1", "p1") else self.state.map_height - 1

        target = (unit.position[0], own_zone_y)

        # If there's a specific engaging enemy, move directly away from it
        closest_enemy = self._find_closest_enemy(unit, own_player_id)
        if closest_enemy:
            # Move opposite direction from enemy
            dx = unit.position[0] - closest_enemy.position[0]
            dy = unit.position[1] - closest_enemy.position[1]
            dist = max((dx**2 + dy**2) ** 0.5, 0.1)
            runaway_x = round(unit.position[0] + (dx / dist) * move_stat)
            runaway_y = round(unit.position[1] + (dy / dist) * move_stat)
            runaway_x = max(0, min(runaway_x, self.state.map_width - 1))
            runaway_y = max(0, min(runaway_y, self.state.map_height - 1))
            target = (runaway_x, runaway_y)

        self._move_toward(unit, target, move_stat, own_player_id)
        unit.has_advanced = True  # Cannot shoot/charge after Fall Back
        self.state.game_log.append(f"{unit.name} falls back")

    def _shooting_phase(self) -> None:
        """Shooting phase: find targets in range, resolve damage via combat engine."""
        self.state.game_log.append("Shooting phase: units may shoot")
        import numpy as np

        for player in self.state.players.values():
            for unit in player.units.values():
                if not unit.is_alive or unit.has_shot or unit.is_engaged or unit.has_advanced:
                    continue
                # Find opponent
                opponent_pid = next(
                    (pid for pid in self.state.players if pid != player.player_id), None
                )
                if opponent_pid is None:
                    continue
                opponent = self.state.players[opponent_pid]
                # Determine max range from unit's weapons
                model = self._unit_models.get(unit.unit_id)
                max_range = 12  # fallback
                if model:
                    for w in model.ranged_weapons:
                        if w.range_max > max_range:
                            max_range = w.range_max
                targets = []
                for target in opponent.units.values():
                    if not target.is_alive:
                        continue
                    dist = (
                        (unit.position[0] - target.position[0]) ** 2
                        + (unit.position[1] - target.position[1]) ** 2
                    ) ** 0.5
                    if dist > max_range:
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
                # Target selection: closest enemy, biased by faction target_priority
                faction_profile = self._faction_profiles.get(player.faction)
                if faction_profile is not None:
                    from backend.engine.ai.faction_ai import get_target_multiplier

                    # Capture loop variables explicitly for closure
                    _actor_unit = unit
                    _profile = faction_profile

                    def _target_score(t, u=_actor_unit, fp=_profile):
                        d = (
                            (u.position[0] - t.position[0]) ** 2
                            + (u.position[1] - t.position[1]) ** 2
                        ) ** 0.5
                        t_model = self._unit_models.get(t.unit_id)
                        t_mult = 1.0
                        if t_model:
                            t_kw = {kw.lower() for kw in (getattr(t_model, "keywords", []) or [])}
                            t_kw.add(getattr(t_model, "category", "infantry").lower())
                            t_mult = get_target_multiplier(fp, t_kw)
                        return d / max(t_mult, 0.01)  # lower = better

                    target = min(targets, key=_target_score)
                else:
                    # No faction profile — use closest enemy
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
                    from backend.engine.combat import _has_cover, simulate_unit_attack

                    # Determine cover
                    terrain = self.state.terrain_map if hasattr(self.state, "terrain_map") else None
                    target_cat = getattr(defender_model, "category", "infantry")
                    has_cover = (
                        _has_cover(unit.position, target.position, terrain, target_cat)
                        if terrain is not None
                        else False
                    )

                    result = simulate_unit_attack(
                        attacker=attacker_model,
                        defender=defender_model,
                        n_iterations=1000,
                        squad_size=unit.models_remaining,
                        distance=int(dist),
                        has_cover=has_cover,
                        ignores_cover=False,
                    )
                    damage = int(result.total_stats.mean)
                    identity = format_event_identity(
                        actor_id=unit.unit_id, target_id=target.unit_id
                    )
                    self.state.game_log.append(
                        f"{unit.name} shoots {target.name} — expected {result.total_stats.mean:.1f} dmg{identity}"
                    )
                else:
                    # Simplified damage fallback
                    damage = max(1, unit.models_remaining // 2)
                    identity = format_event_identity(
                        actor_id=unit.unit_id, target_id=target.unit_id
                    )
                self.state.deal_damage(target.unit_id, damage)
                self.state.game_log.append(
                    f"{unit.name} hits {target.name} for {damage} damage{identity}"
                )
                unit.has_shot = True

    def _charge_phase(self) -> None:
        """Charge phase: roll 2D6, move into engagement if in range."""
        self.state.game_log.append("Charge phase: units may charge")
        import random

        for player in self.state.players.values():
            for unit in player.units.values():
                if not unit.is_alive or unit.has_charged or unit.is_engaged or unit.has_advanced:
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
                    # Charge succeeds — move unit adjacent to closest enemy
                    # (can't move directly onto enemy's cell — that's occupied)
                    charge_pos = (
                        closest.position[0] - 1
                        if closest.position[0] > unit.position[0]
                        else closest.position[0] + 1
                        if closest.position[0] < unit.position[0]
                        else closest.position[0],
                        closest.position[1],
                    )
                    # Clamp to map bounds
                    charge_pos = (
                        max(0, min(charge_pos[0], self.state.map_width - 1)),
                        max(0, min(charge_pos[1], self.state.map_height - 1)),
                    )
                    if self.state.move_unit(unit.unit_id, charge_pos):
                        unit.is_engaged = True
                        identity = format_event_identity(
                            actor_id=unit.unit_id, target_id=closest.unit_id
                        )
                        self.state.game_log.append(
                            f"{unit.name} charges {closest.name} (rolled {roll} ≥ {dist:.0f}) — engaged!{identity}"
                        )
                else:
                    identity = format_event_identity(
                        actor_id=unit.unit_id, target_id=closest.unit_id
                    )
                    self.state.game_log.append(
                        f"{unit.name} fails charge (rolled {roll} < {dist:.0f}){identity}"
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
        # Find an enemy unit engaged with this unit (within 1 cell, i.e. adjacent or same)
        enemy_unit = None
        for player in self.state.players.values():
            for unit in player.units.values():
                if (
                    unit.is_alive
                    and unit != attacking_unit
                    and abs(unit.position[0] - attacking_unit.position[0]) <= 1
                    and abs(unit.position[1] - attacking_unit.position[1]) <= 1
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
        identity = format_event_identity(
            actor_id=attacking_unit.unit_id, target_id=enemy_unit.unit_id
        )
        self.state.game_log.append(
            f"{attacking_unit.name} hits {enemy_unit.name} for {damage_to_enemy} damage{identity}"
        )

        # Enemy unit damages attacking unit (if still alive)
        if enemy_unit.is_alive:
            damage_to_attacker = 1  # Simplified: 1 damage per attack
            self.state.deal_damage(attacking_unit.unit_id, damage_to_attacker)
            identity = format_event_identity(
                actor_id=enemy_unit.unit_id, target_id=attacking_unit.unit_id
            )
            self.state.game_log.append(
                f"{enemy_unit.name} hits {attacking_unit.name} for {damage_to_attacker} damage{identity}"
            )

    def _battle_shock_tests(self) -> None:
        """Battle-shock tests during Command phase (10ed)."""
        import random

        for player in self.state.players.values():
            for unit in player.units.values():
                if unit.is_alive and not unit.is_above_half_strength:
                    die1 = random.randint(1, 6)
                    die2 = random.randint(1, 6)
                    roll = die1 + die2

                    if roll == 2:  # snake eyes — auto-fail
                        unit.is_battle_shocked = True
                        self.state.game_log.append(
                            f"{unit.name} rolls {roll} (snake eyes) and fails Battle-shock"
                        )
                    elif roll == 12:  # boxcars — auto-pass
                        unit.is_battle_shocked = False
                        self.state.game_log.append(
                            f"{unit.name} rolls {roll} (boxcars) and passes Battle-shock"
                        )
                    elif roll < unit.leadership:
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
