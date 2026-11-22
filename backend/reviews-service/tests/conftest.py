
import os

os.environ.update(
    {
        "REVIEWS_SERVICE_POSTGRES_DB_NAME": "reviews_test",
        "REVIEWS_SERVICE_POSTGRES_USER": "reviews_test",
        "REVIEWS_SERVICE_POSTGRES_PASSWORD": "reviews_test",
        "REVIEWS_SERVICE_POSTGRES_HOST": "localhost",
        "REVIEWS_SERVICE_POSTGRES_PORT": "5432",
        "REVIEWS_SERVICE_REDIS_PASSWORD": "redis_test",
        "REVIEWS_SERVICE_REDIS_HOST": "localhost",
        "REVIEWS_SERVICE_REDIS_PORT": "6379",
        "RABBITMQ_USER": "guest",
        "RABBITMQ_PASSWORD": "guest",
        "RABBITMQ_HOST": "localhost",
        "RABBITMQ_PORT": "5672",
        "JWT_ALGORITHM": "HS256",
        "JWT_PUBLIC_KEY": "test-secret-key-for-reviews-service-tests",
        "PRODUCTS_SERVICE_URL": "http://products-test:8002",
        "MAX_ATTEMPTS": "3",
        "RETRY_PAUSE_SECONDS": "0",
        "CONNECT_TIMEOUT": "1",
        "REQUEST_TIMEOUT": "1",
    }
)

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

import src.models
from src.database import Base
from src.redis_manager import RedisManager, redis_manager


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


@pytest.fixture(autouse=True)
def reset_redis_manager():
    RedisManager._client = None
    redis_manager._client = None
    yield
    RedisManager._client = None
    redis_manager._client = None
