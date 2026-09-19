
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class UvicornSettings(BaseModel):
    UVICORN_RELOAD: bool = False
    UVICORN_WORKERS_COUNT: int = 4


class CorsSettings(BaseModel):
    CORS_ORIGINS: list[str] = ["http://localhost", "http://127.0.0.1"]


class PostgresSettings(BaseModel):
    ANALYTICS_SERVICE_POSTGRES_DB_NAME: str
    ANALYTICS_SERVICE_POSTGRES_USER: str
    ANALYTICS_SERVICE_POSTGRES_PASSWORD: str
    ANALYTICS_SERVICE_POSTGRES_HOST: str = 'postgres'
    ANALYTICS_SERVICE_POSTGRES_PORT: int = 5432

    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.ANALYTICS_SERVICE_POSTGRES_USER}:{self.ANALYTICS_SERVICE_POSTGRES_PASSWORD}@{self.ANALYTICS_SERVICE_POSTGRES_HOST}:{self.ANALYTICS_SERVICE_POSTGRES_PORT}/{self.ANALYTICS_SERVICE_POSTGRES_DB_NAME}"


class RabbitMQSettings(BaseModel):
    RABBITMQ_USER: str
    RABBITMQ_PASSWORD: str
    RABBITMQ_HOST: str = 'rabbitmq'
    RABBITMQ_PORT: int = 5672

    USER_EVENTS_EXCHANGE_NAME: str = "user-events-exchange"
    USER_CREATED_ROUTING_KEY: str = "user.created"
    USER_CREATED_QUEUE_NAME: str = "analytics.user-created-queue"
    USER_DELETED_ROUTING_KEY: str = "user.deleted"
    USER_DELETED_QUEUE_NAME: str = "analytics.user-deleted-queue"

    PRODUCTS_EVENTS_EXCHANGE_NAME: str = "products-events-exchange"
    PRODUCT_CREATED_ROUTING_KEY: str = "product.created"
    PRODUCT_CREATED_QUEUE_NAME: str = "analytics.product-created-queue"
    PRODUCT_DELETED_ROUTING_KEY: str = "product.deleted"
    PRODUCT_DELETED_QUEUE_NAME: str = "analytics.product-deleted-queue"

    REVIEWS_EVENTS_EXCHANGE_NAME: str = "reviews-events-exchange"
    REVIEW_CREATED_ROUTING_KEY: str = "review.created"
    REVIEW_CREATED_QUEUE_NAME: str = "analytics.review-created-queue"
    REVIEW_DELETED_ROUTING_KEY: str = "review.deleted"
    REVIEW_DELETED_QUEUE_NAME: str = "analytics.review-deleted-queue"

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
    RabbitMQSettings,
    JwtSettings,
    BaseSettings
):
    model_config = SettingsConfigDict(
        env_file='.env',
        case_sensitive=True,
        extra='ignore'
    )


settings = Settings()
