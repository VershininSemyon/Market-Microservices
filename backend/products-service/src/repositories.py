
from sqlalchemy import asc, delete, desc, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.enums import ProductSortFieldEnum, SortOrderEnum
from src.models import ProductORM


class ProductRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_products(
        self,
        product_ids: list[str] | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        order_by: ProductSortFieldEnum | None = None,
        order: SortOrderEnum = SortOrderEnum.ASC,
        limit: int = 10,
        offset: int = 0
    ) -> list[ProductORM]:
        stmt = select(ProductORM).where(ProductORM.is_active)

        if product_ids is not None:
            stmt = stmt.where(ProductORM.id.in_(product_ids))

        if min_price is not None:
            stmt = stmt.where(ProductORM.price >= min_price)

        if max_price is not None:
            stmt = stmt.where(ProductORM.price <= max_price)

        sort_column = {
            ProductSortFieldEnum.PRICE: ProductORM.price,
            ProductSortFieldEnum.NAME: ProductORM.name,
        }.get(order_by)

        if sort_column is not None:
            if order == SortOrderEnum.DESC:
                stmt = stmt.order_by(desc(sort_column))
            else:
                stmt = stmt.order_by(asc(sort_column))

        stmt = stmt.limit(limit).offset(offset)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_product_by_id(self, product_id) -> ProductORM:
        stmt = select(ProductORM).where(ProductORM.id == product_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def create_product(self, data: dict) -> ProductORM:
        stmt = insert(ProductORM).values(**data).returning(ProductORM)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_product(self, product_id, data: dict) -> ProductORM:
        stmt = update(ProductORM).where(ProductORM.id == product_id).values(**data).returning(ProductORM)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def delete_product(self, product_id) -> None:
        stmt = delete(ProductORM).where(ProductORM.id == product_id)
        await self.session.execute(stmt)

    async def get_product_by_name(self, name: str) -> ProductORM:
        stmt = select(ProductORM).where(ProductORM.name == name)
        result = await self.session.execute(stmt)
        return result.scalars().first()
