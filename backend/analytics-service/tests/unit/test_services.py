
from datetime import date
from unittest.mock import AsyncMock

import pytest

from src.enums import EntityTypeEnum, EventTypeEnum, PeriodEnum
from src.schemas import AnalyticsStatsSchema
from src.services import AnalyticsService


class FakeUnitOfWork:
    def __init__(self, day_analytics_repo: AsyncMock):
        self.day_analytics_repo = day_analytics_repo
        self.commit = AsyncMock()
        self.rollback = AsyncMock()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        return False


@pytest.fixture
def day_analytics_repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def uow(day_analytics_repo: AsyncMock) -> FakeUnitOfWork:
    return FakeUnitOfWork(day_analytics_repo)


@pytest.fixture
def service(uow: FakeUnitOfWork) -> AnalyticsService:
    return AnalyticsService(uow)


async def test_add_analytics_creates_record_and_commits(
    service: AnalyticsService,
    uow: FakeUnitOfWork,
    day_analytics_repo: AsyncMock,
) -> None:
    day = date(2026, 1, 1)

    await service.add_analytics(EntityTypeEnum.PRODUCT, EventTypeEnum.CREATED, day)

    day_analytics_repo.create_day_analytics.assert_awaited_once_with(
        entity_type=EntityTypeEnum.PRODUCT,
        event_type=EventTypeEnum.CREATED,
        day=day,
    )
    uow.commit.assert_awaited_once()


async def test_add_analytics_does_not_commit_when_repository_fails(
    service: AnalyticsService,
    uow: FakeUnitOfWork,
    day_analytics_repo: AsyncMock,
) -> None:
    day_analytics_repo.create_day_analytics.side_effect = RuntimeError("boom")

    with pytest.raises(RuntimeError):
        await service.add_analytics(
            EntityTypeEnum.USER,
            EventTypeEnum.DELETED,
            date(2026, 1, 1),
        )

    uow.commit.assert_not_awaited()


async def test_get_analytics_stats_builds_distribution_and_totals(
    service: AnalyticsService,
    day_analytics_repo: AsyncMock,
) -> None:
    day_analytics_repo.get_stats.return_value = [
        (EntityTypeEnum.USER, EventTypeEnum.CREATED, 3),
        (EntityTypeEnum.PRODUCT, EventTypeEnum.CREATED, 2),
        (EntityTypeEnum.PRODUCT, EventTypeEnum.DELETED, 1),
        (EntityTypeEnum.REVIEW, EventTypeEnum.DELETED, 4),
        (EntityTypeEnum.ORDER, EventTypeEnum.CREATED, 5),
    ]

    stats = await service.get_analytics_stats(PeriodEnum.WEEKLY)

    assert isinstance(stats, AnalyticsStatsSchema)
    day_analytics_repo.get_stats.assert_awaited_once_with(PeriodEnum.WEEKLY)
    assert stats.distribution[EntityTypeEnum.USER][EventTypeEnum.CREATED] == 3
    assert stats.distribution[EntityTypeEnum.PRODUCT][EventTypeEnum.CREATED] == 2
    assert stats.distribution[EntityTypeEnum.PRODUCT][EventTypeEnum.DELETED] == 1
    assert stats.distribution[EntityTypeEnum.REVIEW][EventTypeEnum.DELETED] == 4
    assert stats.distribution[EntityTypeEnum.ORDER][EventTypeEnum.CREATED] == 5
    assert stats.total_created == 10
    assert stats.total_deleted == 5


async def test_get_analytics_stats_initializes_all_combinations_with_zero(
    service: AnalyticsService,
    day_analytics_repo: AsyncMock,
) -> None:
    day_analytics_repo.get_stats.return_value = [
        (EntityTypeEnum.USER, EventTypeEnum.CREATED, 2),
    ]

    stats = await service.get_analytics_stats(PeriodEnum.ALL)

    for entity_type in EntityTypeEnum:
        for event_type in EventTypeEnum:
            assert entity_type in stats.distribution
            assert event_type in stats.distribution[entity_type]

    assert stats.distribution[EntityTypeEnum.USER][EventTypeEnum.DELETED] == 0
    assert stats.distribution[EntityTypeEnum.PRODUCT][EventTypeEnum.CREATED] == 0
    assert stats.total_created == 2
    assert stats.total_deleted == 0


async def test_get_analytics_stats_with_no_data(
    service: AnalyticsService,
    day_analytics_repo: AsyncMock,
) -> None:
    day_analytics_repo.get_stats.return_value = []

    stats = await service.get_analytics_stats(PeriodEnum.DAILY)

    assert stats.total_created == 0
    assert stats.total_deleted == 0
    assert all(
        count == 0
        for events in stats.distribution.values()
        for count in events.values()
    )


async def test_get_analytics_stats_uses_fresh_uow_context_per_call(
    service: AnalyticsService,
    day_analytics_repo: AsyncMock,
) -> None:
    day_analytics_repo.get_stats.return_value = []

    await service.get_analytics_stats(PeriodEnum.MONTHLY)
    await service.get_analytics_stats(PeriodEnum.YEARLY)

    assert day_analytics_repo.get_stats.await_count == 2
    assert day_analytics_repo.get_stats.await_args_list[0].args == (PeriodEnum.MONTHLY,)
    assert day_analytics_repo.get_stats.await_args_list[1].args == (PeriodEnum.YEARLY,)
