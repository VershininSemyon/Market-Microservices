
import uuid
from unittest.mock import AsyncMock

import src.search as search_module
from src.config import settings
from src.search import (
    create_products_index,
    delete_product_index,
    index_product,
    search_product,
)


async def test_create_products_index_skips_existing_index(monkeypatch) -> None:
    es = AsyncMock()
    es.indices.exists.return_value = True
    monkeypatch.setattr(search_module, "es", es)

    await create_products_index()

    es.indices.exists.assert_awaited_once_with(index=settings.PRODUCTS_INDEX)
    es.indices.create.assert_not_awaited()


async def test_create_products_index_creates_missing_index(monkeypatch) -> None:
    es = AsyncMock()
    es.indices.exists.return_value = False
    monkeypatch.setattr(search_module, "es", es)

    await create_products_index()

    es.indices.create.assert_awaited_once()
    create_kwargs = es.indices.create.call_args.kwargs
    assert create_kwargs["index"] == settings.PRODUCTS_INDEX
    assert "mappings" in create_kwargs["body"]
    assert "settings" in create_kwargs["body"]


async def test_index_product(monkeypatch) -> None:
    es = AsyncMock()
    monkeypatch.setattr(search_module, "es", es)
    product_id = uuid.uuid4()

    await index_product(product_id, "apple", "green apple")

    es.index.assert_awaited_once_with(
        index=settings.PRODUCTS_INDEX,
        id=str(product_id),
        document={
            "id": str(product_id),
            "name": "apple",
            "description": "green apple",
        },
    )


async def test_delete_product_index(monkeypatch) -> None:
    es = AsyncMock()
    monkeypatch.setattr(search_module, "es", es)
    product_id = uuid.uuid4()

    await delete_product_index(product_id)

    es.delete.assert_awaited_once_with(
        index=settings.PRODUCTS_INDEX,
        id=str(product_id),
        ignore=[404],
    )


async def test_search_product_returns_hit_ids(monkeypatch) -> None:
    es = AsyncMock()
    es.search.return_value = {
        "hits": {"hits": [{"_id": "product-1"}, {"_id": "product-2"}]}
    }
    monkeypatch.setattr(search_module, "es", es)

    result = await search_product("apple", 5)

    assert result == ["product-1", "product-2"]
    es.search.assert_awaited_once()
    search_kwargs = es.search.call_args.kwargs
    assert search_kwargs["index"] == settings.PRODUCTS_INDEX
    assert search_kwargs["size"] == 5
    should = search_kwargs["body"]["query"]["bool"]["should"]
    assert should[0]["multi_match"]["query"] == "apple"
    assert should[0]["multi_match"]["fields"] == ["name^2", "description"]


async def test_search_product_returns_empty_list(monkeypatch) -> None:
    es = AsyncMock()
    es.search.return_value = {"hits": {"hits": []}}
    monkeypatch.setattr(search_module, "es", es)

    assert await search_product("unknown", 10) == []
