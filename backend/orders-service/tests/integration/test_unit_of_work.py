
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.models import ExchangeTypeEnum
from src.unitofwork import UnitOfWork


@pytest.fixture
def session() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def session_factory(session: AsyncMock) -> MagicMock:
    return MagicMock(return_value=session)


async def test_aenter_creates_session_and_repositories(session_factory, session) -> None:
    uow = UnitOfWork(session_factory)

    async with uow:
        assert uow.session is session
        assert uow.order_repo.session is session
        assert uow.outbox_repo.session is session

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


async def test_commit_persists_order_and_outbox_event(db_session_factory) -> None:
    user_id = uuid.uuid4()
    uow = UnitOfWork(db_session_factory)

    async with uow:
        order = await uow.order_repo.create_order(
            {
                "user_id": user_id,
                "products": {
                    str(uuid.uuid4()): {"name": "apple", "price": 10.0, "quantity": 2}
                },
                "total_price": 20.0,
                "total_amount": 2,
            }
        )
        await uow.outbox_repo.create_outbox_event(
            {
                "exchange_name": "orders-events-exchange",
                "exchange_type": ExchangeTypeEnum.TOPIC,
                "routing_key": "order.created",
                "event_payload": {"event_id": str(uuid.uuid4())},
            }
        )
        await uow.commit()

    verification_uow = UnitOfWork(db_session_factory)
    async with verification_uow:
        stored_order = await verification_uow.order_repo.get_order_by_id(order.id)
        events = await verification_uow.outbox_repo.get_last_outbox_events(10)

    assert stored_order is not None
    assert stored_order.user_id == user_id
    assert len(events) == 1


async def test_uncommitted_changes_are_rolled_back_on_exit(db_session_factory) -> None:
    user_id = uuid.uuid4()
    uow = UnitOfWork(db_session_factory)

    async with uow:
        await uow.order_repo.create_order(
            {
                "user_id": user_id,
                "products": {},
                "total_price": 20.0,
                "total_amount": 2,
            }
        )

    verification_uow = UnitOfWork(db_session_factory)
    async with verification_uow:
        orders = await verification_uow.order_repo.get_orders_by_user_id(user_id)

    assert orders == []
