
import uuid
from datetime import date, datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

import src.services as services_module
from src.config import settings
from src.exceptions import (
    EmailAlreadyExistsError,
    InvalidPasswordError,
    InvalidTokenTypeError,
    TokenBlacklistError,
    UsernameAlreadyExistsError,
    UserNotFoundError,
)
from src.schemas import (
    JWTTokenPairResponseSchema,
    UserCreateSchema,
    UserLoginSchema,
    UserReadSchema,
    UserUpdateSchema,
)
from src.services import AuthService


class FakeUnitOfWork:
    def __init__(self, user_repo: AsyncMock):
        self.user_repo = user_repo
        self.commit = AsyncMock()
        self.rollback = AsyncMock()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        return False


def make_user(**overrides) -> SimpleNamespace:
    data = {
        "id": uuid.uuid4(),
        "username": "alice",
        "email": "alice@example.com",
        "password": "hashed-password",
        "is_admin": False,
        "registration_date": datetime.now(timezone.utc),
    }
    data.update(overrides)
    return SimpleNamespace(**data)


def make_current_user(**overrides) -> UserReadSchema:
    data = {
        "id": uuid.uuid4(),
        "username": "alice",
        "email": "alice@example.com",
        "registration_date": datetime.now(timezone.utc),
    }
    data.update(overrides)
    return UserReadSchema(**data)


@pytest.fixture
def user_repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def uow(user_repo: AsyncMock) -> FakeUnitOfWork:
    return FakeUnitOfWork(user_repo)


@pytest.fixture
def service(uow: FakeUnitOfWork) -> AuthService:
    return AuthService(uow)


@pytest.fixture(autouse=True)
def external(monkeypatch) -> SimpleNamespace:
    mocks = SimpleNamespace(
        hash_password=MagicMock(return_value="hashed-password"),
        verify_password=MagicMock(return_value=True),
        create_access_token=MagicMock(return_value="access-token"),
        create_refresh_token=MagicMock(return_value="refresh-token"),
        decode_token=MagicMock(return_value={}),
        redis_cache=SimpleNamespace(
            set_value=AsyncMock(),
            get_value=AsyncMock(),
            del_key=AsyncMock(),
        ),
        rabbitmq_producer=SimpleNamespace(publish_message=AsyncMock()),
    )

    monkeypatch.setattr(services_module, "hash_password", mocks.hash_password)
    monkeypatch.setattr(services_module, "verify_password", mocks.verify_password)
    monkeypatch.setattr(services_module, "create_access_token", mocks.create_access_token)
    monkeypatch.setattr(services_module, "create_refresh_token", mocks.create_refresh_token)
    monkeypatch.setattr(services_module, "decode_token", mocks.decode_token)
    monkeypatch.setattr(services_module, "redis_cache", mocks.redis_cache)
    monkeypatch.setattr(services_module, "rabbitmq_producer", mocks.rabbitmq_producer)

    return mocks


def create_payload() -> UserCreateSchema:
    return UserCreateSchema(
        username="alice",
        email="alice@example.com",
        password="password123",
    )


async def test_create_user_success(service, uow, user_repo, external) -> None:
    user_repo.get_user_by_username.return_value = None
    user_repo.get_user_by_email.return_value = None
    user_repo.create_user.return_value = make_user()

    result = await service.create_user(create_payload())

    assert isinstance(result, UserReadSchema)
    assert result.username == "alice"
    external.hash_password.assert_called_once_with("password123")
    user_repo.create_user.assert_awaited_once()
    created_data = user_repo.create_user.call_args.args[0]
    assert created_data["password"] == "hashed-password"
    uow.commit.assert_awaited_once()
    external.rabbitmq_producer.publish_message.assert_awaited_once_with(
        routing_key=settings.USER_CREATED_ROUTING_KEY,
        message_body={
            "username": "alice",
            "email": "alice@example.com",
            "event_date": date.today().isoformat(),
        },
    )


