
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class UvicornSettings(BaseModel):
    UVICORN_RELOAD: bool = False
    UVICORN_WORKERS_COUNT: int = 4


class CorsSettings(BaseModel):
    CORS_ORIGINS: list[str] = ["http://localhost", "http://127.0.0.1"]


class PostgresSettings(BaseModel):
    ORDERS_SERVICE_POSTGRES_DB_NAME: str
    ORDERS_SERVICE_POSTGRES_USER: str
    ORDERS_SERVICE_POSTGRES_PASSWORD: str
    ORDERS_SERVICE_POSTGRES_HOST: str = 'postgres'
    ORDERS_SERVICE_POSTGRES_PORT: int = 5432

    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.ORDERS_SERVICE_POSTGRES_USER}:{self.ORDERS_SERVICE_POSTGRES_PASSWORD}@{self.ORDERS_SERVICE_POSTGRES_HOST}:{self.ORDERS_SERVICE_POSTGRES_PORT}/{self.ORDERS_SERVICE_POSTGRES_DB_NAME}"


class RabbitMQSettings(BaseModel):
    RABBITMQ_USER: str
    RABBITMQ_PASSWORD: str
    RABBITMQ_HOST: str = 'rabbitmq'
    RABBITMQ_PORT: int = 5672

    ORDERS_EVENTS_EXCHANGE_NAME: str = "orders-events-exchange"
    ORDER_CREATED_ROUTING_KEY: str = "order.created"

    @property
    def amqp_url(self) -> str:
        return f"amqp://{self.RABBITMQ_USER}:{self.RABBITMQ_PASSWORD}@{self.RABBITMQ_HOST}:{self.RABBITMQ_PORT}/"


class JwtSettings(BaseModel):
    JWT_ALGORITHM: str = 'RS256'
    JWT_PUBLIC_KEY: str


class Settings(
    UvicornSettings,
    CorsSettings,
    PostgresSettings,
    JwtSettings,
    RabbitMQSettings,
    BaseSettings
):
    model_config = SettingsConfigDict(
        env_file='.env',
        case_sensitive=True,
        extra='ignore'
    )


settings = Settings()
