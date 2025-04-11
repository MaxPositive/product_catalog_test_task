from typing import Optional

from product_catalog.adapters.redis_cache import RedisCache


def get_redis_cache() -> Optional[RedisCache]:
    instance = RedisCache()
    if instance.client:
        return instance
    return None
