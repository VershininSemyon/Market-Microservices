
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.database import async_session_factory
from src.jwt import TokenData, decode_token
from src.services import OrderService
from src.unitofwork import UnitOfWork


def get_uow() -> UnitOfWork:
    return UnitOfWork(async_session_factory)

UOWDep = Annotated[UnitOfWork, Depends(get_uow)]


def get_order_service(uow: UOWDep) -> OrderService:
    return OrderService(uow)

OrderServiceDep = Annotated[OrderService, Depends(get_order_service)]


bearer_scheme = HTTPBearer()

def get_current_user(
    token: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
) -> TokenData:
    return decode_token(token.credentials)

CurrentUserDep = Annotated[TokenData, Depends(get_current_user)]
