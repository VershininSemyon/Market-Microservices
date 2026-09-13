
from uuid import UUID

from elasticsearch import AsyncElasticsearch

from src.config import settings

es = AsyncElasticsearch([settings.elastic_url])


async def create_products_index():
    if not await es.indices.exists(index=settings.PRODUCTS_INDEX):
        await es.indices.create(
            index=settings.PRODUCTS_INDEX,
            body={
                "settings": {
                    "analysis": {
                        "analyzer": {
                            "product_analyzer": {
                                "type": "custom",
                                "tokenizer": "standard",
                                "filter": [
                                    "lowercase",
                                    "english_stemmer",
                                    "russian_stemmer"
                                ]
                            }
                        },
                        "filter": {
                            "english_stemmer": {
                                "type": "stemmer",
                                "language": "english"
                            },
                            "russian_stemmer": {
                                "type": "stemmer",
                                "language": "russian"
                            }
                        }
                    }
                },
                "mappings": {
                    "properties": {
                        "id": {"type": "text"},
                        "name": {
                            "type": "text",
                            "analyzer": "product_analyzer"
                        },
                        "description": {
                            "type": "text",
                            "analyzer": "product_analyzer"
                        }
                    }
                }
            }
        )


async def index_product(product_id: UUID, name: str, description: str):
    await es.index(
        index=settings.PRODUCTS_INDEX,
        id=str(product_id),
        document={
            "id": str(product_id),
            "name": name,
            "description": description
        }
    )


async def delete_product_index(product_id: UUID):
    await es.delete(
        index=settings.PRODUCTS_INDEX,
        id=str(product_id),
        ignore=[404]
    )


async def search_product(query: str):
    result = await es.search(
        index=settings.PRODUCTS_INDEX,
        body={
            "query": {
                "bool": {
                    "should": [
                        {
                            "multi_match": {
                                "query": query,
                                "fields": ["name^2", "description"],
                                "fuzziness": "AUTO",
                                "type": "best_fields"
                            }
                        },
                        {
                            "multi_match": {
                                "query": query,
                                "fields": ["name^2", "description"],
                                "type": "bool_prefix"
                            }
                        }
                    ]
                }
            }
        }
    )

    return [hit["_id"] for hit in result["hits"]["hits"]]
