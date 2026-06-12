"""Tests for config secret validation and JWT behavior."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from jose import jwt

from config import JWT_ALGORITHM, JWT_EXPIRE_DAYS, JWT_SECRET, _require_env


class TestConfigValidation:
    def test_require_env_raises_when_missing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("MISSING_TEST_VAR", raising=False)
        with pytest.raises(RuntimeError, match="MISSING_TEST_VAR"):
            _require_env("MISSING_TEST_VAR")

    def test_require_env_returns_value(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("PRESENT_TEST_VAR", "ok")
        assert _require_env("PRESENT_TEST_VAR") == "ok"


class TestJWTSecurity:
    def test_token_includes_expiration(self) -> None:
        from auth import create_access_token

        token = create_access_token("user-1", "user@example.com")
        claims = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])

        assert claims["sub"] == "user-1"
        assert claims["email"] == "user@example.com"
        assert "exp" in claims
        assert "iat" in claims

        exp = datetime.fromtimestamp(claims["exp"], tz=timezone.utc)
        iat = datetime.fromtimestamp(claims["iat"], tz=timezone.utc)
        assert exp - iat >= timedelta(days=JWT_EXPIRE_DAYS - 1)

    def test_bcrypt_hash_and_verify(self) -> None:
        from auth import hash_password, verify_password

        hashed = hash_password("my-secure-password")
        assert hashed != "my-secure-password"
        assert verify_password("my-secure-password", hashed)
        assert not verify_password("wrong-password", hashed)
