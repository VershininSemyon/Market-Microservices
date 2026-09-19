
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class UvicornSettings(BaseModel):
    UVICORN_RELOAD: bool = False
    UVICORN_WORKERS_COUNT: int = 4


class CorsSettings(BaseModel):
    CORS_ORIGINS: list[str] = ["http://localhost", "http://127.0.0.1"]


class PostgresSettings(BaseModel):
    AUTH_SERVICE_POSTGRES_DB_NAME: str
    AUTH_SERVICE_POSTGRES_USER: str
    AUTH_SERVICE_POSTGRES_PASSWORD: str
    AUTH_SERVICE_POSTGRES_HOST: str = 'postgres'
    AUTH_SERVICE_POSTGRES_PORT: int = 5432

    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.AUTH_SERVICE_POSTGRES_USER}:{self.AUTH_SERVICE_POSTGRES_PASSWORD}@{self.AUTH_SERVICE_POSTGRES_HOST}:{self.AUTH_SERVICE_POSTGRES_PORT}/{self.AUTH_SERVICE_POSTGRES_DB_NAME}"


class RedisSettings(BaseModel):
    AUTH_SERVICE_REDIS_PASSWORD: str
    AUTH_SERVICE_REDIS_HOST: str = "redis"
    AUTH_SERVICE_REDIS_PORT: int = 6379

    @property
    def redis_url(self) -> str:
        return f"redis://:{self.AUTH_SERVICE_REDIS_PASSWORD}@{self.AUTH_SERVICE_REDIS_HOST}:{self.AUTH_SERVICE_REDIS_PORT}/0"


class RabbitMQSettings(BaseModel):
    RABBITMQ_USER: str
    RABBITMQ_PASSWORD: str
    RABBITMQ_HOST: str = 'rabbitmq'
    RABBITMQ_PORT: int = 5672

    USER_EVENTS_EXCHANGE_NAME: str = "user-events-exchange"
    USER_CREATED_ROUTING_KEY: str = "user.created"
    USER_DELETED_ROUTING_KEY: str = "user.deleted"

    @property
    def amqp_url(self) -> str:
        return f"amqp://{self.RABBITMQ_USER}:{self.RABBITMQ_PASSWORD}@{self.RABBITMQ_HOST}:{self.RABBITMQ_PORT}/"


class JwtSettings(BaseModel):
    JWT_ALGORITHM: str = 'RS256'
    JWT_PRIVATE_KEY: str
    JWT_PUBLIC_KEY: str

    ACCESS_TOKEN_LIFETIME_MINUTES: int = 15
    REFRESH_TOKEN_LIFETIME_DAYS: int = 2


class PasswordSettings(BaseModel):
    PASSWORD_SALT: str


class Settings(
    UvicornSettings,
    CorsSettings,
    PostgresSettings,
    RedisSettings,
    RabbitMQSettings,
    JwtSettings,
    PasswordSettings,
    BaseSettings
):
    model_config = SettingsConfigDict(
        env_file='.env',
        case_sensitive=True,
        extra='ignore'
    )


settings = Settings()
