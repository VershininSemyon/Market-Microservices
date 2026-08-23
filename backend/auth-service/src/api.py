
from fastapi import APIRouter, Cookie, HTTPException, Response, status
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
    auth_service: AuthServiceDep,
    response: Response
):
    token_data = await auth_service.get_tokens(login_data)

    response.set_cookie(
        key="access_token",
        value=token_data.access,
        httponly=True,
        samesite="lax"
    )

    response.set_cookie(
        key="refresh_token",
        value=token_data.refresh,
        httponly=True,
        samesite="lax",
    )

    return token_data


@auth_router.post(
    "/token/refresh",
    status_code=status.HTTP_200_OK,
)
def refresh_token(
    auth_service: AuthServiceDep,
    response: Response,
    refresh_token: str | None = Cookie(default=None),
):
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Нет refresh токена"
        )

    access_token = auth_service.refresh_token(refresh_token)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        samesite="lax"
    )

    return {
        "access": access_token
    }


user_router = APIRouter(prefix="/users", tags=["Users"])

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
    response: Response
):
    await auth_service.delete_user(current_user.id)
    response.delete_cookie(key="access_token")
    response.delete_cookie(key="refresh_token")


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
