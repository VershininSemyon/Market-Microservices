

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class RabbitMQSettings(BaseModel):
    RABBITMQ_USER: str
    RABBITMQ_PASSWORD: str
    RABBITMQ_HOST: str = 'rabbitmq'
    RABBITMQ_PORT: int = 5672

    USER_EVENTS_EXCHANGE_NAME: str = "user-events-exchange"
    USER_CREATED_ROUTING_KEY: str = "user.registered"
    NOTIFICATION_QUEUE_NAME: str = "notification.user-registered-queue"

    @property
    def amqp_url(self) -> str:
        return f"amqp://{self.RABBITMQ_USER}:{self.RABBITMQ_PASSWORD}@{self.RABBITMQ_HOST}:{self.RABBITMQ_PORT}/"


class SMTPSettings(BaseModel):
    SMTP_HOST: str
    SMTP_PORT: int = 1025
    SMTP_FROM: str


class Settings(
    RabbitMQSettings,
    SMTPSettings,
    BaseSettings
):
    model_config = SettingsConfigDict(
        env_file='.env',
        case_sensitive=True,
        extra='ignore'
    )


settings = Settings()
