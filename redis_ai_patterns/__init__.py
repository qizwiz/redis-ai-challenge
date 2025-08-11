"""
Redis AI Patterns - A library for Redis-based AI coordination
"""

from .homoiconic import HomoiconicRedis
from .streams import StreamProcessor
from .semantic import SemanticExtractor
from .development import DevAssistant
from .core import RedisAIBase

__version__ = "0.1.0"
__all__ = [
    "HomoiconicRedis",
    "StreamProcessor",
    "SemanticExtractor",
    "DevAssistant",
    "RedisAIBase",
]
