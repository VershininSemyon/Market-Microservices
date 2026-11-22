
import os

os.environ.update(
    {
        "ANALYTICS_SERVICE_POSTGRES_DB_NAME": "analytics_test",
        "ANALYTICS_SERVICE_POSTGRES_USER": "analytics_test",
        "ANALYTICS_SERVICE_POSTGRES_PASSWORD": "analytics_test",
        "ANALYTICS_SERVICE_POSTGRES_HOST": "localhost",
        "ANALYTICS_SERVICE_POSTGRES_PORT": "5432",
        "RABBITMQ_USER": "guest",
        "RABBITMQ_PASSWORD": "guest",
        "RABBITMQ_HOST": "localhost",
        "RABBITMQ_PORT": "5672",
        "JWT_ALGORITHM": "HS256",
        "JWT_PUBLIC_KEY": "test-secret-key-for-analytics-service-tests",
    }
)

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

import src.models
from src.database import Base


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
