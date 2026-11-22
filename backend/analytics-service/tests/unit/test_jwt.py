
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException

import jwt
from src.config import settings
from src.jwt import TokenData, decode_token


def make_token(**overrides) -> str:
    payload = {
        "id": str(uuid.uuid4()),
        "username": "alice",
        "email": "alice@example.com",
        "is_admin": False,
        "token_type": "access",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
    }
    payload.update(overrides)
    return jwt.encode(
        payload,
        key=settings.JWT_PUBLIC_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def test_decode_token_returns_token_data() -> None:
    user_id = uuid.uuid4()
    token = make_token(id=str(user_id), username="alice", is_admin=True)

    result = decode_token(token)

    assert isinstance(result, TokenData)
    assert result.id == user_id
    assert result.username == "alice"
    assert result.email == "alice@example.com"
    assert result.is_admin is True


def test_decode_token_rejects_refresh_token() -> None:
    token = make_token(token_type="refresh")

    with pytest.raises(HTTPException) as exc_info:
        decode_token(token)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Неверный тип токена"


def test_decode_token_rejects_expired_token() -> None:
    token = make_token(exp=datetime.now(timezone.utc) - timedelta(seconds=1))

    with pytest.raises(HTTPException) as exc_info:
        decode_token(token)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Токен просрочен"


def test_decode_token_rejects_wrong_signature() -> None:
    token = jwt.encode(
        {
            "id": str(uuid.uuid4()),
            "username": "alice",
            "email": "alice@example.com",
            "is_admin": False,
            "token_type": "access",
        },
        key="another-secret-key-for-analytics-service-tests",
        algorithm=settings.JWT_ALGORITHM,
    )

    with pytest.raises(HTTPException) as exc_info:
        decode_token(token)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Недействительный токен"


def test_decode_token_rejects_malformed_token() -> None:
    with pytest.raises(HTTPException) as exc_info:
        decode_token("not-a-jwt")

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Недействительный токен"
