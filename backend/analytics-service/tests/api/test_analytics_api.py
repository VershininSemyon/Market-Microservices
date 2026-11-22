
from unittest.mock import AsyncMock

import pytest

from src.enums import PeriodEnum
from src.schemas import AnalyticsStatsSchema


def stats_payload(stats: AnalyticsStatsSchema) -> dict:
    return stats.model_dump(mode="json")


@pytest.mark.parametrize(
    "period",
    [
        PeriodEnum.DAILY,
        PeriodEnum.WEEKLY,
        PeriodEnum.MONTHLY,
        PeriodEnum.YEARLY,
        PeriodEnum.ALL,
    ],
)
async def test_get_stats_passes_period_to_service(
    admin_client,
    analytics_service: AsyncMock,
    sample_stats: AnalyticsStatsSchema,
    period: PeriodEnum,
) -> None:
    analytics_service.get_analytics_stats.return_value = sample_stats

    response = await admin_client.get(
        "/analytics/stats",
        params={"period": period.value},
    )

    assert response.status_code == 200
    assert response.json() == stats_payload(sample_stats)
    analytics_service.get_analytics_stats.assert_awaited_once_with(period)


async def test_get_stats_returns_distribution(
    admin_client,
    analytics_service: AsyncMock,
    sample_stats: AnalyticsStatsSchema,
) -> None:
    analytics_service.get_analytics_stats.return_value = sample_stats

    response = await admin_client.get(
        "/analytics/stats",
        params={"period": "all"},
    )

    body = response.json()
    assert body["distribution"]["user"]["created"] == 3
    assert body["distribution"]["product"]["deleted"] == 1
    assert body["distribution"]["review"]["deleted"] == 4
    assert body["total_created"] == 10
    assert body["total_deleted"] == 5


async def test_get_stats_requires_authorization(
    client,
    analytics_service: AsyncMock,
) -> None:
    response = await client.get("/analytics/stats", params={"period": "daily"})

    assert response.status_code == 401
    analytics_service.get_analytics_stats.assert_not_awaited()


async def test_get_stats_forbids_non_admin(
    regular_client,
    analytics_service: AsyncMock,
) -> None:
    response = await regular_client.get(
        "/analytics/stats",
        params={"period": "daily"},
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "Доступ запрещён"}
    analytics_service.get_analytics_stats.assert_not_awaited()


async def test_get_stats_requires_period(
    admin_client,
    analytics_service: AsyncMock,
) -> None:
    response = await admin_client.get("/analytics/stats")

    assert response.status_code == 422
    analytics_service.get_analytics_stats.assert_not_awaited()


async def test_get_stats_rejects_invalid_period(
    admin_client,
    analytics_service: AsyncMock,
) -> None:
    response = await admin_client.get(
        "/analytics/stats",
        params={"period": "hourly"},
    )

    assert response.status_code == 422
    analytics_service.get_analytics_stats.assert_not_awaited()
