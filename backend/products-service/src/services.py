
from src.exceptions import ProductAlreadyExistsError, ProductNotFoundError
from src.schemas import ProductCreateSchema, ProductReadSchema, ProductUpdateSchema, ProductQueryParams
from src.unitofwork import UnitOfWork
from src.search import index_product, delete_product_index, search_product


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

