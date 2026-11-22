
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.unitofwork import UnitOfWork


@pytest.fixture
def session() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def session_factory(session: AsyncMock) -> MagicMock:
    return MagicMock(return_value=session)


async def test_aenter_creates_session_and_repository(session_factory, session) -> None:
    uow = UnitOfWork(session_factory)

    async with uow:
        assert uow.session is session
        assert uow.product_repo.session is session

    session_factory.assert_called_once_with()


async def test_aexit_closes_session_without_rollback(session_factory, session) -> None:
    uow = UnitOfWork(session_factory)

    async with uow:
        pass

    session.rollback.assert_not_awaited()
    session.close.assert_awaited_once()


async def test_aexit_rolls_back_and_closes_on_exception(session_factory, session) -> None:
    uow = UnitOfWork(session_factory)

    with pytest.raises(ValueError):
        async with uow:
            raise ValueError("boom")

    session.rollback.assert_awaited_once()
    session.close.assert_awaited_once()


async def test_commit_delegates_to_session(session_factory, session) -> None:
    uow = UnitOfWork(session_factory)

    async with uow:
        await uow.commit()

    session.commit.assert_awaited_once()


async def test_rollback_delegates_to_session(session_factory, session) -> None:
    uow = UnitOfWork(session_factory)

    async with uow:
        await uow.rollback()

    session.rollback.assert_awaited_once()


async def test_commit_persists_changes(db_session_factory) -> None:
    uow = UnitOfWork(db_session_factory)

    async with uow:
        await uow.product_repo.create_product(
            {
                "name": "apple",
                "description": "green apple",
                "price": 10.0,
                "quantity": 5,
                "is_active": True,
            }
        )
        await uow.commit()

    verification_uow = UnitOfWork(db_session_factory)
    async with verification_uow:
        product = await verification_uow.product_repo.get_product_by_name("apple")

    assert product is not None
    assert product.price == 10.0


async def test_uncommitted_changes_are_rolled_back_on_exit(db_session_factory) -> None:
    uow = UnitOfWork(db_session_factory)

    async with uow:
        await uow.product_repo.create_product(
            {
                "name": "apple",
                "description": "green apple",
                "price": 10.0,
                "quantity": 5,
                "is_active": True,
            }
        )

    verification_uow = UnitOfWork(db_session_factory)
    async with verification_uow:
        product = await verification_uow.product_repo.get_product_by_name("apple")

    assert product is None
