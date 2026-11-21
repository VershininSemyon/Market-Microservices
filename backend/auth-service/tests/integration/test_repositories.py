
import uuid

from src.repositories import UserRepository


def make_user_data(**overrides) -> dict:
    data = {
        "username": "alice",
        "email": "alice@example.com",
        "password": "hashed-password",
        "is_admin": False,
    }
    data.update(overrides)
    return data


async def test_create_user_returns_persisted_entity(db_session) -> None:
    repo = UserRepository(db_session)

    created = await repo.create_user(make_user_data())
    await db_session.commit()

    assert created is not None
    assert isinstance(created.id, uuid.UUID)
    assert created.username == "alice"
    assert created.registration_date is not None


async def test_get_user_by_id(db_session) -> None:
    repo = UserRepository(db_session)
    created = await repo.create_user(make_user_data())
    await db_session.commit()

    fetched = await repo.get_user_by_id(created.id)

    assert fetched is not None
    assert fetched.id == created.id
    assert fetched.email == "alice@example.com"


async def test_get_user_by_id_returns_none_for_unknown_id(db_session) -> None:
    repo = UserRepository(db_session)

    assert await repo.get_user_by_id(uuid.uuid4()) is None


async def test_get_user_by_username(db_session) -> None:
    repo = UserRepository(db_session)
    await repo.create_user(make_user_data())
    await db_session.commit()

    fetched = await repo.get_user_by_username("alice")

    assert fetched is not None
    assert fetched.username == "alice"


async def test_get_user_by_username_returns_none_for_unknown_username(db_session) -> None:
    repo = UserRepository(db_session)

    assert await repo.get_user_by_username("unknown") is None


async def test_get_user_by_email(db_session) -> None:
    repo = UserRepository(db_session)
    await repo.create_user(make_user_data())
    await db_session.commit()

    fetched = await repo.get_user_by_email("alice@example.com")

    assert fetched is not None
    assert fetched.username == "alice"


async def test_get_user_by_email_returns_none_for_unknown_email(db_session) -> None:
    repo = UserRepository(db_session)

    assert await repo.get_user_by_email("unknown@example.com") is None


async def test_update_user_changes_fields(db_session) -> None:
    repo = UserRepository(db_session)
    created = await repo.create_user(make_user_data())
    await db_session.commit()

    updated = await repo.update_user(
        created.id,
        {"username": "bob", "email": "bob@example.com"},
    )
    await db_session.commit()

    assert updated is not None
    assert updated.id == created.id
    assert updated.username == "bob"
    assert updated.email == "bob@example.com"


async def test_update_user_returns_none_for_unknown_id(db_session) -> None:
    repo = UserRepository(db_session)

    assert await repo.update_user(uuid.uuid4(), {"username": "bob"}) is None


async def test_delete_user_removes_entity(db_session) -> None:
    repo = UserRepository(db_session)
    created = await repo.create_user(make_user_data())
    await db_session.commit()

    await repo.delete_user(created.id)
    await db_session.commit()

    assert await repo.get_user_by_id(created.id) is None


async def test_delete_unknown_user_does_not_raise(db_session) -> None:
    repo = UserRepository(db_session)

    await repo.delete_user(uuid.uuid4())
    await db_session.commit()
