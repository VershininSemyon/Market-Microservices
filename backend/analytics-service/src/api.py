
from fastapi import APIRouter, Depends, status

from src.dependencies import AnalyticsServiceDep, require_admin
from src.enums import PeriodEnum
from src.schemas import AnalyticsStatsSchema

analytics_router = APIRouter(prefix="/analytics", tags=["Analytics"])


@analytics_router.get(
    "/stats",
    status_code=status.HTTP_200_OK,
    response_model=AnalyticsStatsSchema,
    dependencies=[Depends(require_admin)]
)
async def get_stats(
    period: PeriodEnum,
    analytics_service: AnalyticsServiceDep
) -> AnalyticsStatsSchema:
    return await analytics_service.get_analytics_stats(period)
