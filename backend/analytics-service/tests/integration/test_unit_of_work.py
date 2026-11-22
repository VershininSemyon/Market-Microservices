
from datetime import date
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.enums import EntityTypeEnum, EventTypeEnum, PeriodEnum
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
        assert uow.day_analytics_repo.session is session

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


async def test_commit_persists_analytics(db_session_factory) -> None:
    uow = UnitOfWork(db_session_factory)

    async with uow:
        await uow.day_analytics_repo.create_day_analytics(
            EntityTypeEnum.PRODUCT,
            EventTypeEnum.CREATED,
            date(2026, 1, 1),
        )
        await uow.commit()

    verification_uow = UnitOfWork(db_session_factory)
    async with verification_uow:
        rows = await verification_uow.day_analytics_repo.get_stats(PeriodEnum.ALL)

    assert len(rows) == 1
    entity_type, event_type, total = rows[0]
    assert entity_type == EntityTypeEnum.PRODUCT
    assert event_type == EventTypeEnum.CREATED
    assert total == 1


async def test_uncommitted_changes_are_rolled_back_on_exit(db_session_factory) -> None:
    uow = UnitOfWork(db_session_factory)

    async with uow:
        await uow.day_analytics_repo.create_day_analytics(
            EntityTypeEnum.USER,
            EventTypeEnum.CREATED,
            date(2026, 1, 1),
        )

    verification_uow = UnitOfWork(db_session_factory)
    async with verification_uow:
        rows = await verification_uow.day_analytics_repo.get_stats(PeriodEnum.ALL)

    assert rows == []
