"""Replay & Auto-play API — full game simulation, replay storage, result viewer."""

import contextlib
import json
import re
from dataclasses import asdict
from datetime import datetime
from enum import Enum

from fastapi import APIRouter, HTTPException

from backend.db.database import db
from backend.engine.ai.autoplay import AutoPlayConfig, run_auto_game
from backend.engine.replay import Replay, ReplayEvent, ReplayRound, load_replay, save_replay
from backend.loader.registry import registry as wiki
from backend.state.roster import RosterState

router = APIRouter()


def _parse_log_events(phase_logs: list[str], round_num: int) -> list:
    """Parse game_log text entries into structured ReplayEvent dicts.

    Strips the identity suffix (``[actor_id=...; target_id=...]``) from each
    log line and uses runtime IDs for ``actor_id``/``target_id`` while keeping
    display names in ``actor_name``/``target_name``.
    """
    from backend.state.runtime_id import strip_event_identity

    events: list = []

    # Patterns match on human-readable text AFTER identity suffix is stripped.
    # They use `$` anchor to avoid partial matches.
    patterns = [
        # "X was destroyed"
        (
            r"^(.+?)\s+was\s+destroyed$",
            lambda m, r, meta: ReplayEvent(
                round=r,
                turn=0,
                event_type="kill",
                actor_id=meta.get("target_id", m.group(1).strip()),
                actor_name=m.group(1).strip(),
                target_id=meta.get("target_id", ""),
                target_name=m.group(1).strip(),
                result_value=1.0,
                detail="destroyed",
                phase="shooting",
            ),
        ),
        # "X shoots Y — expected N dmg"
        (
            r"^(.+?)\s+shoots\s+(.+?)\s+[-—]\s+expected\s+([\d.]+)\s+dmg$",
            lambda m, r, meta: ReplayEvent(
                round=r,
                phase="shooting",
                turn=0,
                event_type="shoot",
                actor_id=meta.get("actor_id", m.group(1).strip()),
                actor_name=m.group(1).strip(),
                target_id=meta.get("target_id", m.group(2).strip()),
                target_name=m.group(2).strip(),
                result_value=float(m.group(3)),
            ),
        ),
        # "X hits Y for N damage in melee"
        (
            r"^(.+?)\s+hits\s+(.+?)\s+for\s+([\d.]+)\s+damage\s+in\s+melee$",
            lambda m, r, meta: ReplayEvent(
                round=r,
                phase="fight",
                turn=0,
                event_type="fight",
                actor_id=meta.get("actor_id", m.group(1).strip()),
                actor_name=m.group(1).strip(),
                target_id=meta.get("target_id", m.group(2).strip()),
                target_name=m.group(2).strip(),
                result_value=float(m.group(3)),
                detail="melee_hit",
            ),
        ),
        # "X hits Y for N damage"
        (
            r"^(.+?)\s+hits\s+(.+?)\s+for\s+([\d.]+)\s+damage$",
            lambda m, r, meta: ReplayEvent(
                round=r,
                phase="shooting",
                turn=0,
                event_type="shoot",
                actor_id=meta.get("actor_id", m.group(1).strip()),
                actor_name=m.group(1).strip(),
                target_id=meta.get("target_id", m.group(2).strip()),
                target_name=m.group(2).strip(),
                result_value=float(m.group(3)),
            ),
        ),
        # 'X charges Y (rolled N ≥ D") – engaged!'
        (
            r"^(.+?)\s+charges\s+(.+?)\s+\(rolled\s+(\d+)\s+[≥>=]\s+[\d.]+",
            lambda m, r, meta: ReplayEvent(
                round=r,
                phase="charge",
                turn=0,
                event_type="charge",
                actor_id=meta.get("actor_id", m.group(1).strip()),
                actor_name=m.group(1).strip(),
                target_id=meta.get("target_id", m.group(2).strip()),
                target_name=m.group(2).strip(),
                result_value=1.0,
                dice_rolled=[int(m.group(3))],
                detail="success",
            ),
        ),
        # 'X fails charge (rolled N < D")'
        (
            r"^(.+?)\s+fails\s+charge\s+\(rolled\s+(\d+)\s+<",
            lambda m, r, meta: ReplayEvent(
                round=r,
                phase="charge",
                turn=0,
                event_type="charge",
                actor_id=meta.get("actor_id", m.group(1).strip()),
                actor_name=m.group(1).strip(),
                result_value=0.0,
                dice_rolled=[int(m.group(2))],
                detail="failed",
            ),
        ),
        # 'X Advances (M+N=D")'
        (
            r'^(.+?)\s+Advances\s+\(M\+(\d+)=(\d+)"',
            lambda m, r, meta: ReplayEvent(
                round=r,
                phase="movement",
                turn=0,
                event_type="move",
                actor_id=meta.get("actor_id", m.group(1).strip()),
                actor_name=m.group(1).strip(),
                detail=f'Advance M+{m.group(2)}={m.group(3)}"',
            ),
        ),
        # "X remains stationary"
        (
            r"^(.+?)\s+remains\s+stationary$",
            lambda m, r, meta: ReplayEvent(
                round=r,
                phase="movement",
                turn=0,
                event_type="move",
                actor_id=meta.get("actor_id", m.group(1).strip()),
                actor_name=m.group(1).strip(),
                detail="Remain Stationary",
            ),
        ),
        # "X falls back"
        (
            r"^(.+?)\s+falls\s+back$",
            lambda m, r, meta: ReplayEvent(
                round=r,
                phase="movement",
                turn=0,
                event_type="move",
                actor_id=meta.get("actor_id", m.group(1).strip()),
                actor_name=m.group(1).strip(),
                detail="Fall Back",
            ),
        ),
        # "X is already at target Y"
        (
            r"^(.+?)\s+is\s+already\s+at\s+target\s+(.+)$",
            lambda m, r, meta: ReplayEvent(
                round=r,
                phase="movement",
                turn=0,
                event_type="move",
                actor_id=meta.get("actor_id", m.group(1).strip()),
                actor_name=m.group(1).strip(),
                target_id=m.group(2).strip(),
                target_name=m.group(2).strip(),
                detail="Already at target",
            ),
        ),
        # "X fought in melee"
        (
            r"^(.+?)\s+fought\s+in\s+melee$",
            lambda m, r, meta: ReplayEvent(
                round=r,
                phase="fight",
                turn=0,
                event_type="fight",
                actor_id=meta.get("actor_id", m.group(1).strip()),
                actor_name=m.group(1).strip(),
            ),
        ),
        # "X moved to (a, b)"
        (
            r"^(.+?)\s+moved\s+to\s+\((\d+),\s*(\d+)\)",
            lambda m, r, meta: ReplayEvent(
                round=r,
                phase="movement",
                turn=0,
                event_type="move",
                actor_id=meta.get("actor_id", m.group(1).strip()),
                actor_name=m.group(1).strip(),
                position_after={"x": int(m.group(2)), "y": int(m.group(3))},
            ),
        ),
        # "X took N damage"
        (
            r"^(.+?)\s+took\s+([\d.]+)\s+damage$",
            lambda m, r, meta: ReplayEvent(
                round=r,
                phase="",
                turn=0,
                event_type="damage",
                actor_id=meta.get("target_id", m.group(1).strip()),
                actor_name=m.group(1).strip(),
                result_value=float(m.group(2)),
            ),
        ),
        # "PlayerName gained N VP"
        (
            r"^(.+?)\s+gained\s+([\d.]+)\s+VP$",
            lambda m, r, meta: ReplayEvent(
                round=r,
                phase="command",
                turn=0,
                event_type="vp",
                actor_id=m.group(1).strip(),
                actor_name=m.group(1).strip(),
                result_value=float(m.group(2)),
            ),
        ),
        # "X found no valid path toward Y"
        (
            r"^(.+?)\s+found\s+no\s+valid\s+path\s+toward\s+(.+)$",
            lambda m, r, meta: ReplayEvent(
                round=r,
                phase="movement",
                turn=0,
                event_type="move",
                actor_id=meta.get("actor_id", m.group(1).strip()),
                actor_name=m.group(1).strip(),
                target_id=m.group(2).strip(),
                target_name=m.group(2).strip(),
                detail="No valid path",
            ),
        ),
        # "X could not move to (a, b)"
        (
            r"^(.+?)\s+could\s+not\s+move\s+to\s+\((\d+),\s*(\d+)\)",
            lambda m, r, meta: ReplayEvent(
                round=r,
                phase="movement",
                turn=0,
                event_type="move",
                actor_id=meta.get("actor_id", m.group(1).strip()),
                actor_name=m.group(1).strip(),
                detail=f"Could not move to ({m.group(2)}, {m.group(3)})",
            ),
        ),
        # Phase banner: "Movement phase: units may move", "Shooting phase: ..."
        (
            r"^([A-Z][a-z]+)\s+phase:\s*",
            lambda m, r, meta: ReplayEvent(
                round=r,
                phase=m.group(1).lower(),
                turn=0,
                event_type="phase",
                actor_id="",
                actor_name="",
                detail=m.group(1),
            ),
        ),
        # "Phase: command" etc
        (
            r"^Phase:\s*(.+)$",
            lambda m, r, meta: ReplayEvent(
                round=r,
                phase=m.group(1).strip().lower(),
                turn=0,
                event_type="phase",
                actor_id="",
                actor_name="",
                detail=m.group(1).strip(),
            ),
        ),
        # "Starting round N"
        (
            r"^Starting\s+round\s+\d+$",
            lambda m, r, meta: ReplayEvent(
                round=r,
                phase="",
                turn=0,
                event_type="round_start",
                actor_id="",
                actor_name="",
                detail=m.group(0),
            ),
        ),
        # Generic fallback — any non-empty line becomes an "info" event
        (
            r"^(.+)$",
            lambda m, r, meta: ReplayEvent(
                round=r,
                phase="",
                turn=0,
                event_type="info",
                actor_id="",
                actor_name="",
                detail=m.group(1)[:200],
            ),
        ),
    ]

    for log_line in phase_logs:
        if not isinstance(log_line, str) or not log_line.strip():
            continue
        # Strip identity suffix → human text + runtime-ID metadata
        human_text, meta = strip_event_identity(log_line.strip())
        if not human_text:
            continue

        for pattern, factory in patterns:
            m = re.match(pattern, human_text)
            if m:
                with contextlib.suppress(Exception):
                    events.append(factory(m, round_num, meta))
                break

    return events


