#!/usr/bin/env python3
"""Deterministic final-gate smoke for replay/result VP authority.

Creates isolated DB, seeds two minimal rosters, runs /api/auto-play, and verifies:
- runtime/replay end_state VP
- /api/results summary.final_victory_points
- /api/replays last round end_state VP
- /result/{game_id} page shell availability + VP wiring hooks
"""

from __future__ import annotations

import importlib
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _norm_vp(vp: dict) -> dict[str, int]:
    out: dict[str, int] = {}
    for k, v in (vp or {}).items():
        out[str(k)] = int(v)
    return out


def main() -> int:
    db_dir = tempfile.mkdtemp(prefix="warpsmith-final-gate-")
    db_path = Path(db_dir) / "smoke.db"
    os.environ["DB_PATH"] = str(db_path)
    os.environ.setdefault("RATE_LIMIT_ANON", "999999/minute")
    os.environ.setdefault("RATE_LIMIT_STORAGE", "memory://")

    from backend.db.database import Database

    db = Database(str(db_path))
    db.migrate()

    units_json = json.dumps(
        [
            {
                "unit_name": "Boyz",
                "squad_size": 10,
                "loadout_pts": 0,
                "nob_pts": 0,
                "is_warlord": True,
            }
        ]
    )

    db.execute(
        "INSERT INTO rosters (id, user_id, name, faction, pts_limit, detachment, units, is_public) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (1001, 1, "Smoke A", "orks", 2000, "", units_json, 0),
    )
    db.execute(
        "INSERT INTO rosters (id, user_id, name, faction, pts_limit, detachment, units, is_public) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (1002, 1, "Smoke B", "orks", 2000, "", units_json, 0),
    )
    db.commit()
    db.close()

    test_client_cls = importlib.import_module("fastapi.testclient").TestClient
    app = importlib.import_module("main").app

    with test_client_cls(app) as client:
        auto = client.post(
            "/api/auto-play",
            params={
                "roster_a_id": 1001,
                "roster_b_id": 1002,
                "mission": "only_war",
                "deployment": "standard",
                "max_rounds": 1,
                "seed": 4242,
            },
        )
        assert auto.status_code == 200, f"auto-play status={auto.status_code} body={auto.text}"
        auto_data = auto.json()
        game_id = auto_data["game_id"]

        runtime_vp = _norm_vp(
            (auto_data.get("replay_log") or [{}])[-1].get("end_state", {}).get("victory_points", {})
        )
        assert runtime_vp, "runtime VP missing from replay_log end_state"

        res = client.get(f"/api/results/{game_id}")
        assert res.status_code == 200, f"results status={res.status_code} body={res.text}"
        result_data = res.json()
        api_vp = _norm_vp(result_data.get("summary", {}).get("final_victory_points", {}))

        rep = client.get(f"/api/replays/{game_id}")
        assert rep.status_code == 200, f"replay status={rep.status_code} body={rep.text}"
        replay_data = rep.json()
        replay_vp = _norm_vp(
            (replay_data.get("rounds") or [{}])[-1].get("end_state", {}).get("victory_points", {})
        )

        page = client.get(f"/result/{game_id}")
        assert page.status_code == 200, f"result page status={page.status_code}"
        html = page.text
        assert "result_chart.js" in html
        assert "finalVp(0)" in html and "finalVp(1)" in html

        js_path = Path(__file__).resolve().parents[1] / "web" / "static" / "result_chart.js"
        js_text = js_path.read_text(encoding="utf-8")
        assert "final_victory_points" in js_text, (
            "result chart JS no longer references authoritative final_victory_points"
        )

    assert runtime_vp == replay_vp == api_vp, (
        "VP mismatch across runtime/replay/results: "
        f"runtime={runtime_vp} replay={replay_vp} api={api_vp}"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
