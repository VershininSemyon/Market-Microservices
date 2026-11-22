
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

from main import app
from src.dependencies import get_current_user, get_product_service
from src.jwt import TokenData
from src.schemas import ProductReadSchema


@pytest.fixture
def product_service() -> AsyncMock:
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
        username="bob",
        email="bob@example.com",
        is_admin=False,
    )


@pytest.fixture
def sample_product() -> ProductReadSchema:
    return ProductReadSchema(
        id=uuid.uuid4(),
        name="apple",
        description="green apple",
        price=10.0,
        quantity=5,
        is_active=True,
        created_at=datetime.now(timezone.utc),
    )


@pytest.fixture
async def client(product_service: AsyncMock):
    app.dependency_overrides[get_product_service] = lambda: product_service
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
async def user_client(client: AsyncClient, regular_user: TokenData):
    app.dependency_overrides[get_current_user] = lambda: regular_user
    try:
        yield client
    finally:
        app.dependency_overrides.pop(get_current_user, None)
