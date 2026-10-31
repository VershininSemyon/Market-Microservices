
import uuid

from sqlalchemy import delete, insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import OrderORM, OutboxEventORM


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


class OutboxEventRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_outbox_event(self, data: dict) -> OutboxEventORM:
        stmt = insert(OutboxEventORM).values(**data).returning(OutboxEventORM)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_last_outbox_events(self, limit: int = 10) -> list[OutboxEventORM]:
        stmt = select(OutboxEventORM).order_by(OutboxEventORM.created_at.asc()).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def delete_outbox_events(self, event_ids: list[uuid.UUID]) -> None:
        if not event_ids:
            return
        stmt = delete(OutboxEventORM).where(OutboxEventORM.id.in_(event_ids))
        await self.session.execute(stmt)
