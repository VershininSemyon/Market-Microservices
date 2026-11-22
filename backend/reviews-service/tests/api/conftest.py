
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

from main import app
from src.dependencies import get_current_user, get_review_service
from src.jwt import TokenData
from src.schemas import ReviewReadSchema

COMMENT = "This is a very good product"


@pytest.fixture
def review_service() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def current_user() -> TokenData:
    return TokenData(
        id=uuid.uuid4(),
        username="alice",
        email="alice@example.com",
        is_admin=False,
    )


@pytest.fixture
def sample_review() -> ReviewReadSchema:
    return ReviewReadSchema(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        product_id=uuid.uuid4(),
        rating=8,
        comment=COMMENT,
        created_at=datetime.now(timezone.utc),
    )


@pytest.fixture
async def client(review_service: AsyncMock):
    app.dependency_overrides[get_review_service] = lambda: review_service
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as async_client:
            yield async_client
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
async def authenticated_client(client: AsyncClient, current_user: TokenData):
    app.dependency_overrides[get_current_user] = lambda: current_user
    try:
        yield client
    finally:
        app.dependency_overrides.pop(get_current_user, None)
