
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class UvicornSettings(BaseModel):
    UVICORN_RELOAD: bool = False
    UVICORN_WORKERS_COUNT: int = 4


class CorsSettings(BaseModel):
    CORS_ORIGINS: list[str] = ["http://localhost", "http://127.0.0.1"]


class PostgresSettings(BaseModel):
    PRODUCTS_SERVICE_POSTGRES_DB_NAME: str
    PRODUCTS_SERVICE_POSTGRES_USER: str
    PRODUCTS_SERVICE_POSTGRES_PASSWORD: str
    PRODUCTS_SERVICE_POSTGRES_HOST: str = 'postgres'
    PRODUCTS_SERVICE_POSTGRES_PORT: int = 5432

    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.PRODUCTS_SERVICE_POSTGRES_USER}:{self.PRODUCTS_SERVICE_POSTGRES_PASSWORD}@{self.PRODUCTS_SERVICE_POSTGRES_HOST}:{self.PRODUCTS_SERVICE_POSTGRES_PORT}/{self.PRODUCTS_SERVICE_POSTGRES_DB_NAME}"


class ElasticSearchSettings(BaseModel):
    PRODUCTS_INDEX: str = "products-index"


class JwtSettings(BaseModel):
    JWT_ALGORITHM: str = 'RS256'
    JWT_PUBLIC_KEY: str


class Settings(
    UvicornSettings,
    CorsSettings,
    PostgresSettings,
    ElasticSearchSettings,
    JwtSettings,
    BaseSettings
):
    model_config = SettingsConfigDict(
        env_file='.env',
        case_sensitive=True,
        extra='ignore'
    )


settings = Settings()
