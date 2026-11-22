
import uuid
from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

from main import app
from src.dependencies import get_analytics_service, get_current_user
from src.enums import EntityTypeEnum, EventTypeEnum
from src.jwt import TokenData
from src.schemas import AnalyticsStatsSchema


def build_stats() -> AnalyticsStatsSchema:
    distribution = {
        entity: {event: 0 for event in EventTypeEnum}
        for entity in EntityTypeEnum
    }
    distribution[EntityTypeEnum.USER][EventTypeEnum.CREATED] = 3
    distribution[EntityTypeEnum.PRODUCT][EventTypeEnum.CREATED] = 2
    distribution[EntityTypeEnum.PRODUCT][EventTypeEnum.DELETED] = 1
    distribution[EntityTypeEnum.REVIEW][EventTypeEnum.DELETED] = 4
    distribution[EntityTypeEnum.ORDER][EventTypeEnum.CREATED] = 5

    return AnalyticsStatsSchema(
        distribution=distribution,
        total_created=10,
        total_deleted=5,
    )


@pytest.fixture
def analytics_service() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def admin_user() -> TokenData:
    return TokenData(
        id=uuid.uuid4(),
        username="admin",
        email="admin@example.com",
        is_admin=True,
    )


@pytest.fixture
def regular_user() -> TokenData:
    return TokenData(
        id=uuid.uuid4(),
        username="alice",
        email="alice@example.com",
        is_admin=False,
    )


@pytest.fixture
def sample_stats() -> AnalyticsStatsSchema:
    return build_stats()


@pytest.fixture
async def client(analytics_service: AsyncMock):
    app.dependency_overrides[get_analytics_service] = lambda: analytics_service
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as async_client:
            yield async_client
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
async def admin_client(client: AsyncClient, admin_user: TokenData):
    app.dependency_overrides[get_current_user] = lambda: admin_user
    try:
        yield client
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
async def regular_client(client: AsyncClient, regular_user: TokenData):
    app.dependency_overrides[get_current_user] = lambda: regular_user
    try:
        yield client
    finally:
        app.dependency_overrides.pop(get_current_user, None)
