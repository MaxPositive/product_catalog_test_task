from product_catalog.adapters.repository import CatalogRepository, ProductRepository, PropertyRepository
from product_catalog.adapters.redis_cache import RedisCache
from product_catalog.domain.dto import *
from product_catalog.domain.models import PropertyType


class CatalogService:
    def __init__(self, repo: CatalogRepository, redis_cache: Optional[RedisCache]):
        self.repo = repo
        self.redis_cache = redis_cache

    async def get_catalog(
        self,
        page: int,
        page_size: int = 10,
        name: Optional[str] = None,
        sort: Optional[str] = "uid",
        property_filters: Optional[dict[str, list[str] | dict[str, int]]] = None
    ) -> CatalogResponse:
        cache_key = None
        if self.redis_cache:
            cache_key = f"catalog:page={page}:size={page_size}:name={name}:sort={sort}"
            if property_filters:
                filter_str = ":".join(
                    f"{k}={','.join(v) if isinstance(v, list) else f'from={v.get('from', '')},to={v.get('to', '')}'}" for
                    k, v in sorted(property_filters.items()))
                cache_key += f":filters={filter_str}"

            cached_result = await self.redis_cache.get(cache_key)
            if cached_result:
                return CatalogResponse(**cached_result)

        products, total_count = await self.repo.get_all(
            page=page,
            page_size=page_size,
            name=name,
            sort=sort,
            property_filters=property_filters
        )

        product_responses = [
            ProductResponse(
                uid=product.uid,
                name=product.name,
                properties=[
                    ProductPropertyResponse(
                        uid=prop.property.uid,
                        name=prop.property.name,
                        value_uid=prop.value_uid,
                        value=prop.value.value if prop.value else prop.int_value
                    )
                    for prop in product.properties
                ]
            )
            for product in products
        ]

        response = CatalogResponse(products=product_responses, count=total_count)
        if self.redis_cache:
            await self.redis_cache.set(cache_key, response.model_dump())

        return response

    async def get_filter_stats(
        self,
        name: Optional[str] = None,
        property_filters: Optional[dict[str, list[str] | dict[str, int]]] = None
    ) -> FilterStatsResponse:
        stats = await self.repo.get_filter_stats(name=name, property_filters=property_filters)

        prefixed_stats = {"count": stats["count"]}
        for key, value in stats.items():
            if key != "count":
                prefixed_stats[f"property_{key}"] = value

        return FilterStatsResponse(**prefixed_stats)


class ProductService:
    def __init__(self, repo: ProductRepository, redis_cache: Optional[RedisCache]):
        self.repo = repo
        self.redis_cache = redis_cache

    async def get_product(self, product_uid: str) -> ProductResponse:
        product = await self.repo.get(product_uid)
        product_response = ProductResponse(
            uid=product.uid,
            name=product.name,
            properties=[
                ProductPropertyResponse(
                    uid=prop.property.uid,
                    name=prop.property.name,
                    value_uid=prop.value_uid,
                    value=prop.value.value if prop.value else prop.int_value
                )
                for prop in product.properties
            ]
        )
        return product_response

    async def create_product(self, product_data: ProductCreate) -> ProductResponse:
        product = await self.repo.add(product_data)
        if self.redis_cache:
            cache_keys = await self.redis_cache.client.keys("catalog:*")
            for key in cache_keys:
                await self.redis_cache.delete(key)

        product_response = ProductResponse(
            uid=product.uid,
            name=product.name,
            properties=[
                ProductPropertyResponse(
                    uid=prop.property.uid,
                    name=prop.property.name,
                    value_uid=prop.value_uid,
                    value=prop.value.value if prop.value else prop.int_value
                )
                for prop in product.properties
            ]
        )
        return product_response

    async def delete_product(self, product_uid: str) -> None:
        await self.repo.delete(product_uid)

        if self.redis_cache:
            cache_keys = await self.redis_cache.client.keys("catalog:*")
            for key in cache_keys:
                await self.redis_cache.delete(key)


class PropertyService:
    def __init__(self, repo: PropertyRepository, redis_cache: Optional[RedisCache]):
        self.repo = repo
        self.redis_cache = redis_cache

    async def create_property(self, property_data: PropertyCreate) -> dict[str, Any]:
        property = await self.repo.add(property_data)

        if self.redis_cache:
            cache_keys = await self.redis_cache.client.keys("catalog:*")
            for key in cache_keys:
                await self.redis_cache.delete(key)

        response = {
            "uid": property.uid,
            "name": property.name,
            "type": property.type.value.lower()
        }
        if property.type == PropertyType.LIST:
            response["values"] = [
                {"value_uid": value.uid, "value": value.value}
                for value in property.values
            ]
        return response

    async def delete_property(self, property_uid: str) -> None:
        await self.repo.delete(property_uid)

        if self.redis_cache:
            cache_keys = await self.redis_cache.client.keys("catalog:*")
            for key in cache_keys:
                await self.redis_cache.delete(key)
