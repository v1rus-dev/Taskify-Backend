import os
from typing import Optional

import redis
from redis import Redis

_redis_client: Optional[Redis] = None


def get_redis_client() -> Redis:
    global _redis_client
    if _redis_client is None:
        host = os.getenv("REDIS_HOST", "redis")
        port = int(os.getenv("REDIS_PORT", 6379))
        username = os.getenv("REDIS_USER")
        password = os.getenv("REDIS_USER_PASSWORD")
        db = int(os.getenv("REDIS_DB", 0))
        _redis_client = redis.Redis(
            host=host,
            port=port,
            username=username,
            password=password,
            db=db,
            decode_responses=True,
        )
    return _redis_client
