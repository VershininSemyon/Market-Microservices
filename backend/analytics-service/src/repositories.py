
from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.enums import EntityTypeEnum, EventTypeEnum, PeriodEnum
from src.models import DayAnalyticsORM


class DayAnalyticsRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_day_analytics(
        self,
        entity_type: EntityTypeEnum,
        event_type: EventTypeEnum,
        day: date
    ) -> DayAnalyticsORM:
        stmt = select(DayAnalyticsORM).where(
            DayAnalyticsORM.entity_type == entity_type,
            DayAnalyticsORM.event_type == event_type,
            DayAnalyticsORM.occurred_at == day
        )
        result = await self.session.execute(stmt)
        analytics_obj = result.scalar_one_or_none()

        if analytics_obj:
            analytics_obj.count += 1
            return analytics_obj

        new_analytics = DayAnalyticsORM(
            entity_type=entity_type,
            event_type=event_type,
            occurred_at=day,
            count=1
        )
        self.session.add(new_analytics)
        return new_analytics

    async def get_stats(self, period: PeriodEnum):
        start_date = {
            PeriodEnum.DAILY: date.today(),
            PeriodEnum.WEEKLY: date.today() - timedelta(days=7),
            PeriodEnum.MONTHLY: date.today() - timedelta(days=30),
            PeriodEnum.YEARLY: date.today() - timedelta(days=365)
        }

        stmt = select(
            DayAnalyticsORM.entity_type,
            DayAnalyticsORM.event_type,
            func.sum(DayAnalyticsORM.count).label("total_count")
        )

        if period != PeriodEnum.ALL:
            stmt = stmt.where(DayAnalyticsORM.occurred_at >= start_date[period])

        stmt = stmt.group_by(
            DayAnalyticsORM.entity_type,
            DayAnalyticsORM.event_type
        )

        result = await self.session.execute(stmt)
        return result.all()
