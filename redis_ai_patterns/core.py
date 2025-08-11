"""
Core Redis AI utilities and base classes
"""

import redis
import json
import time
from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod


class RedisAIBase(ABC):
    """Base class for Redis AI components"""

    def __init__(
        self,
        redis_host: str = "localhost",
        redis_port: int = 6379,
        namespace: str = None,
    ):
        self.redis_client = redis.Redis(
            host=redis_host, port=redis_port, decode_responses=True
        )
        self.namespace = namespace or self.__class__.__name__.lower()
        self.session_id = f"{self.namespace}_{int(time.time())}"

    def key(self, suffix: str) -> str:
        """Generate namespaced Redis key"""
        return f"{self.namespace}:{suffix}"

    def store_json(self, key: str, data: Any) -> None:
        """Store JSON data in Redis"""
        self.redis_client.set(self.key(key), json.dumps(data))

    def get_json(self, key: str) -> Any:
        """Retrieve JSON data from Redis"""
        data = self.redis_client.get(self.key(key))
        return json.loads(data) if data else None

    def ping(self) -> bool:
        """Test Redis connection"""
        try:
            self.redis_client.ping()
            return True
        except:
            return False
