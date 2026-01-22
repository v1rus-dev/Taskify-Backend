import json
import logging
import os
from typing import Any, Optional

from redis import Redis

logger = logging.getLogger("app.cache")


class CacheService:
    def __init__(self, client: Redis):
        self.client = client
        self.default_ttl = int(os.getenv("REDIS_CACHE_TTL_SECONDS", 60))

    def get_json(self, key: str) -> Optional[Any]:
        try:
            raw = self.client.get(key)
        except Exception as exc:
            logger.warning("Redis get failed for key=%s: %s", key, exc)
            return None
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return None

    def set_json(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        ttl = self.default_ttl if ttl_seconds is None else ttl_seconds
        try:
            payload = json.dumps(value, ensure_ascii=True)
            self.client.setex(key, ttl, payload)
        except Exception as exc:
            logger.warning("Redis set failed for key=%s: %s", key, exc)

    def delete(self, *keys: str) -> None:
        if not keys:
            return
        try:
            self.client.delete(*keys)
        except Exception as exc:
            logger.warning("Redis delete failed for keys=%s: %s", keys, exc)