async def test_create_user_raises_when_username_taken(service, user_repo, external) -> None:
    user_repo.get_user_by_username.return_value = make_user()

    with pytest.raises(UsernameAlreadyExistsError):
        await service.create_user(create_payload())

    user_repo.create_user.assert_not_awaited()
    external.rabbitmq_producer.publish_message.assert_not_awaited()


async def test_create_user_raises_when_email_taken(service, user_repo, external) -> None:
    user_repo.get_user_by_username.return_value = None
    user_repo.get_user_by_email.return_value = make_user(username="bob", email="alice@example.com")

    with pytest.raises(EmailAlreadyExistsError):
        await service.create_user(create_payload())

    user_repo.create_user.assert_not_awaited()
    external.rabbitmq_producer.publish_message.assert_not_awaited()


async def test_delete_user_success(service, uow, user_repo, external) -> None:
    user = make_user()
    user_repo.get_user_by_id.return_value = user

    await service.delete_user(str(user.id))

    user_repo.delete_user.assert_awaited_once_with(str(user.id))
    uow.commit.assert_awaited_once()
    external.redis_cache.del_key.assert_awaited_once_with(f"users:{user.id}:refresh-token")
    external.rabbitmq_producer.publish_message.assert_awaited_once()
    publish_kwargs = external.rabbitmq_producer.publish_message.call_args.kwargs
    assert publish_kwargs["routing_key"] == settings.USER_DELETED_ROUTING_KEY
    assert publish_kwargs["message_body"]["email"] == user.email


async def test_delete_user_raises_when_not_found(service, user_repo, external) -> None:
    user_repo.get_user_by_id.return_value = None

    with pytest.raises(UserNotFoundError):
        await service.delete_user(str(uuid.uuid4()))

    user_repo.delete_user.assert_not_awaited()
    external.redis_cache.del_key.assert_not_awaited()
    external.rabbitmq_producer.publish_message.assert_not_awaited()


async def test_change_user_updates_username_and_email(service, uow, user_repo) -> None:
    current = make_current_user()
    data = UserUpdateSchema(username="bob", email="bob@example.com")
    user_repo.get_user_by_username.return_value = None
    user_repo.get_user_by_email.return_value = None
    user_repo.update_user.return_value = make_user(
        id=current.id,
        username="bob",
        email="bob@example.com",
    )

    result = await service.change_user(current, data)

    assert result.username == "bob"
    assert result.email == "bob@example.com"
    user_repo.update_user.assert_awaited_once_with(
        current.id,
        {"username": "bob", "email": "bob@example.com"},
    )
    uow.commit.assert_awaited_once()


async def test_change_user_skips_lookups_when_values_unchanged(service, user_repo) -> None:
    current = make_current_user()
    data = UserUpdateSchema(username="alice", email="alice@example.com")
    user_repo.update_user.return_value = make_user(id=current.id)

    await service.change_user(current, data)

    user_repo.get_user_by_username.assert_not_awaited()
    user_repo.get_user_by_email.assert_not_awaited()


async def test_change_user_raises_when_username_taken(service, user_repo) -> None:
    current = make_current_user()
    data = UserUpdateSchema(username="bob", email="alice@example.com")
    user_repo.get_user_by_username.return_value = make_user(username="bob")

    with pytest.raises(UsernameAlreadyExistsError):
        await service.change_user(current, data)

    user_repo.update_user.assert_not_awaited()


async def test_change_user_raises_when_email_taken(service, user_repo) -> None:
    current = make_current_user()
    data = UserUpdateSchema(username="alice", email="bob@example.com")
    user_repo.get_user_by_email.return_value = make_user(username="bob", email="bob@example.com")

    with pytest.raises(EmailAlreadyExistsError):
        await service.change_user(current, data)

    user_repo.update_user.assert_not_awaited()


