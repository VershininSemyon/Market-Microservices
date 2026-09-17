
import json
from uuid import UUID

from src.config import settings
from src.enums import SortOrderEnum
from src.exceptions import ProductAlreadyExistsError, ProductNotFoundError
from src.producer import rabbitmq_producer
from src.redis_cache_backend import redis_cache
from src.schemas import ProductCreateSchema, ProductQueryParams, ProductReadSchema, ProductUpdateSchema
from src.search import delete_product_index, index_product, search_product
from src.unitofwork import UnitOfWork


class ProductService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def _invalidate_products_cache(self, product_id: str | None = None):
        await redis_cache.del_key("products:list")
        if product_id is not None:
            await redis_cache.del_key(f"products:{product_id}")

    async def create_product(self, data: ProductCreateSchema, user_email: str) -> ProductReadSchema:
        async with self.uow:
            product_exists = await self.uow.product_repo.get_product_by_name(data.name)
            if product_exists:
                raise ProductAlreadyExistsError()

            product = await self.uow.product_repo.create_product(data.model_dump())
            await self.uow.commit()

        await self._invalidate_products_cache()
        await index_product(product.id, product.name, product.description)
        await rabbitmq_producer.publish_message(
            routing_key=settings.PRODUCT_CREATED_ROUTING_KEY,
            message_body={
                "product_name": product.name,
                "created_by": user_email
            }
        )
        return ProductReadSchema.model_validate(product)

    async def get_products_list(self, filters: ProductQueryParams) -> list[ProductReadSchema]:
        # Первый запрос без параметров - кэш
        if all([
            filters.text_query is None,
            filters.min_price is None,
            filters.max_price is None,
            filters.order_by is None,
            filters.order == SortOrderEnum.ASC,
            filters.limit == 10,
            filters.offset == 0
        ]):
            cached = await redis_cache.get_value("products:list")
            if cached is not None:
                return [ProductReadSchema.model_validate(data) for data in json.loads(cached)]

            async with self.uow:
                products = await self.uow.product_repo.list_products()
            products = [ProductReadSchema.model_validate(product) for product in products]

            await redis_cache.set_value(
                "products:list",
                json.dumps([product.model_dump(mode='json') for product in products]),
                3600 * 24 # день
            )
            return products


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

    async def delete_product(self, product_id: UUID, user_email: str) -> None:
        async with self.uow:
            product = await self.uow.product_repo.get_product_by_id(product_id)
            if not product:
                raise ProductNotFoundError()

            await self.uow.product_repo.delete_product(product_id)
            await self.uow.commit()

        await self._invalidate_products_cache(product_id)
        await delete_product_index(product_id)
        await rabbitmq_producer.publish_message(
            routing_key=settings.PRODUCT_DELETED_ROUTING_KEY,
            message_body={
                "product_id": str(product_id),
                "product_name": product.name,
                "deleted_by": user_email
            }
        )

    async def get_product_by_id(self, product_id: UUID) -> ProductReadSchema:
        cached = await redis_cache.get_value(f"products:{product_id}")
        if cached is not None:
            return ProductReadSchema.model_validate_json(cached)

        async with self.uow:
            product = await self.uow.product_repo.get_product_by_id(product_id)

        if not product:
            raise ProductNotFoundError()

        product = ProductReadSchema.model_validate(product)
        await redis_cache.set_value(
            f"products:{product_id}",
            product.model_dump_json(),
            3600 * 24 * 7 # неделя
        )
        return product

    async def update_product(self, product_id: UUID, data: ProductUpdateSchema) -> ProductReadSchema:
        async with self.uow:
            product_by_name = await self.uow.product_repo.get_product_by_name(data.name)
            if product_by_name and product_by_name.id != product_id:
                raise ProductAlreadyExistsError()

            product = await self.uow.product_repo.update_product(product_id, data.model_dump())
            if not product:
                raise ProductNotFoundError()
            await self.uow.commit()

        await self._invalidate_products_cache(product_id)
        await index_product(product.id, product.name, product.description)
        return ProductReadSchema.model_validate(product)
