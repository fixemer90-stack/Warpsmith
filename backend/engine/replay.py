"""
F3.6 — Replay Recording: JSON Event Log per Round/Phase.

Записывает события игры в структурированный реплей с возможностью
сериализации в JSON и сохранения в SQLite.
"""

from __future__ import annotations

import json
import sqlite3
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any

from backend.model.unit import Unit
from backend.state.game_state import GameState, UnitState


@dataclass
class ReplayEvent:
    """Одно событие в реплее."""

    round: int
    phase: str
    turn: int
    event_type: str  # "shoot", "charge", "move", "kill", "damage", "cp_spend", etc.
    actor_id: str  # unit_id инициатора
    actor_name: str  # удобочитаемое имя
    target_id: str | None = None
    target_name: str | None = None
    weapon_index: int | None = None
    weapon_name: str | None = None
    dice_rolled: list[int] | None = None
    result_value: float | None = None  # урон, CP, VP
    detail: str | None = None  # дополнительный текст
    position_before: dict[str, int] | None = None
    position_after: dict[str, int] | None = None
    timestamp: float = 0.0  # ms от начала игры; устанавливается ReplayRecorder.record()


@dataclass
class ReplayRound:
    """Один раунд реплея."""

    round: int
    start_state: dict[str, Any]  # снимок GameState в начале раунда
    end_state: dict[str, Any]  # снимок в конце
    events: list[ReplayEvent] = field(default_factory=list)
    phase_summary: dict[str, dict[str, Any]] = field(default_factory=dict)


@dataclass
class Replay:
    """Полный реплей игры."""

    game_id: str  # UUID
    created_at: str  # ISO timestamp
    rosters: dict[str, Any]  # roster_a, roster_b
    mission: str
    deployment: str
    seed: int
    rounds: list[ReplayRound]
    summary: dict[str, Any]  # итоги (кто победил, счёт)
    version: str = "1.0"


class ReplayRecorder:
    """Записывает события игры в структурированный реплей."""

    def __init__(
        self, game_id: str, rosters: dict[str, Any], mission: str, deployment: str, seed: int
    ):
        self.replay = Replay(
            game_id=game_id,
            created_at=datetime.utcnow().isoformat(),
            rosters=rosters,
            mission=mission,
            deployment=deployment,
            seed=seed,
            rounds=[],
            summary={},
        )
        self._start_time: float | None = None
        self._current_round: ReplayRound | None = None

    def start_game(self):
        """Запустить таймер реплея."""
        self._start_time = time.time()

    def start_round(self, round_num: int, state: GameState):
        """Начать новый раунд."""
        self._current_round = ReplayRound(
            round=round_num,
            start_state=_snapshot_state(state),
            end_state={},
        )

    def end_round(self, state: GameState):
        """Завершить раунд и сохранить снимок."""
        if self._current_round:
            self._current_round.end_state = _snapshot_state(state)
            self.replay.rounds.append(self._current_round)
            self._current_round = None

    def record(self, event: ReplayEvent):
        """Записать одно событие."""
        if self._start_time:
            elapsed = (time.time() - self._start_time) * 1000
            event.timestamp = elapsed
        if self._current_round is not None:
            self._current_round.events.append(event)

    def record_shoot(
        self,
        round_num: int,
        phase: str,
        turn: int,
        actor: UnitState,
        target: UnitState,
        weapon_name: str,
        damage: float,
        dice: list[int] | None = None,
    ):
        """Записать событие стрельбы."""
        self.record(
            ReplayEvent(
                round=round_num,
                phase=phase,
                turn=turn,
                event_type="shoot",
                actor_id=actor.unit_id,
                actor_name=actor.name,
                target_id=target.unit_id,
                target_name=target.name,
                weapon_name=weapon_name,
                dice_rolled=dice,
                result_value=damage,
                position_before=_pos_dict(actor.position),
            )
        )

    def record_charge(
        self,
        round_num: int,
        phase: str,
        turn: int,
        actor: UnitState,
        target: UnitState,
        charge_roll: int,
        success: bool,
    ):
        """Записать событие заряда."""
        self.record(
            ReplayEvent(
                round=round_num,
                phase=phase,
                turn=turn,
                event_type="charge",
                actor_id=actor.unit_id,
                actor_name=actor.name,
                target_id=target.unit_id,
                target_name=target.name,
                dice_rolled=[charge_roll],
                result_value=1.0 if success else 0.0,
                detail="success" if success else "failed",
            )
        )

    def record_kill(
        self, round_num: int, phase: str, turn: int, actor: UnitState, target: UnitState
    ):
        self.record(
            ReplayEvent(
                round=round_num,
                phase=phase,
                turn=turn,
                event_type="kill",
                actor_id=actor.unit_id,
                actor_name=actor.name,
                target_id=target.unit_id,
                target_name=target.name,
                result_value=1.0,
            )
        )

    def record_move(
        self,
        round_num: int,
        phase: str,
        turn: int,
        actor: UnitState,
        from_pos: tuple,
        to_pos: tuple,
    ):
        self.record(
            ReplayEvent(
                round=round_num,
                phase=phase,
                turn=turn,
                event_type="move",
                actor_id=actor.unit_id,
                actor_name=actor.name,
                position_before={"x": from_pos[0], "y": from_pos[1]},
                position_after={"x": to_pos[0], "y": to_pos[1]},
            )
        )

    def record_damage(
        self,
        round_num: int,
        phase: str,
        turn: int,
        actor: UnitState,
        target: UnitState,
        damage: float,
    ):
        """Записать событие нанесения урона (не убийства)."""
        self.record(
            ReplayEvent(
                round=round_num,
                phase=phase,
                turn=turn,
                event_type="damage",
                actor_id=actor.unit_id,
                actor_name=actor.name,
                target_id=target.unit_id,
                target_name=target.name,
                result_value=damage,
            )
        )

    def record_cp_spend(
        self, round_num: int, phase: str, turn: int, actor_id: str, actor_name: str, cp_amount: int
    ):
        """Записать трату командных очков."""
        self.record(
            ReplayEvent(
                round=round_num,
                phase=phase,
                turn=turn,
                event_type="cp_spend",
                actor_id=actor_id,
                actor_name=actor_name,
                result_value=float(cp_amount),
            )
        )

    def set_summary(self, summary: dict[str, Any]):
        self.replay.summary = summary


