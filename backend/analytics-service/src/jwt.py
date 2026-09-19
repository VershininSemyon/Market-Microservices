
import uuid

from fastapi import HTTPException
from pydantic import BaseModel

import jwt
from src.config import settings


class TokenData(BaseModel):
    id: uuid.UUID
    username: str
    email: str
    is_admin: bool


def decode_token(token: str) -> TokenData:
    try:
        data = jwt.decode(
            jwt=token,
            algorithms=[settings.JWT_ALGORITHM],
            key=settings.JWT_PUBLIC_KEY
        )

        if data['token_type'] != 'access':
            raise HTTPException(status_code=401, detail="Неверный тип токена")

        return TokenData.model_validate(data)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Токен просрочен")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Недействительный токен")
