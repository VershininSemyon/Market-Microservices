
from uuid import UUID

from src.exceptions import ProductAlreadyExistsError, ProductNotFoundError
from src.schemas import ProductCreateSchema, ProductQueryParams, ProductReadSchema, ProductUpdateSchema
from src.search import delete_product_index, index_product, search_product
from src.unitofwork import UnitOfWork


class ProductService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def create_product(self, data: ProductCreateSchema) -> ProductReadSchema:
        async with self.uow:
            product_exists = await self.uow.product_repo.get_product_by_name(data.name)
            if product_exists:
                raise ProductAlreadyExistsError()

            product = await self.uow.product_repo.create_product(data.model_dump())
            await self.uow.commit()

        await index_product(product.id, product.name, product.description)
        return ProductReadSchema.model_validate(product)

    async def get_products_list(self, filters: ProductQueryParams) -> list[ProductReadSchema]:
        product_ids = None

        if filters.text_query:
            product_ids = await search_product(filters.text_query)

        async with self.uow:
            products = await self.uow.product_repo.list_products(
                product_ids=product_ids,
                min_price=filters.min_price,
                max_price=filters.max_price,
                order_by=filters.order_by,
                order=filters.order,
                limit=filters.limit,
                offset=filters.offset
            )

        return [ProductReadSchema.model_validate(product) for product in products]

    async def delete_product(self, product_id: UUID) -> None:
        async with self.uow:
            await self.uow.product_repo.delete_product(product_id)
            await self.uow.commit()

        await delete_product_index(product_id)

    async def get_product_by_id(self, product_id: UUID) -> ProductReadSchema:
        async with self.uow:
            product = await self.uow.product_repo.get_product_by_id(product_id)
            if not product:
                raise ProductNotFoundError()

        return ProductReadSchema.model_validate(product)

    async def update_product(self, product_id: UUID, data: ProductUpdateSchema) -> ProductReadSchema:
        async with self.uow:
            product_by_name = await self.uow.product_repo.get_product_by_name(data.name)
            if product_by_name and product_by_name.id != product_id:
                raise ProductAlreadyExistsError()

            product = await self.uow.product_repo.update_product(product_id, data.model_dump())
            if not product:
                raise ProductNotFoundError()
            await self.uow.commit()

        await index_product(product.id, product.name, product.description)
        return ProductReadSchema.model_validate(product)