@router.post("/auto-play")
async def auto_play_simulation(
    roster_a_id: int,
    roster_b_id: int,
    mission: str = "only_war",
    deployment: str = "standard",
    max_rounds: int = 5,
    seed: int | None = None,
):
    """Запуск полной AI vs AI симуляции."""

    try:
        # Ensure wiki is loaded
        with contextlib.suppress(Exception):
            wiki.load()

        # Load rosters from database
        roster_a_row = db.fetchone("SELECT * FROM rosters WHERE id = ?", (roster_a_id,))
        roster_b_row = db.fetchone("SELECT * FROM rosters WHERE id = ?", (roster_b_id,))

        if not roster_a_row:
            raise HTTPException(status_code=404, detail=f"Roster A not found: {roster_a_id}")

        if not roster_b_row:
            raise HTTPException(status_code=404, detail=f"Roster B not found: {roster_b_id}")

        from backend.engine.ai.deployment import DeploymentType
        from backend.model.unit import Unit, Weapon
        from backend.state.roster import RosterState

        def units_from_db(units_json):
            units_list = []
            units_data = json.loads(units_json)
            for u_data in units_data:
                unit = wiki.get_unit(u_data["unit_name"])
                if unit:
                    unit_copy = Unit(
                        name=unit.name,
                        faction=unit.faction,
                        category=unit.category,
                        movement=unit.movement,
                        toughness=unit.toughness,
                        save=unit.save,
                        wounds=unit.wounds,
                        leadership=unit.leadership,
                        objective_control=unit.objective_control,
                        squad_size={
                            "min": u_data["squad_size"],
                            "max": u_data["squad_size"],
                            "step": 1,
                        },
                        ranged_weapons=unit.ranged_weapons,
                        melee_weapons=unit.melee_weapons,
                        abilities=unit.abilities,
                        keywords=unit.keywords,
                        faction_keywords=unit.faction_keywords,
                        tags=unit.tags,
                        points=unit.points,
                        model_count=unit.model_count,
                        is_epic_hero=unit.is_epic_hero,
                        can_be_warlord=unit.can_be_warlord,
                        is_leader=unit.is_leader,
                        leader_for=unit.leader_for,
                    )
                    units_list.append((unit.name, unit_copy))
            return units_list

        roster_a = RosterState(
            name=roster_a_row["name"],
            faction=roster_a_row["faction"],
            total_pts=roster_a_row["pts_limit"],
            units=units_from_db(roster_a_row["units"]),
        )

        roster_b = RosterState(
            name=roster_b_row["name"],
            faction=roster_b_row["faction"],
            total_pts=roster_b_row["pts_limit"],
            units=units_from_db(roster_b_row["units"]),
        )

        try:
            deployment_type = DeploymentType(deployment.lower().strip())
        except ValueError:
            raise HTTPException(
                status_code=400, detail=f"Unknown deployment type: {deployment}"
            ) from None

        if seed is None:
            import random as _random

            seed = _random.randint(1, 99999)

        config = AutoPlayConfig(max_rounds=max_rounds, deployment_type=deployment_type, seed=seed)
        result = run_auto_game(roster_a, roster_b, mission_name=mission, config=config)

        if result.error:
            raise HTTPException(status_code=400, detail=result.error)

        # Save replay to DB so round-viewer can load it
        import uuid

        game_id = (
            result.game_state.game_id if result.game_state else f"auto_{uuid.uuid4().hex[:12]}"
        )
        replay_rounds = []
        for rl in result.round_logs:
            round_num = rl.get("round", 0)
            phase_logs = rl.get("phase_logs", [])
            parsed_events = _parse_log_events(phase_logs, round_num)
            replay_rounds.append(
                ReplayRound(
                    round=round_num,
                    start_state=rl.get("start_state", {}),
                    end_state=rl.get("end_state", {}),
                    events=parsed_events,
                    phase_summary={"phase_logs": phase_logs},
                )
            )

        replay = Replay(
            game_id=game_id,
            created_at=datetime.utcnow().isoformat(),
            rosters={
                "roster_a": {"name": roster_a.name, "faction": roster_a.faction},
                "roster_b": {"name": roster_b.name, "faction": roster_b.faction},
            },
            mission=mission,
            deployment=deployment,
            seed=seed,
            rounds=replay_rounds,
            summary=result.summary,
        )
        save_replay(db.conn, replay)

        result_dict = result.to_dict()
        return {
            "success": True,
            "game_id": game_id,
            "result": result_dict,
            "replay_log": result.round_logs,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


# ── Replay API ─────────────────────────────────────────


@router.get("/replays/{game_id}")
async def get_replay(game_id: str):
    """Return full replay JSON for a given game_id."""
    replay = load_replay(db.conn, game_id)
    if replay is None:
        raise HTTPException(status_code=404, detail=f"Replay {game_id} not found")
    return json.loads(json.dumps(asdict(replay), default=str))


@router.get("/replays")
async def list_replays_view():
    """Return list of replays from DB."""
    rows = db.fetchall(
        "SELECT game_id, created_at, mission, deployment, seed, summary FROM replays ORDER BY created_at DESC"
    )
    result = []
    for r in rows:
        result.append(
            {
                "game_id": r["game_id"],
                "created_at": r["created_at"],
                "mission": r["mission"],
                "deployment": r["deployment"],
                "seed": r["seed"],
                "summary": json.loads(r["summary"]) if r["summary"] else {},
            }
        )
    return result


# ── Result API ────────────────────────────────────────


@router.get("/results/{game_id}")
async def get_result(game_id: str):
    """Return full replay+result JSON for a given game_id."""
    replay = load_replay(db.conn, game_id)
    if replay is None:
        raise HTTPException(status_code=404, detail=f"Result {game_id} not found")
    data = json.loads(json.dumps(asdict(replay), default=str))

    summary = data.setdefault("summary", {})
    rounds = data.get("rounds") or []

    # Authoritative final snapshot precedence:
    # 1) summary.final_state (if persisted explicitly),
    # 2) last round end_state,
    # 3) last round start_state.
    final_state = summary.get("final_state")
    if not final_state and rounds:
        last_round = rounds[-1]
        final_state = last_round.get("end_state") or last_round.get("start_state") or {}

    if final_state:
        data["final_state"] = final_state
        summary.setdefault("final_state", final_state)

    # Expose final VP from the same authoritative final snapshot.
    final_vp = (final_state or {}).get("victory_points", {})
    if final_vp:
        summary.setdefault("final_victory_points", final_vp)

    # Compute winner from authoritative final VP if summary.winner is None.
    if summary.get("winner") is None and final_vp:
        pids = sorted(final_vp.keys())
        if len(pids) >= 2 and (final_vp[pids[0]] != final_vp[pids[1]]):
            summary["winner"] = (
                int(pids[0]) if final_vp[pids[0]] > final_vp[pids[1]] else int(pids[1])
            )

    return data
