
import uuid
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

UserUsername = Annotated[str, Field(max_length=100)]


class UserReadSchema(BaseModel):
    id: uuid.UUID
    username: UserUsername
    email: EmailStr
    registration_date: datetime

    model_config = ConfigDict(from_attributes=True)


class UserCreateSchema(BaseModel):
    username: UserUsername
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError("Пароль должен содержать минимум 8 символов")
        return value


class UserUpdateSchema(BaseModel):
    username: UserUsername
    email: EmailStr


class UserLoginSchema(BaseModel):
    username: str
    password: str


class JWTTokenPairResponseSchema(BaseModel):
    access: str
    refresh: str
