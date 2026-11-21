
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock

from src.exceptions import InvalidTokenError
from src.schemas import UserReadSchema


def make_user(**overrides) -> UserReadSchema:
    data = {
        "id": uuid.uuid4(),
        "username": "alice",
        "email": "alice@example.com",
        "registration_date": datetime.now(timezone.utc),
    }
    data.update(overrides)
    return UserReadSchema(**data)


async def test_register_user(client, auth_service: AsyncMock) -> None:
    user = make_user()
    auth_service.create_user.return_value = user

    response = await client.post(
        "/auth/users/",
        json={"username": "alice", "email": "alice@example.com", "password": "password123"},
    )

    assert response.status_code == 201
    assert response.json()["username"] == "alice"
    assert response.json()["email"] == "alice@example.com"
    auth_service.create_user.assert_awaited_once()


async def test_register_user_rejects_short_password(client, auth_service: AsyncMock) -> None:
    response = await client.post(
        "/auth/users/",
        json={"username": "alice", "email": "alice@example.com", "password": "short"},
    )

    assert response.status_code == 422
    auth_service.create_user.assert_not_awaited()


async def test_register_user_rejects_invalid_email(client, auth_service: AsyncMock) -> None:
    response = await client.post(
        "/auth/users/",
        json={"username": "alice", "email": "not-an-email", "password": "password123"},
    )

    assert response.status_code == 422
    auth_service.create_user.assert_not_awaited()


async def test_get_me_returns_current_user(authenticated_client, sample_user: UserReadSchema) -> None:
    response = await authenticated_client.get("/auth/users/me")

    assert response.status_code == 200
    assert response.json()["id"] == str(sample_user.id)
    assert response.json()["username"] == sample_user.username


async def test_get_me_requires_authorization(client) -> None:
    response = await client.get("/auth/users/me")

    assert response.status_code == 401


async def test_get_me_rejects_invalid_token(client, auth_service: AsyncMock) -> None:
    auth_service.authenticate_user.side_effect = InvalidTokenError()

    response = await client.get(
        "/auth/users/me",
        headers={"Authorization": "Bearer invalid-token"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Недействительный токен"}


async def test_delete_me(authenticated_client, auth_service: AsyncMock, sample_user: UserReadSchema) -> None:
    response = await authenticated_client.delete("/auth/users/me")

    assert response.status_code == 204
    auth_service.delete_user.assert_awaited_once_with(sample_user.id)


async def test_change_me(authenticated_client, auth_service: AsyncMock, sample_user: UserReadSchema) -> None:
    updated = make_user(id=sample_user.id, username="bob", email="bob@example.com")
    auth_service.change_user.return_value = updated

    response = await authenticated_client.put(
        "/auth/users/me",
        json={"username": "bob", "email": "bob@example.com"},
    )

    assert response.status_code == 200
    assert response.json()["username"] == "bob"
    auth_service.change_user.assert_awaited_once()
    called_current_user, called_data = auth_service.change_user.call_args.args
    assert called_current_user == sample_user
    assert called_data.username == "bob"


async def test_change_me_rejects_invalid_email(authenticated_client, auth_service: AsyncMock) -> None:
    response = await authenticated_client.put(
        "/auth/users/me",
        json={"username": "bob", "email": "not-an-email"},
    )

    assert response.status_code == 422
    auth_service.change_user.assert_not_awaited()
