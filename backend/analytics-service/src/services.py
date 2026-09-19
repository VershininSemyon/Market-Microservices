
from datetime import date

from src.enums import EntityTypeEnum, EventTypeEnum, PeriodEnum
from src.schemas import AnalyticsStatsSchema
from src.unitofwork import UnitOfWork


class AnalyticsService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def add_analytics(
        self,
        entity_type: EntityTypeEnum,
        event_type: EventTypeEnum,
        day: date
    ) -> None:
        async with self.uow:
            await self.uow.day_analytics_repo.create_day_analytics(
                entity_type=entity_type,
                event_type=event_type,
                day=day
            )
            await self.uow.commit()

    async def get_analytics_stats(self, period: PeriodEnum) -> AnalyticsStatsSchema:
        result = {
            entity: {event: 0 for event in EventTypeEnum}
            for entity in EntityTypeEnum
        }

        async with self.uow:
            data = await self.uow.day_analytics_repo.get_stats(period)

        for entity_type, event_type, count in data:
            result[entity_type][event_type] = count

        total_created = sum(result[entity_type][EventTypeEnum.CREATED] for entity_type in result)
        total_deleted = sum(result[entity_type][EventTypeEnum.DELETED] for entity_type in result)

        return AnalyticsStatsSchema(
            distribution=result,
            total_created=total_created,
            total_deleted=total_deleted
        )
