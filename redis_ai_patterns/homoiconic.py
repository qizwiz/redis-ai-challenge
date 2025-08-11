"""
Homoiconic Redis - Code as data, data as code
Redis-based Lisp interpreter for AI coordination
"""

import redis
import json
import re
from typing import Dict, List, Any, Union, Callable
from .core import RedisAIBase


class HomoiconicRedis(RedisAIBase):
    """Redis-based homoiconic programming environment"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._init_builtins()

    def _init_builtins(self) -> None:
        """Initialize built-in functions"""
        self.builtins = {
            # Arithmetic
            "+": lambda *args: sum(float(x) for x in args),
            "-": lambda *args: (
                float(args[0]) - sum(float(x) for x in args[1:])
                if len(args) > 1
                else -float(args[0])
            ),
            "*": lambda *args: self._multiply(*args),
            "/": lambda *args: self._divide(*args),
            # Comparison
            "=": lambda x, y: float(x) == float(y),
            "<": lambda x, y: float(x) < float(y),
            ">": lambda x, y: float(x) > float(y),
            # Logic
            "and": lambda *args: all(self._is_truthy(x) for x in args),
            "or": lambda *args: any(self._is_truthy(x) for x in args),
            "not": lambda x: not self._is_truthy(x),
            # Control flow
            "if": self._if_builtin,
            # Helper for truthiness
            "is-truthy": self._is_truthy,
            # String operations
            "concat": lambda *args: "".join(str(x) for x in args),
            "length": lambda s: len(str(s)),
            # List operations
            "list": lambda *args: list(args),
            "first": lambda lst: lst[0] if lst else None,
            "rest": lambda lst: lst[1:] if len(lst) > 1 else [],
            # Redis operations
            "redis-set": self._redis_set,
            "redis-get": self._redis_get,
            "redis-exists": self._redis_exists,
        }

    def _redis_set(self, key: str, value: Any) -> str:
        self.redis_client.set(self.key(key), json.dumps(value))
        return f"stored {key}"

    def _redis_get(self, key: str) -> Any:
        data = self.redis_client.get(self.key(key))
        return json.loads(data) if data else None

    def _redis_exists(self, key: str) -> bool:
        return bool(self.redis_client.exists(self.key(key)))

    def _if_builtin(
        self, condition: Any, true_expr: Any, false_expr: Any = None
    ) -> Any:
        """Built-in 'if' function"""
        if self._is_truthy(self.execute(condition)):
            return self.execute(true_expr)
        elif false_expr is not None:
            return self.execute(false_expr)
        return None

    def _is_truthy(self, value: Any) -> bool:
        """Determine if a value is truthy"""
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value != 0
        if isinstance(value, str):
            return bool(value) and value.lower() not in ("false", "nil")
        if isinstance(value, (list, dict)):
            return bool(value)
        return False

    def _multiply(self, *args) -> Union[int, float]:
        """Helper for multiplication"""
        res = 1
        for x in args:
            res *= float(x)
        return res

    def _divide(self, *args) -> Union[int, float]:
        """Helper for division"""
        if not args:
            raise ValueError("Division requires at least one argument")
        res = float(args[0])
        for x in args[1:]:
            if float(x) == 0:
                raise ZeroDivisionError("Division by zero")
            res /= float(x)
        return res

    def _parse_tokens(self, tokens: List[str]) -> List[Any]:
        """Parse a list of tokens into expressions"""
        parsed_expressions = []
        i = 0
        while i < len(tokens):
            token = tokens[i]
            if token.startswith("(") and token.endswith(")"):
                # Nested expression
                parsed_expressions.append(self.parse(token))
            else:
                # Atom
                parsed_expressions.append(self._parse_atom(token))
            i += 1
        return parsed_expressions

    def parse(self, code: str) -> Any:
        """Parse Lisp expression from string"""
        code = code.strip()
        if not code:
            return None

        if code.startswith("(") and code.endswith(")"):
            # Parse list expression
            inner = code[1:-1].strip()
            if not inner:
                return []

            tokens = self._tokenize(inner)
            return self._parse_tokens(tokens)
        else:
            # Parse atom
            return self._parse_atom(code)

    def _tokenize(self, code: str) -> List[str]:
        """Tokenize Lisp code"""
        tokens = []
        current = ""
        in_string = False

        i = 0
        while i < len(code):
            char = code[i]

            if char == '"' and not in_string:
                in_string = True
                current += char
            elif char == '"' and in_string:
                in_string = False
                current += char
            elif in_string:
                current += char
            elif char == "(":
                if current.strip():
                    tokens.append(current.strip())
                    current = ""
                # Find matching closing paren
                paren_count = 1
                sub_expr = ""
                i += 1
                while i < len(code) and paren_count > 0:
                    if code[i] == "(":
                        paren_count += 1
                    elif code[i] == ")":
                        paren_count -= 1
                    if paren_count > 0:
                        sub_expr += code[i]
                    i += 1
                tokens.append(f"({sub_expr})")
                i -= 1  # Back up one since we'll increment at end of loop
            elif char.isspace():
                if current.strip():
                    tokens.append(current.strip())
                    current = ""
            else:
                current += char

            i += 1

        if current.strip():
            tokens.append(current.strip())

        return tokens

    def _parse_atom(self, atom: str) -> Any:
        """Parse atomic expression"""
        atom = atom.strip()

        # String literal
        if atom.startswith('"') and atom.endswith('"'):
            return atom[1:-1]

        # Number
        try:
            if "." in atom:
                return float(atom)
            return int(atom)
        except ValueError:
            pass

        # Boolean
        if atom.lower() == "true":
            return True
        if atom.lower() in ("false", "nil"):
            return False

        # Symbol
        return atom

    def execute(self, expression: Any) -> Any:
        """Execute Lisp expression"""
        if not isinstance(expression, list):
            return expression

        if not expression:
            return None

        func_name = expression[0]
        args = expression[1:]

        # Look up function
        if func_name in self.builtins:
            func = self.builtins[func_name]
            # Evaluate arguments for most functions
            if func_name not in ("if", "and", "or", "first", "rest"):
                evaluated_args = [
                    self.execute(arg) if isinstance(arg, list) else arg for arg in args
                ]
                return func(*evaluated_args)
            else:
                return func(*args)
        else:
            raise ValueError(f"Unknown function: {func_name}")

    def store_code(self, name: str, code: Any) -> None:
        """Store executable code in Redis"""
        self.redis_client.lpush(self.key(f"code:{name}"), json.dumps(code))

    def load_code(self, name: str) -> Any:
        """Load executable code from Redis"""
        data = self.redis_client.lindex(self.key(f"code:{name}"), 0)
        return json.loads(data) if data else None

    def run_stored_code(self, name: str) -> Any:
        """Execute code stored in Redis"""
        code = self.load_code(name)
        if code:
            return self.execute(code)
        return None
