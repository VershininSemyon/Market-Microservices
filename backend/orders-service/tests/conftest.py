
import os

os.environ.update(
    {
        "ORDERS_SERVICE_POSTGRES_DB_NAME": "orders_test",
        "ORDERS_SERVICE_POSTGRES_USER": "orders_test",
        "ORDERS_SERVICE_POSTGRES_PASSWORD": "orders_test",
        "ORDERS_SERVICE_POSTGRES_HOST": "localhost",
        "ORDERS_SERVICE_POSTGRES_PORT": "5432",
        "RABBITMQ_USER": "guest",
        "RABBITMQ_PASSWORD": "guest",
        "RABBITMQ_HOST": "localhost",
        "RABBITMQ_PORT": "5672",
        "JWT_ALGORITHM": "HS256",
        "JWT_PUBLIC_KEY": "test-secret-key-for-orders-service-tests",
        "PRODUCTS_SERVICE_URL": "http://products-test:8002",
        "MAX_ATTEMPTS": "3",
        "RETRY_PAUSE_SECONDS": "0",
        "CONNECT_TIMEOUT": "1",
        "REQUEST_TIMEOUT": "1",
    }
)

import pytest
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.pool import StaticPool

import src.models  # noqa: F401
from src.database import Base


@compiles(JSONB, "sqlite")
def compile_jsonb_for_sqlite(type_, compiler, **kwargs) -> str:
    return "JSON"


@pytest.fixture
async def db_session_factory():
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    try:
        yield session_factory
    finally:
        await engine.dispose()


@pytest.fixture
async def db_session(db_session_factory):
    async with db_session_factory() as session:
        yield session
