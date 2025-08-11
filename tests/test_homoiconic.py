"""
Tests for HomoiconicRedis - Redis-based Lisp interpreter
"""

import pytest
import json
from unittest.mock import Mock, patch
from redis_ai_patterns.homoiconic import HomoiconicRedis


class TestHomoiconicRedis:

    @pytest.fixture
    def mock_redis(self):
        with patch("redis.Redis") as mock:
            mock_client = Mock()
            mock.return_value = mock_client
            yield mock_client

    @pytest.fixture
    def lisp_engine(self, mock_redis):
        return HomoiconicRedis(namespace="test_lisp")

    def test_initialization(self, lisp_engine):
        """Test proper initialization with builtins"""
        assert "+" in lisp_engine.builtins
        assert "-" in lisp_engine.builtins
        assert "if" in lisp_engine.builtins
        assert "redis-set" in lisp_engine.builtins

    def test_parse_atom_number(self, lisp_engine):
        """Test parsing numeric atoms"""
        assert lisp_engine._parse_atom("42") == 42
        assert lisp_engine._parse_atom("3.14") == 3.14
        assert lisp_engine._parse_atom("-5") == -5

    def test_parse_atom_string(self, lisp_engine):
        """Test parsing string atoms"""
        assert lisp_engine._parse_atom('"hello"') == "hello"
        assert lisp_engine._parse_atom('"hello world"') == "hello world"

    def test_parse_atom_boolean(self, lisp_engine):
        """Test parsing boolean atoms"""
        assert lisp_engine._parse_atom("true") is True
        assert lisp_engine._parse_atom("false") is False
        assert lisp_engine._parse_atom("nil") is False

    def test_parse_atom_symbol(self, lisp_engine):
        """Test parsing symbol atoms"""
        assert lisp_engine._parse_atom("symbol") == "symbol"
        assert lisp_engine._parse_atom("my-function") == "my-function"

    def test_parse_simple_expression(self, lisp_engine):
        """Test parsing simple s-expressions"""
        result = lisp_engine.parse("(+ 1 2)")
        assert result == ["+", 1, 2]

    def test_parse_nested_expression(self, lisp_engine):
        """Test parsing nested s-expressions"""
        result = lisp_engine.parse("(+ 1 (* 2 3))")
        expected = ["+", 1, ["*", 2, 3]]
        assert result == expected

    def test_execute_arithmetic_add(self, lisp_engine):
        """Test arithmetic addition"""
        result = lisp_engine.execute(["+", 1, 2, 3])
        assert result == 6

    def test_execute_arithmetic_multiply(self, lisp_engine):
        """Test arithmetic multiplication"""
        result = lisp_engine.execute(["*", 2, 3, 4])
        assert result == 24

    def test_execute_comparison(self, lisp_engine):
        """Test comparison operations"""
        assert lisp_engine.execute(["=", 5, 5]) is True
        assert lisp_engine.execute(["=", 5, 6]) is False
        assert lisp_engine.execute(["<", 3, 5]) is True
        assert lisp_engine.execute([">", 7, 2]) is True

    def test_execute_logic_operations(self, lisp_engine):
        """Test logical operations"""
        assert lisp_engine.execute(["and", True, True]) is True
        assert lisp_engine.execute(["and", True, False]) is False
        assert lisp_engine.execute(["or", False, True]) is True
        assert lisp_engine.execute(["not", True]) is False

    def test_execute_if_condition(self, lisp_engine):
        """Test if conditional execution"""
        result = lisp_engine.execute(["if", True, "yes", "no"])
        assert result == "yes"

        result = lisp_engine.execute(["if", False, "yes", "no"])
        assert result == "no"

    def test_execute_string_operations(self, lisp_engine):
        """Test string operations"""
        result = lisp_engine.execute(["concat", "hello", " ", "world"])
        assert result == "hello world"

        result = lisp_engine.execute(["length", "test"])
        assert result == 4

    def test_execute_list_operations(self, lisp_engine):
        """Test list operations"""
        result = lisp_engine.execute(["list", 1, 2, 3])
        assert result == [1, 2, 3]

        result = lisp_engine.execute(["first", [1, 2, 3]])
        assert result == 1

        result = lisp_engine.execute(["rest", [1, 2, 3]])
        assert result == [2, 3]

    def test_redis_operations(self, lisp_engine, mock_redis):
        """Test Redis integration operations"""
        # Test redis-set
        result = lisp_engine.execute(["redis-set", "mykey", "myvalue"])
        assert "stored mykey" in result
        mock_redis.set.assert_called()

        # Test redis-get
        mock_redis.get.return_value = json.dumps("myvalue")
        result = lisp_engine.execute(["redis-get", "mykey"])
        assert result == "myvalue"

        # Test redis-exists
        mock_redis.exists.return_value = True
        result = lisp_engine.execute(["redis-exists", "mykey"])
        assert result is True

    def test_store_and_load_code(self, lisp_engine, mock_redis):
        """Test storing and loading executable code"""
        code = ["+", 1, 2, 3]

        lisp_engine.store_code("add_example", code)
        mock_redis.lpush.assert_called_with(
            "test_lisp:code:add_example", json.dumps(code)
        )

        # Mock loading code
        mock_redis.lindex.return_value = json.dumps(code)
        loaded = lisp_engine.load_code("add_example")
        assert loaded == code

    def test_run_stored_code(self, lisp_engine, mock_redis):
        """Test executing stored code"""
        code = ["+", 10, 20, 30]
        mock_redis.lindex.return_value = json.dumps(code)

        result = lisp_engine.run_stored_code("add_example")
        assert result == 60

    def test_unknown_function_error(self, lisp_engine):
        """Test error handling for unknown functions"""
        with pytest.raises(ValueError, match="Unknown function: unknown"):
            lisp_engine.execute(["unknown", 1, 2])

    def test_is_truthy(self, lisp_engine):
        """Test truthiness evaluation"""
        assert lisp_engine._is_truthy(True) is True
        assert lisp_engine._is_truthy(False) is False
        assert lisp_engine._is_truthy(1) is True
        assert lisp_engine._is_truthy(0) is False
        assert lisp_engine._is_truthy("hello") is True
        assert lisp_engine._is_truthy("false") is False
        assert lisp_engine._is_truthy("") is False
