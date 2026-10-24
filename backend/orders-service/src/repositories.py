
from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import OrderORM


class OrderRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_order_by_id(self, order_id):
        stmt = select(OrderORM).where(OrderORM.id == order_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def create_order(self, data: dict) -> OrderORM:
        stmt = insert(OrderORM).values(**data).returning(OrderORM)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_orders_by_user_id(self, user_id: str):
        stmt = select(OrderORM).where(OrderORM.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()
