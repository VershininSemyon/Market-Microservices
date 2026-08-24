
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.database import async_session_factory
from src.schemas import UserReadSchema
from src.services import AuthService
from src.unitofwork import UnitOfWork


def get_uow() -> UnitOfWork:
    return UnitOfWork(async_session_factory)

UOWDep = Annotated[UnitOfWork, Depends(get_uow)]


def get_auth_service(uow: UOWDep) -> AuthService:
    return AuthService(uow)

AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


bearer_scheme = HTTPBearer()

async def get_current_user(
    auth_service: AuthServiceDep,
    access_token: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
) -> UserReadSchema:
    return await auth_service.authenticate_user(access_token.credentials)

CurrentUserDep = Annotated[UserReadSchema, Depends(get_current_user)]
