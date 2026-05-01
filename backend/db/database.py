"""SQLite wrapper — мини ORM без зависимостей."""

import os
import sqlite3
from pathlib import Path
from typing import Optional


class Database:
    def __init__(self, db_path: str = ""):
        if not db_path:
            db_path = os.getenv("DB_PATH", str(Path.cwd() / "simulator.db"))
        self.db_path = db_path
        self._conn: sqlite3.Connection | None = None

    def connect(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA journal_mode=WAL")
        return self._conn

    @property
    def conn(self) -> sqlite3.Connection:
        conn = self.connect()
        assert conn is not None
        return conn

    def execute(self, sql: str, params=()):
        return self.conn.execute(sql, params)

    def executemany(self, sql: str, params_list):
        return self.conn.executemany(sql, params_list)

    def fetchone(self, sql: str, params=()):
        return self.conn.execute(sql, params).fetchone()

    def fetchall(self, sql: str, params=()):
        return self.conn.execute(sql, params).fetchall()

    def commit(self):
        self.conn.commit()

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None

    def migrate(self):
        """Автомиграция: создаёт таблицы при первом запуске."""
        schema = """
        CREATE TABLE IF NOT EXISTS users (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            email        TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            display_name TEXT DEFAULT '',
            created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login   TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS rosters (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER DEFAULT 1,
            name        TEXT NOT NULL,
            faction     TEXT NOT NULL,
            pts_limit   INTEGER DEFAULT 2000,
            detachment  TEXT DEFAULT '',
            units       TEXT NOT NULL DEFAULT '[]',
            is_public   BOOLEAN DEFAULT 0,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS scenarios (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER,
            roster_a_id INTEGER,
            roster_b_id INTEGER,
            mission     TEXT DEFAULT '',
            map         TEXT DEFAULT '{}',
            result      TEXT DEFAULT '{}',
            winner      TEXT DEFAULT '',
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS replays (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            scenario_id INTEGER,
            round       INTEGER,
            phase       TEXT,
            events      TEXT DEFAULT '[]',
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (scenario_id) REFERENCES scenarios(id)
        );

        CREATE INDEX IF NOT EXISTS idx_rosters_user ON rosters(user_id);
        CREATE INDEX IF NOT EXISTS idx_rosters_faction ON rosters(faction);
        CREATE INDEX IF NOT EXISTS idx_scenarios_user ON scenarios(user_id);
        """
        self.conn.executescript(schema)
        self.commit()


# Singleton
db = Database()
