import json
from datetime import timedelta
from typing import Any
import redis.asyncio as redis
from app.config import get_settings

settings = get_settings()


class CacheService:
    def __init__(self):
        self.redis_client: redis.Redis | None = None

    async def connect(self):
        try:
            self.redis_client = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
            )
            await self.redis_client.ping()
        except Exception:
            self.redis_client = None

    async def close(self):
        if self.redis_client:
            await self.redis_client.close()

    async def get(self, key: str) -> Any | None:
        if not self.redis_client:
            return None
        try:
            value = await self.redis_client.get(key)
            if value:
                return json.loads(value)
        except Exception:
            pass
        return None

    async def set(self, key: str, value: Any, expire: int | None = None) -> bool:
        if not self.redis_client:
            return False
        try:
            serialized = json.dumps(value, default=str)
            if expire:
                await self.redis_client.setex(key, expire, serialized)
            else:
                await self.redis_client.set(key, serialized)
            return True
        except Exception:
            return False

    async def delete(self, key: str) -> bool:
        if not self.redis_client:
            return False
        try:
            await self.redis_client.delete(key)
            return True
        except Exception:
            return False

    async def exists(self, key: str) -> bool:
        if not self.redis_client:
            return False
        try:
            return await self.redis_client.exists(key) > 0
        except Exception:
            return False

    async def get_or_set(self, key: str, fetch_func, expire: int = 300) -> Any:
        cached = await self.get(key)
        if cached is not None:
            return cached

        value = await fetch_func()
        if value is not None:
            await self.set(key, value, expire)
        return value

    async def invalidate_pattern(self, pattern: str) -> int:
        if not self.redis_client:
            return 0
        try:
            keys = []
            async for key in self.redis_client.scan_iter(match=pattern):
                keys.append(key)
            if keys:
                return await self.redis_client.delete(*keys)
            return 0
        except Exception:
            return 0


cache = CacheService()


async def get_cache() -> CacheService:
    return cache


CACHE_KEYS = {
    "user_profile": "user:profile:{user_id}",
    "user_progress": "user:progress:{user_id}",
    "dashboard": "dashboard:{user_id}",
    "radar": "user:radar:{user_id}",
    "review_queue": "user:review_queue:{user_id}",
    "content_list": "content:list:{content_type}:{page}:{page_size}",
    "knowledge_point": "kp:{kp_id}",
    "lesson": "lesson:{lesson_id}",
    "scene": "scene:{scene_id}",
    "system_stats": "admin:system_stats",
    "learning_trends": "admin:learning_trends",
}

CACHE_EXPIRE = {
    "user_profile": 300,
    "user_progress": 300,
    "dashboard": 120,
    "radar": 600,
    "review_queue": 300,
    "content_list": 600,
    "knowledge_point": 3600,
    "lesson": 3600,
    "scene": 3600,
    "system_stats": 60,
    "learning_trends": 300,
}
