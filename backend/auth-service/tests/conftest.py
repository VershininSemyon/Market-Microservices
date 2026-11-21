
import os

os.environ.update(
    {
        "AUTH_SERVICE_POSTGRES_DB_NAME": "auth_test",
        "AUTH_SERVICE_POSTGRES_USER": "auth_test",
        "AUTH_SERVICE_POSTGRES_PASSWORD": "auth_test",
        "AUTH_SERVICE_POSTGRES_HOST": "localhost",
        "AUTH_SERVICE_POSTGRES_PORT": "5432",
        "AUTH_SERVICE_REDIS_PASSWORD": "redis_test",
        "AUTH_SERVICE_REDIS_HOST": "localhost",
        "AUTH_SERVICE_REDIS_PORT": "6379",
        "RABBITMQ_USER": "guest",
        "RABBITMQ_PASSWORD": "guest",
        "RABBITMQ_HOST": "localhost",
        "RABBITMQ_PORT": "5672",
        "JWT_ALGORITHM": "HS256",
        "JWT_PRIVATE_KEY": "test-secret-key-for-auth-service-tests",
        "JWT_PUBLIC_KEY": "test-secret-key-for-auth-service-tests",
        "PASSWORD_SALT": "test-salt",
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