async def test_get_tokens_success(service, user_repo, external) -> None:
    user = make_user()
    user_repo.get_user_by_username.return_value = user
    external.verify_password.return_value = True

    result = await service.get_tokens(
        UserLoginSchema(username="alice", password="password123")
    )

    assert isinstance(result, JWTTokenPairResponseSchema)
    assert result.access == "access-token"
    assert result.refresh == "refresh-token"
    external.verify_password.assert_called_once_with("password123", user.password)
    expected_user_data = {
        "id": str(user.id),
        "username": "alice",
        "email": "alice@example.com",
        "is_admin": False,
    }
    external.create_access_token.assert_called_once_with(expected_user_data)
    external.create_refresh_token.assert_called_once_with(expected_user_data)
    external.redis_cache.set_value.assert_awaited_once_with(
        f"users:{user.id}:refresh-token",
        "refresh-token",
        settings.REFRESH_TOKEN_LIFETIME_DAYS * 24 * 3600,
    )


async def test_get_tokens_raises_when_user_not_found(service, user_repo, external) -> None:
    user_repo.get_user_by_username.return_value = None

    with pytest.raises(UserNotFoundError):
        await service.get_tokens(UserLoginSchema(username="alice", password="password123"))

    external.verify_password.assert_not_called()


async def test_get_tokens_raises_on_invalid_password(service, user_repo, external) -> None:
    user_repo.get_user_by_username.return_value = make_user()
    external.verify_password.return_value = False

    with pytest.raises(InvalidPasswordError):
        await service.get_tokens(UserLoginSchema(username="alice", password="wrong"))

    external.redis_cache.set_value.assert_not_awaited()


async def test_refresh_token_success(service, external) -> None:
    external.decode_token.return_value = {
        "id": "user-id",
        "username": "alice",
        "email": "alice@example.com",
        "is_admin": False,
        "token_type": "refresh",
    }
    external.redis_cache.get_value.return_value = "old-refresh"

    result = await service.refresh_token("old-refresh")

    assert isinstance(result, JWTTokenPairResponseSchema)
    assert result.access == "access-token"
    assert result.refresh == "refresh-token"
    external.redis_cache.get_value.assert_awaited_once_with("users:user-id:refresh-token")
    external.redis_cache.set_value.assert_awaited_once_with(
        "users:user-id:refresh-token",
        "refresh-token",
        settings.REFRESH_TOKEN_LIFETIME_DAYS * 24 * 3600,
    )


async def test_refresh_token_raises_on_wrong_token_type(service, external) -> None:
    external.decode_token.return_value = {"id": "user-id", "token_type": "access"}

    with pytest.raises(InvalidTokenTypeError):
        await service.refresh_token("access-token")

    external.redis_cache.get_value.assert_not_awaited()


async def test_refresh_token_raises_when_stored_token_differs(service, external) -> None:
    external.decode_token.return_value = {
        "id": "user-id",
        "username": "alice",
        "email": "alice@example.com",
        "is_admin": False,
        "token_type": "refresh",
    }
    external.redis_cache.get_value.return_value = "another-refresh"

    with pytest.raises(TokenBlacklistError):
        await service.refresh_token("old-refresh")

    external.redis_cache.set_value.assert_not_awaited()


async def test_authenticate_user_success(service, user_repo, external) -> None:
    user = make_user()
    external.decode_token.return_value = {"id": str(user.id), "token_type": "access"}
    user_repo.get_user_by_id.return_value = user

    result = await service.authenticate_user("access-token")

    assert isinstance(result, UserReadSchema)
    assert result.id == user.id
    user_repo.get_user_by_id.assert_awaited_once_with(str(user.id))


async def test_authenticate_user_raises_on_wrong_token_type(service, user_repo, external) -> None:
    external.decode_token.return_value = {"id": "user-id", "token_type": "refresh"}

    with pytest.raises(InvalidTokenTypeError):
        await service.authenticate_user("refresh-token")

    user_repo.get_user_by_id.assert_not_awaited()


async def test_authenticate_user_raises_when_not_found(service, user_repo, external) -> None:
    external.decode_token.return_value = {"id": str(uuid.uuid4()), "token_type": "access"}
    user_repo.get_user_by_id.return_value = None

    with pytest.raises(UserNotFoundError):
        await service.authenticate_user("access-token")
