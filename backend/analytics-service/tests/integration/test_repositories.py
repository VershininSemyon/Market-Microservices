
from datetime import date, timedelta

from sqlalchemy import func, select

from src.enums import EntityTypeEnum, EventTypeEnum, PeriodEnum
from src.models import DayAnalyticsORM
from src.repositories import DayAnalyticsRepository


async def count_rows(db_session) -> int:
    result = await db_session.execute(
        select(func.count()).select_from(DayAnalyticsORM)
    )
    return result.scalar_one()


async def test_create_day_analytics_inserts_first_record(db_session) -> None:
    repo = DayAnalyticsRepository(db_session)
    day = date(2026, 1, 1)

    record = await repo.create_day_analytics(
        EntityTypeEnum.PRODUCT,
        EventTypeEnum.CREATED,
        day,
    )
    await db_session.commit()

    assert record.id is not None
    assert record.entity_type == EntityTypeEnum.PRODUCT
    assert record.event_type == EventTypeEnum.CREATED
    assert record.occurred_at == day
    assert record.count == 1
    assert await count_rows(db_session) == 1


async def test_create_day_analytics_increments_existing_record(db_session) -> None:
    repo = DayAnalyticsRepository(db_session)
    day = date(2026, 1, 1)

    await repo.create_day_analytics(EntityTypeEnum.USER, EventTypeEnum.CREATED, day)
    await db_session.commit()
    updated = await repo.create_day_analytics(EntityTypeEnum.USER, EventTypeEnum.CREATED, day)
    await db_session.commit()

    assert updated.count == 2
    assert await count_rows(db_session) == 1


async def test_create_day_analytics_keeps_days_separate(db_session) -> None:
    repo = DayAnalyticsRepository(db_session)

    await repo.create_day_analytics(EntityTypeEnum.USER, EventTypeEnum.CREATED, date(2026, 1, 1))
    await repo.create_day_analytics(EntityTypeEnum.USER, EventTypeEnum.CREATED, date(2026, 1, 2))
    await db_session.commit()

    assert await count_rows(db_session) == 2


async def test_create_day_analytics_keeps_entity_and_event_separate(db_session) -> None:
    repo = DayAnalyticsRepository(db_session)
    day = date(2026, 1, 1)

    await repo.create_day_analytics(EntityTypeEnum.USER, EventTypeEnum.CREATED, day)
    await repo.create_day_analytics(EntityTypeEnum.USER, EventTypeEnum.DELETED, day)
    await repo.create_day_analytics(EntityTypeEnum.PRODUCT, EventTypeEnum.CREATED, day)
    await db_session.commit()

    assert await count_rows(db_session) == 3


async def test_get_stats_all_groups_and_sums(db_session) -> None:
    repo = DayAnalyticsRepository(db_session)
    today = date.today()

    await repo.create_day_analytics(EntityTypeEnum.USER, EventTypeEnum.CREATED, today)
    await repo.create_day_analytics(EntityTypeEnum.USER, EventTypeEnum.CREATED, today)
    await repo.create_day_analytics(
        EntityTypeEnum.USER,
        EventTypeEnum.CREATED,
        today - timedelta(days=500),
    )
    await repo.create_day_analytics(
        EntityTypeEnum.PRODUCT,
        EventTypeEnum.DELETED,
        today,
    )
    await db_session.commit()

    rows = await repo.get_stats(PeriodEnum.ALL)
    stats = {(entity, event): total for entity, event, total in rows}

    assert stats == {
        (EntityTypeEnum.USER, EventTypeEnum.CREATED): 3,
        (EntityTypeEnum.PRODUCT, EventTypeEnum.DELETED): 1,
    }


async def test_get_stats_daily_only_includes_today(db_session) -> None:
    repo = DayAnalyticsRepository(db_session)
    today = date.today()

    await repo.create_day_analytics(EntityTypeEnum.REVIEW, EventTypeEnum.CREATED, today)
    await repo.create_day_analytics(
        EntityTypeEnum.REVIEW,
        EventTypeEnum.CREATED,
        today - timedelta(days=1),
    )
    await db_session.commit()

    rows = await repo.get_stats(PeriodEnum.DAILY)
    stats = {(entity, event): total for entity, event, total in rows}

    assert stats == {(EntityTypeEnum.REVIEW, EventTypeEnum.CREATED): 1}


async def test_get_stats_weekly_includes_last_seven_days(db_session) -> None:
    repo = DayAnalyticsRepository(db_session)
    today = date.today()

    await repo.create_day_analytics(
        EntityTypeEnum.ORDER,
        EventTypeEnum.CREATED,
        today - timedelta(days=7),
    )
    await repo.create_day_analytics(
        EntityTypeEnum.ORDER,
        EventTypeEnum.CREATED,
        today - timedelta(days=8),
    )
    await db_session.commit()

    rows = await repo.get_stats(PeriodEnum.WEEKLY)
    stats = {(entity, event): total for entity, event, total in rows}

    assert stats == {(EntityTypeEnum.ORDER, EventTypeEnum.CREATED): 1}


async def test_get_stats_monthly_includes_last_thirty_days(db_session) -> None:
    repo = DayAnalyticsRepository(db_session)
    today = date.today()

    await repo.create_day_analytics(
        EntityTypeEnum.USER,
        EventTypeEnum.DELETED,
        today - timedelta(days=30),
    )
    await repo.create_day_analytics(
        EntityTypeEnum.USER,
        EventTypeEnum.DELETED,
        today - timedelta(days=31),
    )
    await db_session.commit()

    rows = await repo.get_stats(PeriodEnum.MONTHLY)
    stats = {(entity, event): total for entity, event, total in rows}

    assert stats == {(EntityTypeEnum.USER, EventTypeEnum.DELETED): 1}


async def test_get_stats_yearly_includes_last_three_hundred_sixty_five_days(db_session) -> None:
    repo = DayAnalyticsRepository(db_session)
    today = date.today()

    await repo.create_day_analytics(
        EntityTypeEnum.PRODUCT,
        EventTypeEnum.CREATED,
        today - timedelta(days=365),
    )
    await repo.create_day_analytics(
        EntityTypeEnum.PRODUCT,
        EventTypeEnum.CREATED,
        today - timedelta(days=366),
    )
    await db_session.commit()

    rows = await repo.get_stats(PeriodEnum.YEARLY)
    stats = {(entity, event): total for entity, event, total in rows}

    assert stats == {(EntityTypeEnum.PRODUCT, EventTypeEnum.CREATED): 1}


async def test_get_stats_returns_empty_list_without_data(db_session) -> None:
    repo = DayAnalyticsRepository(db_session)

    assert await repo.get_stats(PeriodEnum.ALL) == []
