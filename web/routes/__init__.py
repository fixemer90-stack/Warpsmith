"""
Web Routes — FastAPI routers for Warpsmith.

Modules:
    api.py              — Core: /units, /simulate, /map/tiles, /health, /factions
    api_detachments.py  — /detachments, /detachments/{name}
    api_rosters.py      — /rosters CRUD, /rosters/generate, /rosters/synergies
    api_replays.py      — /auto-play, /replays, /results, _parse_log_events
    auth.py             — /register, /login, /logout, /api/me
    pages.py            — HTML pages: /, /team-builder, /scenario-setup, etc.
"""
