from typing import Annotated, Optional

from fastapi import Depends

from product_catalog.adapters.repository import CatalogRepository, ProductRepository, PropertyRepository
from product_catalog.adapters.redis_cache import RedisCache
from product_catalog.service_layer.services import CatalogService, ProductService, PropertyService

from product_catalog.di.repository import get_catalog_repository, get_product_repository, get_property_repository
from product_catalog.di.redis_cache import get_redis_cache


def get_catalog_service(
    repo: Annotated[CatalogRepository, Depends(get_catalog_repository)],
    redis_cache: Annotated[Optional[RedisCache], Depends(get_redis_cache)]
) -> CatalogService:
    return CatalogService(repo=repo, redis_cache=redis_cache)


def get_product_service(
    repo: Annotated[ProductRepository, Depends(get_product_repository)],
    redis_cache: Annotated[Optional[RedisCache], Depends(get_redis_cache)]
) -> ProductService:
    return ProductService(repo=repo, redis_cache=redis_cache)


def get_property_service(
    repo: Annotated[PropertyRepository, Depends(get_property_repository)],
    redis_cache: Annotated[Optional[RedisCache], Depends(get_redis_cache)]
) -> PropertyService:
    return PropertyService(repo=repo, redis_cache=redis_cache)