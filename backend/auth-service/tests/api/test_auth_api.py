
from unittest.mock import AsyncMock

from src.exceptions import UserNotFoundError
from src.schemas import JWTTokenPairResponseSchema


async def test_authenticate_returns_token_pair(client, auth_service: AsyncMock) -> None:
    auth_service.get_tokens.return_value = JWTTokenPairResponseSchema(
        access="access-token",
        refresh="refresh-token",
    )

    response = await client.post(
        "/auth/token",
        json={"username": "alice", "password": "password123"},
    )

    assert response.status_code == 200
    assert response.json() == {"access": "access-token", "refresh": "refresh-token"}
    auth_service.get_tokens.assert_awaited_once()


async def test_authenticate_returns_error_for_invalid_credentials(client, auth_service: AsyncMock) -> None:
    auth_service.get_tokens.side_effect = UserNotFoundError()

    response = await client.post(
        "/auth/token",
        json={"username": "alice", "password": "password123"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Пользователь не найден"}


async def test_authenticate_validates_request_body(client, auth_service: AsyncMock) -> None:
    response = await client.post("/auth/token", json={"username": "alice"})

    assert response.status_code == 422
    auth_service.get_tokens.assert_not_awaited()


async def test_refresh_token_returns_new_pair(client, auth_service: AsyncMock) -> None:
    auth_service.refresh_token.return_value = JWTTokenPairResponseSchema(
        access="new-access",
        refresh="new-refresh",
    )

    response = await client.post("/auth/token/refresh", json="old-refresh")

    assert response.status_code == 200
    assert response.json() == {"access": "new-access", "refresh": "new-refresh"}
    auth_service.refresh_token.assert_awaited_once_with("old-refresh")


async def test_refresh_token_requires_body(client, auth_service: AsyncMock) -> None:
    response = await client.post("/auth/token/refresh")

    assert response.status_code == 401
    assert response.json() == {"detail": "Нет refresh токена"}
    auth_service.refresh_token.assert_not_awaited()
