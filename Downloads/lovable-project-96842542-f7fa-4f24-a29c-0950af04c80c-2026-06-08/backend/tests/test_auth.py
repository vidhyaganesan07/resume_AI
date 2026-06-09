"""Tests for auth schema validation and endpoints."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from schemas import SignInRequest, SignUpRequest


class TestSignUpRequestEmailValidation:
    def test_accepts_valid_email(self) -> None:
        req = SignUpRequest(email="user@example.com", password="secret12")
        assert req.email == "user@example.com"

    @pytest.mark.parametrize(
        "invalid_email",
        ["not-an-email", "missing-at-sign.com", "@no-local.com", "spaces @bad.com"],
    )
    def test_rejects_invalid_email(self, invalid_email: str) -> None:
        with pytest.raises(ValidationError):
            SignUpRequest(email=invalid_email, password="secret12")


class TestSignInRequestEmailValidation:
    def test_accepts_valid_email(self) -> None:
        req = SignInRequest(email="user@example.com", password="secret12")
        assert req.email == "user@example.com"

    def test_rejects_invalid_email(self) -> None:
        with pytest.raises(ValidationError):
            SignInRequest(email="bad-email", password="secret12")


class TestSignupEndpointValidation:
    def test_invalid_email_returns_422(self, client) -> None:
        response = client.post(
            "/api/auth/signup",
            json={"email": "not-valid", "password": "secret12"},
        )
        assert response.status_code == 422

    def test_valid_signup_succeeds(self, client) -> None:
        response = client.post(
            "/api/auth/signup",
            json={"email": "newuser@example.com", "password": "secret12"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["access_token"]
        assert data["user"]["email"] == "newuser@example.com"
