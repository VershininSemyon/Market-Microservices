
from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.database import async_session_factory
from src.jwt import TokenData, decode_token
from src.services import ProductService
from src.unitofwork import UnitOfWork


def get_uow() -> UnitOfWork:
    return UnitOfWork(async_session_factory)

UOWDep = Annotated[UnitOfWork, Depends(get_uow)]


def get_product_service(uow: UOWDep) -> ProductService:
    return ProductService(uow)

ProductServiceDep = Annotated[ProductService, Depends(get_product_service)]


bearer_scheme = HTTPBearer()

def get_current_user(
    token: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
) -> TokenData:
    return decode_token(token.credentials)

CurrentUserDep = Annotated[TokenData, Depends(get_current_user)]

def require_admin(user: CurrentUserDep) -> None:
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Доступ запрещён")
