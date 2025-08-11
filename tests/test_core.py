"""
Tests for core Redis AI functionality
"""

import pytest
import redis
import json
import time
from unittest.mock import Mock, patch
from redis_ai_patterns.core import RedisAIBase


class TestRedisAIBase:

    @pytest.fixture
    def mock_redis(self):
        with patch("redis.Redis") as mock:
            mock_client = Mock()
            mock.return_value = mock_client
            yield mock_client

    @pytest.fixture
    def base_instance(self, mock_redis):
        return RedisAIBase(redis_host="localhost", redis_port=6379, namespace="test")

    def test_initialization(self, base_instance, mock_redis):
        """Test proper initialization"""
        assert base_instance.namespace == "test"
        assert base_instance.session_id.startswith("test_")
        mock_redis.ping.assert_not_called()  # Not called during init

    def test_key_generation(self, base_instance):
        """Test namespaced key generation"""
        key = base_instance.key("example")
        assert key == "test:example"

    def test_store_json(self, base_instance, mock_redis):
        """Test JSON storage in Redis"""
        test_data = {"key": "value", "number": 42}
        base_instance.store_json("test_key", test_data)

        mock_redis.set.assert_called_once_with("test:test_key", json.dumps(test_data))

    def test_get_json(self, base_instance, mock_redis):
        """Test JSON retrieval from Redis"""
        test_data = {"key": "value"}
        mock_redis.get.return_value = json.dumps(test_data)

        result = base_instance.get_json("test_key")

        assert result == test_data
        mock_redis.get.assert_called_once_with("test:test_key")

    def test_get_json_none(self, base_instance, mock_redis):
        """Test JSON retrieval when key doesn't exist"""
        mock_redis.get.return_value = None

        result = base_instance.get_json("nonexistent")

        assert result is None

    def test_ping_success(self, base_instance, mock_redis):
        """Test successful Redis ping"""
        mock_redis.ping.return_value = True

        result = base_instance.ping()

        assert result is True
        mock_redis.ping.assert_called_once()

    def test_ping_failure(self, base_instance, mock_redis):
        """Test Redis ping failure"""
        mock_redis.ping.side_effect = redis.ConnectionError("Connection failed")

        result = base_instance.ping()

        assert result is False

    def test_default_namespace(self):
        """Test default namespace generation"""
        with patch("redis.Redis"):
            instance = RedisAIBase()
            assert instance.namespace == "redisaibase"  # lowercased class name
