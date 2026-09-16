

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class UvicornSettings(BaseModel):
    UVICORN_RELOAD: bool = False
    UVICORN_WORKERS_COUNT: int = 4


class CorsSettings(BaseModel):
    CORS_ORIGINS: list[str] = ["http://localhost", "http://127.0.0.1"]


class PostgresSettings(BaseModel):
    REVIEWS_SERVICE_POSTGRES_DB_NAME: str
    REVIEWS_SERVICE_POSTGRES_USER: str
    REVIEWS_SERVICE_POSTGRES_PASSWORD: str
    REVIEWS_SERVICE_POSTGRES_HOST: str = 'postgres'
    REVIEWS_SERVICE_POSTGRES_PORT: int = 5432

    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.REVIEWS_SERVICE_POSTGRES_USER}:{self.REVIEWS_SERVICE_POSTGRES_PASSWORD}@{self.REVIEWS_SERVICE_POSTGRES_HOST}:{self.REVIEWS_SERVICE_POSTGRES_PORT}/{self.REVIEWS_SERVICE_POSTGRES_DB_NAME}"


class RabbitMQSettings(BaseModel):
    RABBITMQ_USER: str
    RABBITMQ_PASSWORD: str
    RABBITMQ_HOST: str = 'rabbitmq'
    RABBITMQ_PORT: int = 5672

    REVIEWS_EVENTS_EXCHANGE_NAME: str = "reviews-events-exchange"
    REVIEW_CREATED_ROUTING_KEY: str = "review.created"
    REVIEW_DELETED_ROUTING_KEY: str = "review.deleted"

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
