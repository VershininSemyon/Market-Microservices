
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

from main import app
from src.dependencies import get_auth_service, get_current_user
from src.schemas import UserReadSchema


@pytest.fixture
def auth_service() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def sample_user() -> UserReadSchema:
    return UserReadSchema(
        id=uuid.uuid4(),
        username="alice",
        email="alice@example.com",
        registration_date=datetime.now(timezone.utc),
    )


@pytest.fixture
async def client(auth_service: AsyncMock):
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as async_client:
            yield async_client
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
async def authenticated_client(client: AsyncClient, sample_user: UserReadSchema):
    app.dependency_overrides[get_current_user] = lambda: sample_user
    try:
        yield client
    finally:
        app.dependency_overrides.pop(get_current_user, None)
