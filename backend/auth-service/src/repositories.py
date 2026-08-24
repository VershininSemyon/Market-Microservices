
from sqlalchemy import delete, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import UserORM


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user_by_id(self, user_id):
        stmt = select(UserORM).where(UserORM.id == user_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def create_user(self, data: dict) -> UserORM:
        stmt = insert(UserORM).values(**data).returning(UserORM)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_user(self, user_id, data: dict) -> UserORM:
        stmt = update(UserORM).where(UserORM.id == user_id).values(**data).returning(UserORM)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def delete_user(self, user_id) -> None:
        stmt = delete(UserORM).where(UserORM.id == user_id)
        await self.session.execute(stmt)

    async def get_user_by_username(self, username: str) -> UserORM:
        stmt = select(UserORM).where(UserORM.username == username)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_user_by_email(self, email: str) -> UserORM:
        stmt = select(UserORM).where(UserORM.email == email)
        result = await self.session.execute(stmt)
        return result.scalars().first()
