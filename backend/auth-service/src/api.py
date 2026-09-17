
from fastapi import APIRouter, Body, HTTPException, status

from src.dependencies import AuthServiceDep, CurrentUserDep
from src.schemas import (
    JWTTokenPairResponseSchema,
    UserCreateSchema,
    UserLoginSchema,
    UserReadSchema,
    UserUpdateSchema,
)

auth_router = APIRouter(prefix="/auth", tags=["Auth"])


@auth_router.post(
    "/token",
    response_model=JWTTokenPairResponseSchema,
    status_code=status.HTTP_200_OK,
)
async def authenticate(
    login_data: UserLoginSchema,
    auth_service: AuthServiceDep
):
    token_data = await auth_service.get_tokens(login_data)

    return token_data


@auth_router.post(
    "/token/refresh",
    status_code=status.HTTP_200_OK,
)
async def refresh_token(
    auth_service: AuthServiceDep,
    refresh_token: str | None = Body(default=None),
):
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Нет refresh токена"
        )

    return await auth_service.refresh_token(refresh_token)


user_router = APIRouter(prefix="/auth/users", tags=["Users"])

@user_router.post(
    "/",
    response_model=UserReadSchema,
    status_code=status.HTTP_201_CREATED
)
async def register_user(
    user_data: UserCreateSchema,
    auth_service: AuthServiceDep
) -> UserReadSchema:
    new_user = await auth_service.create_user(user_data)
    return new_user


@user_router.get(
    "/me",
    response_model=UserReadSchema,
    status_code=status.HTTP_200_OK,
)
async def get_me(
    current_user: CurrentUserDep,
) -> UserReadSchema:
    return current_user


@user_router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_me(
    current_user: CurrentUserDep,
    auth_service: AuthServiceDep,
):
    await auth_service.delete_user(current_user.id)


@user_router.put(
    "/me",
    response_model=UserReadSchema,
    status_code=status.HTTP_200_OK
)
async def change_me(
    user_data: UserUpdateSchema,
    current_user: CurrentUserDep,
    auth_service: AuthServiceDep,
) -> UserReadSchema:
    return await auth_service.change_user(current_user, user_data)
