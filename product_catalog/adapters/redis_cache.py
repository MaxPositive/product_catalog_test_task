import json
from typing import Optional, Any
from redis.asyncio import Redis
from product_catalog.config import settings


class RedisCache:
    def __init__(self):
        self.ttl = 3600
        try:
            self.client = Redis(
                host=settings.redis.host,
                port=settings.redis.port,
                decode_responses=True
            )
        except Exception:
            self.client = None

    async def get(self, key: str) -> Optional[Any]:
        if not self.client:
            return
        cached_data = await self.client.get(key)
        if cached_data:
            return json.loads(cached_data)
        return None

    async def set(self, key: str, value: Any) -> None:
        if not self.client:
            return
        serialized_value = json.dumps(value)
        await self.client.setex(key, self.ttl, serialized_value)

    async def delete(self, key: str) -> None:
        if not self.client:
            return
        await self.client.delete(key)