def _snapshot_state(state: GameState) -> dict[str, Any]:
    """Canonical GameState snapshot — delegates to backend.state.game_state."""
    from backend.state.game_state import snapshot_game_state

    return snapshot_game_state(state)


def _unit_snapshot(unit: UnitState) -> dict[str, Any]:
    """Canonical unit snapshot — delegates to backend.state.game_state."""
    from backend.state.game_state import _unit_snapshot as _canonical_unit_snapshot

    return _canonical_unit_snapshot(unit, player_id="")


def _pos_dict(pos) -> dict[str, int]:
    if isinstance(pos, (list, tuple)) and len(pos) >= 2:
        return {"x": int(pos[0]), "y": int(pos[1])}
    if hasattr(pos, "x") and hasattr(pos, "y"):
        return {"x": int(pos.x), "y": int(pos.y)}
    return {"x": 0, "y": 0}


# SQL таблица для хранения реплеев
TABLE_REPLAYS = """
CREATE TABLE IF NOT EXISTS replays (
    game_id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    roster_a TEXT NOT NULL,
    roster_b TEXT NOT NULL,
    mission TEXT NOT NULL,
    deployment TEXT NOT NULL,
    seed INTEGER NOT NULL,
    replay_json TEXT NOT NULL,
    summary TEXT,
    user_id INTEGER
)
"""


def replay_to_json(replay: Replay) -> str:
    """Сериализовать Replay в JSON."""

    def _default(obj):
        if hasattr(obj, "__dataclass_fields__"):
            return asdict(obj)
        msg = f"Object of type {type(obj).__name__} is not JSON serializable"
        raise TypeError(msg)

    return json.dumps(asdict(replay), default=_default, indent=2)


def replay_from_json(data: str) -> Replay:
    """Десериализовать Replay из JSON."""
    raw = json.loads(data)
    return _replay_from_dict(raw)


def _replay_from_dict(raw: dict[str, Any]) -> Replay:
    """Рекурсивно восстановить Replay из словаря."""
    rounds = []
    for r in raw.get("rounds", []):
        events = [ReplayEvent(**e) for e in r.get("events", [])]
        rounds.append(
            ReplayRound(
                round=r["round"],
                start_state=r.get("start_state", {}),
                end_state=r.get("end_state", {}),
                events=events,
                phase_summary=r.get("phase_summary", {}),
            )
        )

    return Replay(
        game_id=raw["game_id"],
        created_at=raw["created_at"],
        rosters=raw.get("rosters", {}),
        mission=raw.get("mission", ""),
        deployment=raw.get("deployment", ""),
        seed=raw.get("seed", 0),
        rounds=rounds,
        summary=raw.get("summary", {}),
        version=raw.get("version", "1.0"),
    )


def save_replay(db: sqlite3.Connection, replay: Replay, user_id: int | None = None):
    """Сохранить реплей в SQLite."""
    db.execute(
        """INSERT OR REPLACE INTO replays
           (game_id, created_at, roster_a, roster_b,
            mission, deployment, seed, replay_json, summary, user_id)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            replay.game_id,
            replay.created_at,
            json.dumps(replay.rosters.get("roster_a", {})),
            json.dumps(replay.rosters.get("roster_b", {})),
            replay.mission,
            replay.deployment,
            replay.seed,
            replay_to_json(replay),
            json.dumps(replay.summary),
            user_id,
        ),
    )
    db.commit()


def load_replay(db: sqlite3.Connection, game_id: str) -> Replay | None:
    """Загрузить реплей из SQLite по game_id."""
    row = db.execute(
        "SELECT replay_json FROM replays WHERE game_id = ?",
        (game_id,),
    ).fetchone()
    if row:
        return replay_from_json(row[0])
    return None


def list_replays(
    db: sqlite3.Connection, user_id: int | None = None, limit: int = 20
) -> list[dict[str, Any]]:
    """Список реплеев (метаданные без полного JSON)."""
    if user_id:
        rows = db.execute(
            """SELECT game_id, created_at, mission, deployment,
                   seed, summary
              FROM replays WHERE user_id = ?
              ORDER BY created_at DESC LIMIT ?""",
            (user_id, limit),
        ).fetchall()
    else:
        rows = db.execute(
            """SELECT game_id, created_at, mission, deployment,
                   seed, summary
              FROM replays ORDER BY created_at DESC LIMIT ?""",
            (limit,),
        ).fetchall()

    return [
        {
            "game_id": r[0],
            "created_at": r[1],
            "mission": r[2],
            "deployment": r[3],
            "seed": r[4],
            "summary": json.loads(r[5]) if r[5] else {},
        }
        for r in rows
    ]


# API endpoints: see web/routes/api.py
# GET /api/replays/{game_id} — load replay by game_id
# GET /api/replays — list all replays
# POST /api/auto-play — runs simulation and saves replay
