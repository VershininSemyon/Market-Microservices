

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class UvicornSettings(BaseModel):
    UVICORN_RELOAD: bool = False
    UVICORN_WORKERS_COUNT: int = 4


class CorsSettings(BaseModel):
    CORS_ORIGINS: list[str] = ["http://localhost", "http://127.0.0.1"]


class PostgresSettings(BaseModel):
    POSTGRES_DB_NAME: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str = 'postgres'
    POSTGRES_PORT: int = 5432

    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB_NAME}"


class JwtSettings(BaseModel):
    JWT_ALGORITHM: str = 'RS256'
    JWT_PRIVATE_KEY: str
    JWT_PUBLIC_KEY: str

    ACCESS_TOKEN_LIFETIME_MINUTES: int = 15
    REFRESH_TOKEN_LIFETIME_DAYS: int = 2


class PasswordSettings(BaseModel):
    PASSWORD_SALT: str


class RedisSettings(BaseModel):
    REDIS_PASSWORD: str
    REDIS_PORT: int = 6379

    @property
    def redis_url(self) -> str:
        return f"redis://:{self.REDIS_PASSWORD}@redis:{self.REDIS_PORT}/0"


class Settings(
    UvicornSettings,
    CorsSettings,
    PostgresSettings,
    JwtSettings,
    PasswordSettings,
    RedisSettings,
    BaseSettings
):
    model_config = SettingsConfigDict(
        env_file='.env',
        case_sensitive=True,
        extra='ignore'
    )


settings = Settings()
