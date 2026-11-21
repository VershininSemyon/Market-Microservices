
from datetime import datetime, timedelta, timezone

import jwt
import pytest

from src.config import settings
from src.exceptions import InvalidTokenError, TokenExpiredError
from src.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


@pytest.fixture(scope="module")
def hashed_password() -> str:
    return hash_password("secret-password")


def test_hash_password_returns_bcrypt_hash(hashed_password: str) -> None:
    assert hashed_password != "secret-password"
    assert hashed_password.startswith("$2")


def test_verify_password_accepts_correct_password(hashed_password: str) -> None:
    assert verify_password("secret-password", hashed_password) is True


def test_verify_password_rejects_wrong_password(hashed_password: str) -> None:
    assert verify_password("wrong-password", hashed_password) is False


def test_create_access_token_contains_payload_and_type() -> None:
    token = create_access_token({"id": "user-id", "username": "alice", "is_admin": False})

    payload = decode_token(token)

    assert payload["id"] == "user-id"
    assert payload["username"] == "alice"
    assert payload["is_admin"] is False
    assert payload["token_type"] == "access"


def test_create_refresh_token_contains_payload_and_type() -> None:
    token = create_refresh_token({"id": "user-id", "username": "alice", "is_admin": True})

    payload = decode_token(token)

    assert payload["id"] == "user-id"
    assert payload["is_admin"] is True
    assert payload["token_type"] == "refresh"


def test_decode_token_raises_on_expired_token() -> None:
    token = jwt.encode(
        {
            "id": "user-id",
            "token_type": "access",
            "exp": datetime.now(timezone.utc) - timedelta(seconds=1),
        },
        key=settings.JWT_PRIVATE_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )

    with pytest.raises(TokenExpiredError):
        decode_token(token)


def test_decode_token_raises_on_invalid_token() -> None:
    with pytest.raises(InvalidTokenError):
        decode_token("not-a-jwt")


def test_decode_token_raises_on_wrong_signature() -> None:
    token = jwt.encode(
        {"id": "user-id", "token_type": "access"},
        key="another-secret-key-for-auth-service-tests",
        algorithm=settings.JWT_ALGORITHM,
    )

    with pytest.raises(InvalidTokenError):
        decode_token(token)
