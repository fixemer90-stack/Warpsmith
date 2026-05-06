"""Smoke tests for _parse_log_events."""

import pytest

from web.routes.api_replays import _parse_log_events

SAMPLE = [
    "Starting round 1",
    "Phase: command",
    "Phase: movement",
    "Movement phase: units may move",
    "Ork Boyz remains stationary",
    'Ork Nobz Advances (M+4=10")',
    "Ork Boyz falls back",
    "Shooting phase: units may shoot",
    "Ork Boyz hits Space Marine for 3 damage",
    "Ork Boyz shoots Space Marine — expected 2.5 dmg",
    "Charge phase: units may charge",
    'Ork Boyz charges Space Marine (rolled 9 ≥ 7") – engaged!',
    'Tau Fire Warriors fails charge (rolled 4 < 8")',
    "Fight phase: units may fight",
    "Ork Boyz fought in melee",
    "Ork Boyz moved to (12, 8)",
    "Ork Boyz took 2 damage",
    "Player 1 gained 5 VP",
    "Ork Boyz found no valid path toward Space Marine",
    "Ork Boyz could not move to (5, 3)",
    "Ork Boyz is already at target Space Marine",
]


def test_parses_shoot_events():
    events = _parse_log_events(SAMPLE, 1)
    shoot_events = [e for e in events if e.event_type == "shoot"]
    assert len(shoot_events) == 2
    # "hits ... for N damage"
    hit = shoot_events[0]
    assert hit.actor_name == "Ork Boyz"
    assert hit.target_name == "Space Marine"
    assert hit.result_value == 3.0
    # "shoots ... expected N dmg"
    exp = shoot_events[1]
    assert exp.actor_name == "Ork Boyz"
    assert exp.target_name == "Space Marine"
    assert exp.result_value == 2.5


def test_parses_charge_success():
    events = _parse_log_events(SAMPLE, 1)
    charges = [e for e in events if e.event_type == "charge"]
    success = [c for c in charges if c.detail == "success"]
    assert len(success) == 1
    assert success[0].actor_name == "Ork Boyz"
    assert success[0].target_name == "Space Marine"
    assert success[0].result_value == 1.0


def test_parses_charge_fail():
    events = _parse_log_events(SAMPLE, 1)
    charges = [e for e in events if e.event_type == "charge"]
    fails = [c for c in charges if c.detail == "failed"]
    assert len(fails) == 1
    assert fails[0].actor_name == "Tau Fire Warriors"
    assert fails[0].result_value == 0.0


def test_parses_move_events():
    events = _parse_log_events(SAMPLE, 1)
    moves = [e for e in events if e.event_type == "move"]
    assert len(moves) >= 6  # stationary, advance, fall back, move to, no path, already at target

    details = {e.detail for e in moves if e.detail}
    assert "Remain Stationary" in details
    assert "Fall Back" in details
    assert 'Advance M+4=10"' in details
    assert "No valid path" in details
    assert "Already at target" in details


def test_parses_fight():
    events = _parse_log_events(SAMPLE, 1)
    fights = [e for e in events if e.event_type == "fight"]
    assert len(fights) == 1
    assert fights[0].actor_name == "Ork Boyz"


def test_parses_damage():
    events = _parse_log_events(SAMPLE, 1)
    dmg = [e for e in events if e.event_type == "damage"]
    assert len(dmg) == 1
    assert dmg[0].actor_name == "Ork Boyz"
    assert dmg[0].result_value == 2.0


def test_parses_vp():
    events = _parse_log_events(SAMPLE, 1)
    vp = [e for e in events if e.event_type == "vp"]
    assert len(vp) == 1
    assert vp[0].actor_name == "Player 1"
    assert vp[0].result_value == 5.0


def test_parses_phase_and_info():
    events = _parse_log_events(SAMPLE, 1)
    phases = [e for e in events if e.event_type == "phase"]
    # "Phase: command", "Phase: movement", "Movement phase:...", "Shooting phase:...", etc
    assert len(phases) >= 6

    infos = [e for e in events if e.event_type == "round_start"]
    assert len(infos) == 1


def test_events_not_empty():
    """The original bug: events was always []. Now it must be non-empty."""
    events = _parse_log_events(SAMPLE, 1)
    assert len(events) > 0, "events must not be empty!"
