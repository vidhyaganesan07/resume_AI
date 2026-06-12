"""Tests for SQLite connection lifecycle."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from admin import _conn
from database import get_db


class TestSQLiteContextManagers:
    def test_admin_conn_closes_connection(
        self, tmp_db_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        connections: list[sqlite3.Connection] = []
        real_connect = sqlite3.connect

        def tracking_connect(*args, **kwargs):
            conn = real_connect(*args, **kwargs)
            connections.append(conn)
            return conn

        monkeypatch.setattr(sqlite3, "connect", tracking_connect)

        with _conn() as conn:
            conn.execute("SELECT 1")

        assert len(connections) == 1
        with pytest.raises(sqlite3.ProgrammingError):
            connections[0].execute("SELECT 1")

    def test_get_db_closes_connection(
        self, tmp_db_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        connections: list[sqlite3.Connection] = []
        real_connect = sqlite3.connect

        def tracking_connect(*args, **kwargs):
            conn = real_connect(*args, **kwargs)
            connections.append(conn)
            return conn

        monkeypatch.setattr(sqlite3, "connect", tracking_connect)

        with get_db() as conn:
            conn.execute("SELECT 1")

        assert len(connections) == 1
        with pytest.raises(sqlite3.ProgrammingError):
            connections[0].execute("SELECT 1")

    def test_get_db_rolls_back_on_error(self, tmp_db_path: Path) -> None:
        import database as db

        db.init_db()

        with pytest.raises(ValueError):
            with get_db() as conn:
                conn.execute(
                    "INSERT INTO users (id, email, password_hash, created_at) "
                    "VALUES ('u1', 'a@b.com', 'hash', 'now')"
                )
                raise ValueError("force rollback")

        with get_db() as conn:
            count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        assert count == 0
