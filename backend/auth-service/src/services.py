
from src.exceptions import (
    EmailAlreadyExistsError,
    InvalidPasswordError,
    InvalidTokenTypeError,
    UsernameAlreadyExistsError,
    UserNotFoundError,
)
from src.schemas import (
    JWTTokenPairResponseSchema,
    UserCreateSchema,
    UserLoginSchema,
    UserReadSchema,
    UserUpdateSchema,
)
from src.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from src.unitofwork import UnitOfWork


class AuthService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def create_user(self, data: UserCreateSchema) -> UserReadSchema:
        async with self.uow:
            user = await self.uow.user_repo.get_user_by_username(data.username)
            if user is not None:
                raise UsernameAlreadyExistsError()

            user = await self.uow.user_repo.get_user_by_email(data.email)
            if user is not None:
                raise EmailAlreadyExistsError()

            user_dict = data.model_dump()
            user_dict['password'] = hash_password(user_dict['password'])

            created_user = await self.uow.user_repo.create_user(user_dict)
            await self.uow.commit()

        return UserReadSchema.model_validate(created_user)

    async def delete_user(self, user_id: str) -> None:
        async with self.uow:
            await self.uow.user_repo.delete_user(user_id)
            await self.uow.commit()

    async def change_user(self, current_user: UserReadSchema, data: UserUpdateSchema) -> UserReadSchema:
        async with self.uow:
            if current_user.username != data.username:
                user = await self.uow.user_repo.get_user_by_username(data.username)
                if user is not None:
                    raise UsernameAlreadyExistsError()

            if current_user.email != data.email:
                user = await self.uow.user_repo.get_user_by_email(data.email)
                if user is not None:
                    raise EmailAlreadyExistsError()

            updated_user = await self.uow.user_repo.update_user(current_user.id, data.model_dump())
            await self.uow.commit()

        return UserReadSchema.model_validate(updated_user)

    async def get_tokens(self, login_data: UserLoginSchema) -> JWTTokenPairResponseSchema:
        async with self.uow:
            user = await self.uow.user_repo.get_user_by_username(login_data.username)

        if not user:
            raise UserNotFoundError()

        if not verify_password(login_data.password, user.password):
            raise InvalidPasswordError()

        user_data = {
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "is_admin": user.is_admin
        }

        return JWTTokenPairResponseSchema.model_validate({
            "access": create_access_token(user_data),
            "refresh": create_refresh_token(user_data)
        })

    def refresh_token(self, refresh_token: str) -> str:
        data = decode_token(refresh_token)

        if data.get('token_type') != 'refresh':
            raise InvalidTokenTypeError()

        user_data = {
            "id": data['id'],
            "username": data['username'],
            "email": data['email'],
            "is_admin": data['is_admin']
        }

        access = create_access_token(user_data)
        return access

    async def authenticate_user(self, access_token: str) -> UserReadSchema:
        data = decode_token(access_token)

        if data.get('token_type') != 'access':
            raise InvalidTokenTypeError()

        async with self.uow:
            user = await self.uow.user_repo.get_user_by_id(data['id'])
            return UserReadSchema.model_validate(user)
