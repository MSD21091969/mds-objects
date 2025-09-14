# src/core/managers/cache_manager.py

import logging
import redis
import os
import json
from typing import Optional, Any

logger = logging.getLogger(__name__)

class CacheManager:
    """
    Manages the connection to a Redis cache for caching frequently accessed data.
    """
    def __init__(self):
        self._client = None
        self.redis_host = os.getenv("REDIS_HOST", "localhost")
        self.redis_port = int(os.getenv("REDIS_PORT", 6379))
        self._connect()

    def _connect(self):
        try:
            # decode_responses=True zorgt ervoor dat we strings terugkrijgen
            self._client = redis.Redis(
                host=self.redis_host,
                port=self.redis_port,
                db=0,
                decode_responses=True
            )
            self._client.ping()
            logger.info(f"Successfully connected to Redis at {self.redis_host}:{self.redis_port}.")
        except redis.exceptions.ConnectionError as e:
            logger.error(f"Error connecting to Redis: {e}", exc_info=True)
            self._client = None

    def get(self, key: str) -> Optional[Any]:
        """Gets a value from the cache and deserializes it from JSON."""
        if not self._client:
            return None
        try:
            cached_value = self._client.get(key)
            if cached_value:
                return json.loads(cached_value)
            return None
        except Exception as e:
            logger.error(f"Error getting key '{key}' from Redis: {e}", exc_info=True)
            return None

    def set(self, key: str, value: Any, ttl: int = 3600):
        """Serializes a value to JSON and sets it in the cache with a TTL."""
        if not self._client:
            return
        try:
            serialized_value = json.dumps(value)
            self._client.setex(key, ttl, serialized_value)
        except Exception as e:
            logger.error(f"Error setting key '{key}' in Redis: {e}", exc_info=True)

    def delete(self, key: str):
        """Deletes a key from the cache."""
        if not self._client:
            return
        try:
            self._client.delete(key)
        except Exception as e:
            logger.error(f"Error deleting key '{key}' from Redis: {e}", exc_info=True)
