
import uuid

from src.enums import ProductSortFieldEnum, SortOrderEnum
from src.models import ProductORM
from src.repositories import ProductRepository


def make_data(**overrides) -> dict:
    data = {
        "name": "apple",
        "description": "green apple",
        "price": 10.0,
        "quantity": 5,
        "is_active": True,
    }
    data.update(overrides)
    return data


async def test_create_product_returns_persisted_entity(db_session) -> None:
    repo = ProductRepository(db_session)

    product = await repo.create_product(make_data())
    await db_session.commit()

    assert product is not None
    assert isinstance(product.id, uuid.UUID)
    assert product.name == "apple"
    assert product.created_at is not None


async def test_list_products_returns_only_active(db_session) -> None:
    repo = ProductRepository(db_session)
    await repo.create_product(make_data(name="active"))
    await repo.create_product(make_data(name="inactive", is_active=False))
    await db_session.commit()

    products = await repo.list_products()

    assert [product.name for product in products] == ["active"]


async def test_list_products_filters_by_ids(db_session) -> None:
    repo = ProductRepository(db_session)
    first = await repo.create_product(make_data(name="first"))
    second = await repo.create_product(make_data(name="second"))
    await repo.create_product(make_data(name="third"))
    await db_session.commit()

    products = await repo.list_products(product_ids=[first.id, second.id])

    assert {product.name for product in products} == {"first", "second"}


async def test_list_products_filters_by_price_range(db_session) -> None:
    repo = ProductRepository(db_session)
    await repo.create_product(make_data(name="cheap", price=10.0))
    await repo.create_product(make_data(name="middle", price=20.0))
    await repo.create_product(make_data(name="expensive", price=30.0))
    await db_session.commit()

    products = await repo.list_products(min_price=15.0, max_price=25.0)

    assert [product.name for product in products] == ["middle"]


async def test_list_products_sorts_by_price(db_session) -> None:
    repo = ProductRepository(db_session)
    await repo.create_product(make_data(name="middle", price=20.0))
    await repo.create_product(make_data(name="cheap", price=10.0))
    await repo.create_product(make_data(name="expensive", price=30.0))
    await db_session.commit()

    ascending = await repo.list_products(order_by=ProductSortFieldEnum.PRICE)
    descending = await repo.list_products(
        order_by=ProductSortFieldEnum.PRICE,
        order=SortOrderEnum.DESC,
    )

    assert [product.price for product in ascending] == [10.0, 20.0, 30.0]
    assert [product.price for product in descending] == [30.0, 20.0, 10.0]


async def test_list_products_sorts_by_name(db_session) -> None:
    repo = ProductRepository(db_session)
    await repo.create_product(make_data(name="banana"))
    await repo.create_product(make_data(name="apple"))
    await db_session.commit()

    products = await repo.list_products(order_by=ProductSortFieldEnum.NAME)

    assert [product.name for product in products] == ["apple", "banana"]


async def test_list_products_applies_pagination(db_session) -> None:
    repo = ProductRepository(db_session)
    for index in range(3):
        await repo.create_product(make_data(name=f"product-{index}", price=float(index + 1)))
    await db_session.commit()

    products = await repo.list_products(
        order_by=ProductSortFieldEnum.PRICE,
        limit=1,
        offset=1,
    )

    assert [product.name for product in products] == ["product-1"]


async def test_get_active_products_by_ids_returns_only_active(db_session) -> None:
    repo = ProductRepository(db_session)
    active = await repo.create_product(make_data(name="active"))
    inactive = await repo.create_product(make_data(name="inactive", is_active=False))
    await db_session.commit()

    products = await repo.get_active_products_by_ids([active.id, inactive.id, uuid.uuid4()])

    assert [product.id for product in products] == [active.id]


async def test_get_product_by_id_returns_active_product(db_session) -> None:
    repo = ProductRepository(db_session)
    created = await repo.create_product(make_data())
    await db_session.commit()

    product = await repo.get_product_by_id(created.id)

    assert product is not None
    assert product.id == created.id


async def test_get_product_by_id_returns_none_for_inactive_product(db_session) -> None:
    repo = ProductRepository(db_session)
    created = await repo.create_product(make_data(is_active=False))
    await db_session.commit()

    assert await repo.get_product_by_id(created.id) is None


async def test_get_product_by_id_returns_none_for_unknown_id(db_session) -> None:
    repo = ProductRepository(db_session)

    assert await repo.get_product_by_id(uuid.uuid4()) is None


async def test_get_product_by_name(db_session) -> None:
    repo = ProductRepository(db_session)
    await repo.create_product(make_data(name="apple"))
    await db_session.commit()

    product = await repo.get_product_by_name("apple")

    assert product is not None
    assert product.name == "apple"


async def test_get_product_by_name_returns_none_for_inactive_product(db_session) -> None:
    repo = ProductRepository(db_session)
    await repo.create_product(make_data(name="apple", is_active=False))
    await db_session.commit()

    assert await repo.get_product_by_name("apple") is None


async def test_update_product_changes_fields(db_session) -> None:
    repo = ProductRepository(db_session)
    created = await repo.create_product(make_data())
    await db_session.commit()

    updated = await repo.update_product(
        created.id,
        {"price": 99.0, "quantity": 7},
    )
    await db_session.commit()

    assert updated is not None
    assert updated.id == created.id
    assert updated.price == 99.0
    assert updated.quantity == 7


async def test_update_product_returns_none_for_unknown_id(db_session) -> None:
    repo = ProductRepository(db_session)

    assert await repo.update_product(uuid.uuid4(), {"price": 99.0}) is None


async def test_update_product_returns_none_for_inactive_product(db_session) -> None:
    repo = ProductRepository(db_session)
    created = await repo.create_product(make_data(is_active=False))
    await db_session.commit()

    assert await repo.update_product(created.id, {"price": 99.0}) is None


async def test_delete_product_soft_deletes(db_session) -> None:
    repo = ProductRepository(db_session)
    created = await repo.create_product(make_data())
    await db_session.commit()

    await repo.delete_product(created.id)
    await db_session.commit()

    stored = await db_session.get(ProductORM, created.id)
    assert stored is not None
    assert stored.is_active is False
    assert await repo.get_product_by_id(created.id) is None


async def test_change_product_quantity_decrements(db_session) -> None:
    repo = ProductRepository(db_session)
    created = await repo.create_product(make_data(quantity=5))
    await db_session.commit()

    updated = await repo.change_product_quantity(created.id, -3)
    await db_session.commit()

    assert updated is not None
    assert updated.quantity == 2


async def test_change_product_quantity_increments(db_session) -> None:
    repo = ProductRepository(db_session)
    created = await repo.create_product(make_data(quantity=5))
    await db_session.commit()

    updated = await repo.change_product_quantity(created.id, 4)
    await db_session.commit()

    assert updated is not None
    assert updated.quantity == 9


async def test_change_product_quantity_returns_none_for_unknown_id(db_session) -> None:
    repo = ProductRepository(db_session)

    assert await repo.change_product_quantity(uuid.uuid4(), -1) is None
