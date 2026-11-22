
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

import src.outbox_scheduler as scheduler_module


class FakeUnitOfWork:
    def __init__(self, outbox_repo: AsyncMock):
        self.outbox_repo = outbox_repo
        self.commit = AsyncMock()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        return False


def make_event_payload(**overrides) -> dict:
    data = {
        "event_id": str(uuid.uuid4()),
        "total_amount": 2,
        "total_price": 20.0,
        "products": [{"id": str(uuid.uuid4()), "quantity": 2}],
        "event_date": "2026-01-01",
        "user_email": "alice@example.com",
    }
    data.update(overrides)
    return data


def make_event(**overrides) -> SimpleNamespace:
    data = {
        "id": uuid.uuid4(),
        "event_payload": make_event_payload(),
    }
    data.update(overrides)
    return SimpleNamespace(**data)


@pytest.fixture
def dependencies(monkeypatch) -> SimpleNamespace:
    repo = AsyncMock()
    uow = FakeUnitOfWork(repo)
    uow_factory = MagicMock(return_value=uow)
    publish = AsyncMock()

    monkeypatch.setattr(scheduler_module, "UnitOfWork", uow_factory)
    monkeypatch.setattr(scheduler_module, "publish_order_created_event", publish)

    return SimpleNamespace(
        repo=repo,
        uow=uow,
        uow_factory=uow_factory,
        publish=publish,
    )


async def test_process_outbox_returns_without_events(dependencies) -> None:
    dependencies.repo.get_last_outbox_events.return_value = []

    await scheduler_module.process_outbox()

    dependencies.repo.get_last_outbox_events.assert_awaited_once_with(10)
    dependencies.publish.assert_not_awaited()
    dependencies.repo.delete_outbox_events.assert_not_awaited()
    dependencies.uow.commit.assert_not_awaited()


async def test_process_outbox_publishes_and_deletes_events(dependencies) -> None:
    first = make_event()
    second = make_event()
    dependencies.repo.get_last_outbox_events.return_value = [first, second]

    await scheduler_module.process_outbox()

    assert dependencies.publish.await_count == 2
    dependencies.repo.delete_outbox_events.assert_awaited_once_with([first.id, second.id])
    dependencies.uow.commit.assert_awaited_once()


async def test_process_outbox_skips_invalid_payload(dependencies) -> None:
    invalid = make_event(event_payload={})
    valid = make_event()
    dependencies.repo.get_last_outbox_events.return_value = [invalid, valid]

    await scheduler_module.process_outbox()

    dependencies.publish.assert_awaited_once()
    dependencies.repo.delete_outbox_events.assert_awaited_once_with([valid.id])
    dependencies.uow.commit.assert_awaited_once()


async def test_process_outbox_skips_failed_publish(dependencies) -> None:
    failed = make_event()
    valid = make_event()
    dependencies.repo.get_last_outbox_events.return_value = [failed, valid]
    dependencies.publish.side_effect = [RuntimeError("boom"), None]

    await scheduler_module.process_outbox()

    dependencies.repo.delete_outbox_events.assert_awaited_once_with([valid.id])
    dependencies.uow.commit.assert_awaited_once()


async def test_process_outbox_does_not_commit_when_all_fail(dependencies) -> None:
    dependencies.repo.get_last_outbox_events.return_value = [
        make_event(event_payload={}),
        make_event(event_payload={}),
    ]

    await scheduler_module.process_outbox()

    dependencies.publish.assert_not_awaited()
    dependencies.repo.delete_outbox_events.assert_not_awaited()
    dependencies.uow.commit.assert_not_awaited()
