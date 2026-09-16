

from sqlalchemy import delete, func, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import ReviewORM


class ReviewRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_review_by_id(self, review_id):
        stmt = select(ReviewORM).where(ReviewORM.id == review_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def create_review(self, data: dict) -> ReviewORM:
        stmt = insert(ReviewORM).values(**data).returning(ReviewORM)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_review(self, review_id, data: dict) -> ReviewORM:
        stmt = update(ReviewORM).where(ReviewORM.id == review_id).values(**data).returning(ReviewORM)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def delete_review(self, review_id) -> None:
        stmt = delete(ReviewORM).where(ReviewORM.id == review_id)
        await self.session.execute(stmt)

    async def get_reviews_by_product_id(self, product_id: str):
        stmt = select(ReviewORM).where(ReviewORM.product_id == product_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_review_by_user_and_product(self, user_id: str, product_id: str):
        stmt = select(ReviewORM).where(ReviewORM.user_id == user_id, ReviewORM.product_id == product_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_product_avg_rating(self, product_id: str) -> float:
        stmt = select(func.avg(ReviewORM.rating)).where(ReviewORM.product_id == product_id)
        result = await self.session.execute(stmt)
        return result.scalar() or 0.0
