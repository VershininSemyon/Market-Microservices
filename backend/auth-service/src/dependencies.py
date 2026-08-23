
from typing import Annotated

from database import async_session_factory
from fastapi import Cookie, Depends, HTTPException, status
from schemas import UserReadSchema
from services import AuthService
from unitofwork import UnitOfWork


def get_uow() -> UnitOfWork:
    return UnitOfWork(async_session_factory)

UOWDep = Annotated[UnitOfWork, Depends(get_uow)]


def get_auth_service(uow: UOWDep) -> AuthService:
    return AuthService(uow)

AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


async def get_current_user(
    auth_service: AuthServiceDep,
    access_token: str | None = Cookie(default=None),
) -> UserReadSchema:
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Не предоставлен access токен",
        )

    user = await auth_service.authenticate_user(access_token)
    return user

CurrentUserDep = Annotated[UserReadSchema, Depends(get_current_user)]
