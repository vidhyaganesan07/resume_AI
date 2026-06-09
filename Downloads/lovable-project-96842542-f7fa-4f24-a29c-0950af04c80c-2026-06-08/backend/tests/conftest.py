"""Shared pytest fixtures for backend tests."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Set required secrets before any application modules import config.
os.environ.setdefault(
    "JWT_SECRET",
    "test-jwt-secret-with-sufficient-length-for-validation",
)
os.environ.setdefault("ADMIN_USERNAME", "testadmin")
os.environ.setdefault("ADMIN_PASSWORD", "test-admin-password-secure")


@pytest.fixture
def tmp_db_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    db_path = tmp_path / "test_resumescout.db"
    monkeypatch.setattr("config.DB_PATH", db_path)
    monkeypatch.setattr("database.DB_PATH", db_path)
    monkeypatch.setattr("admin.DB_PATH", db_path)
    return db_path


@pytest.fixture
def client(tmp_db_path: Path):
    import database as db
    from fastapi.testclient import TestClient
    from main import app

    db.init_db()
    with TestClient(app) as test_client:
        yield test_client
