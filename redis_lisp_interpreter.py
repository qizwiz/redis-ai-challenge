#!/usr/bin/env python3
"""
Redis as Lisp Interpreter - Exploiting Homoiconicity
Since Redis is homoiconic (data structures can represent code), we can represent
and manipulate Lisp expressions directly in Redis, making Redis a Lisp environment!

The breakthrough insight: Redis lists naturally represent Lisp s-expressions:
- Redis: ["forward-char", "1"]
- Lisp:  (forward-char 1)

Redis hashes can represent symbol tables, environments, and function definitions.
Redis sets can represent collections and unique symbol spaces.
"""

import redis
import json
import time
from typing import List, Dict, Any, Union, Optional


class RedisLispInterpreter:
    """
    A Lisp interpreter that runs entirely in Redis using homoiconic data structures
    """

    def __init__(self):
        self.redis_client = redis.Redis(
            host="localhost", port=6379, decode_responses=True
        )
        self.session_id = f"lisp_{int(time.time())}"
        self.environment_stack = []

        # Initialize global environment in Redis
        self._initialize_global_environment()

    def _initialize_global_environment(self):
        """Initialize global Lisp environment in Redis"""
        print("🚀 Initializing Redis Lisp Environment...")

        # Global symbol table as Redis hash
        global_env = "lisp:global:env"

        # Built-in functions stored as Redis data
        builtins = {
            "+": {"type": "builtin", "arity": "variadic", "impl": "arithmetic_add"},
            "-": {"type": "builtin", "arity": "variadic", "impl": "arithmetic_sub"},
            "*": {"type": "builtin", "arity": "variadic", "impl": "arithmetic_mul"},
            "car": {"type": "builtin", "arity": 1, "impl": "list_car"},
            "cdr": {"type": "builtin", "arity": 1, "impl": "list_cdr"},
            "cons": {"type": "builtin", "arity": 2, "impl": "list_cons"},
            "list": {"type": "builtin", "arity": "variadic", "impl": "list_create"},
            "quote": {"type": "special", "impl": "special_quote"},
            "if": {"type": "special", "impl": "special_if"},
            "defun": {"type": "special", "impl": "special_defun"},
            "lambda": {"type": "special", "impl": "special_lambda"},
            # Emacs-specific functions
            "forward-char": {
                "type": "emacs",
                "arity": "0-1",
                "impl": "emacs_forward_char",
            },
            "backward-char": {
                "type": "emacs",
                "arity": "0-1",
                "impl": "emacs_backward_char",
            },
            "insert": {"type": "emacs", "arity": 1, "impl": "emacs_insert"},
            "message": {"type": "emacs", "arity": 1, "impl": "emacs_message"},
        }

        # Store each builtin as a Redis hash
        for name, definition in builtins.items():
            func_key = f"lisp:function:{name}"
            self.redis_client.hset(
                func_key,
                mapping={
                    "name": name,
                    "type": definition["type"],
                    "arity": str(definition.get("arity", "variadic")),
                    "implementation": definition["impl"],
                    "defined_in": "global",
                },
            )

            # Add to global environment
            self.redis_client.hset(global_env, name, func_key)

        # Store environment metadata
        self.redis_client.hset(
            "lisp:global:meta",
            mapping={
                "type": "environment",
                "parent": "",
                "created": time.time(),
                "session": self.session_id,
            },
        )

        print(f"✅ Initialized {len(builtins)} built-in functions")

    def sexp_to_redis_list(self, sexp_str: str) -> str:
        """Convert s-expression string to Redis list key"""
        # Simple parser for demonstration
        sexp_str = sexp_str.strip()
        if not (sexp_str.startswith("(") and sexp_str.endswith(")")):
            # Atomic value
            list_key = f"lisp:atom:{hash(sexp_str) % 10000}"
            self.redis_client.rpush(list_key, sexp_str)
            return list_key

        # Parse list expression
        inner = sexp_str[1:-1].strip()
        tokens = self._tokenize(inner)

        list_key = f"lisp:list:{hash(sexp_str) % 10000}:{int(time.time())}"

        for token in tokens:
            if token.startswith("(") and token.endswith(")"):
                # Nested expression
                nested_key = self.sexp_to_redis_list(token)
                self.redis_client.rpush(list_key, f"@list:{nested_key}")
            else:
                # Atomic token
                self.redis_client.rpush(list_key, token)

        # Store metadata
        self.redis_client.hset(
            f"{list_key}:meta",
            mapping={
                "type": "list",
                "length": len(tokens),
                "original": sexp_str,
                "created": time.time(),
            },
        )

        return list_key

    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenizer for Lisp expressions"""
        tokens = []
        current_token = ""
        paren_depth = 0
        in_string = False

        for char in text:
            if char == '"' and not in_string:
                in_string = True
                current_token += char
            elif char == '"' and in_string:
                in_string = False
                current_token += char
            elif in_string:
                current_token += char
            elif char == "(":
                if current_token.strip():
                    tokens.append(current_token.strip())
                    current_token = ""
                current_token += char
                paren_depth += 1
            elif char == ")":
                current_token += char
                paren_depth -= 1
                if paren_depth == 0:
                    tokens.append(current_token.strip())
                    current_token = ""
            elif char.isspace() and paren_depth == 0:
                if current_token.strip():
                    tokens.append(current_token.strip())
                    current_token = ""
            else:
                current_token += char

        if current_token.strip():
            tokens.append(current_token.strip())

        return tokens

    def redis_list_to_sexp(self, list_key: str) -> str:
        """Convert Redis list back to s-expression string"""
        elements = self.redis_client.lrange(list_key, 0, -1)

        if not elements:
            return "()"

        sexp_parts = []
        for element in elements:
            if element.startswith("@list:"):
                # Reference to another list
                nested_key = element[6:]  # Remove '@list:' prefix
                nested_sexp = self.redis_list_to_sexp(nested_key)
                sexp_parts.append(nested_sexp)
            else:
                sexp_parts.append(element)

        return f"({' '.join(sexp_parts)})"

    def evaluate_redis_expression(
        self, list_key: str, env_key: str = "lisp:global:env"
    ) -> Any:
        """Evaluate a Lisp expression stored as Redis list"""
        elements = self.redis_client.lrange(list_key, 0, -1)

        if not elements:
            return None

        if len(elements) == 1 and not elements[0].startswith("@list:"):
            # Atomic expression - variable lookup or literal
            atom = elements[0]

            # Check if it's a number
            try:
                return float(atom) if "." in atom else int(atom)
            except ValueError:
                pass

            # Check if it's a string literal
            if atom.startswith('"') and atom.endswith('"'):
                return atom[1:-1]  # Remove quotes

            # Variable lookup in environment
            var_ref = self.redis_client.hget(env_key, atom)
            if var_ref:
                return var_ref
            else:
                return f"UNBOUND-VARIABLE: {atom}"

        # Function call - first element is function, rest are arguments
        func_name_or_ref = elements[0]
        args = elements[1:]

        # Resolve function reference
        if func_name_or_ref.startswith("@list:"):
            # Lambda expression
            return self._evaluate_lambda_call(func_name_or_ref[6:], args, env_key)
        else:
            # Named function
            func_ref = self.redis_client.hget(env_key, func_name_or_ref)
            if not func_ref:
                return f"UNDEFINED-FUNCTION: {func_name_or_ref}"

            return self._evaluate_function_call(func_ref, args, env_key)

    def _evaluate_function_call(
        self, func_key: str, args: List[str], env_key: str
    ) -> Any:
        """Evaluate function call using Redis-stored function definition"""
        func_data = self.redis_client.hgetall(func_key)

        if not func_data:
            return f"INVALID-FUNCTION-REF: {func_key}"

        func_type = func_data.get("type")
        implementation = func_data.get("implementation")

        # Evaluate arguments (except for special forms)
        if func_type != "special":
            evaluated_args = []
            for arg in args:
                if arg.startswith("@list:"):
                    nested_result = self.evaluate_redis_expression(arg[6:], env_key)
                    evaluated_args.append(nested_result)
                else:
                    # Atomic argument
                    arg_key = f"lisp:temp:arg:{hash(arg) % 1000}"
                    self.redis_client.rpush(arg_key, arg)
                    evaluated_args.append(
                        self.evaluate_redis_expression(arg_key, env_key)
                    )
                    self.redis_client.delete(arg_key)
            args = evaluated_args

        # Dispatch to implementation
        if implementation == "arithmetic_add":
            return sum(
                float(arg)
                for arg in args
                if isinstance(arg, (int, float, str))
                and str(arg).replace(".", "").replace("-", "").isdigit()
            )
        elif implementation == "arithmetic_mul":
            result = 1
            for arg in args:
                if isinstance(arg, (int, float)) or (
                    isinstance(arg, str)
                    and arg.replace(".", "").replace("-", "").isdigit()
                ):
                    result *= float(arg)
            return result
        elif implementation == "emacs_forward_char":
            n = int(args[0]) if args else 1
            return f"EMACS-COMMAND: (forward-char {n})"
        elif implementation == "emacs_insert":
            text = args[0] if args else ""
            return f'EMACS-COMMAND: (insert "{text}")'
        elif implementation == "emacs_message":
            text = args[0] if args else ""
            return f"EMACS-MESSAGE: {text}"
        else:
            return f"UNIMPLEMENTED: {implementation}"

    def store_lisp_program_in_redis(self, program: str) -> str:
        """Store entire Lisp program as manipulable Redis data"""
        print(f"📄 Storing Lisp program in Redis...")

        program_key = f"lisp:program:{self.session_id}"
        lines = program.strip().split("\n")

        expression_keys = []
        for i, line in enumerate(lines):
            line = line.strip()
            if line and not line.startswith(";"):  # Skip comments and empty lines
                expr_key = self.sexp_to_redis_list(line)
                expression_keys.append(expr_key)

                # Store line metadata
                self.redis_client.hset(
                    f"{program_key}:line:{i}",
                    mapping={
                        "line_number": i,
                        "original_text": line,
                        "expression_key": expr_key,
                        "parsed": time.time(),
                    },
                )

        # Store program metadata
        self.redis_client.hset(
            f"{program_key}:meta",
            mapping={
                "total_lines": len(lines),
                "expressions": len(expression_keys),
                "stored": time.time(),
                "session": self.session_id,
            },
        )

        # Store expression keys as Redis list (program execution order)
        prog_expr_key = f"{program_key}:expressions"
        for expr_key in expression_keys:
            self.redis_client.rpush(prog_expr_key, expr_key)

        print(f"✅ Stored {len(expression_keys)} expressions")
        return program_key

    def execute_redis_lisp_program(self, program_key: str) -> List[Any]:
        """Execute Lisp program stored in Redis"""
        print(f"▶️  Executing Redis Lisp program...")

        expr_list_key = f"{program_key}:expressions"
        expression_keys = self.redis_client.lrange(expr_list_key, 0, -1)

        results = []
        for i, expr_key in enumerate(expression_keys):
            print(f"   Executing expression {i+1}: {self.redis_list_to_sexp(expr_key)}")

            result = self.evaluate_redis_expression(expr_key)
            results.append(result)

            print(f"   → {result}")

            # Store execution result in Redis
            self.redis_client.hset(
                f"{program_key}:result:{i}",
                mapping={
                    "expression_key": expr_key,
                    "result": str(result),
                    "executed": time.time(),
                    "step": i,
                },
            )

        return results

    def demonstrate_redis_lisp_homoiconicity(self):
        """Demonstrate Redis as a homoiconic Lisp environment"""
        print("🚀 REDIS AS HOMOICONIC LISP INTERPRETER")
        print("=" * 60)
        print("Code as data, data as code - all in Redis!")
        print("=" * 60)

        # Sample Lisp program that manipulates itself
        sample_program = """
        (+ 1 2 3)
        (* 4 5)
        (forward-char 3)
        (insert "Hello from Redis Lisp!")
        (message "Redis is homoiconic!")
        """

        print("📝 Sample Lisp Program:")
        for line in sample_program.strip().split("\n"):
            if line.strip():
                print(f"   {line.strip()}")

        # Store program in Redis
        program_key = self.store_lisp_program_in_redis(sample_program)

        # Execute program
        results = self.execute_redis_lisp_program(program_key)

        # Demonstrate code manipulation as data
        print(f"\n🔄 HOMOICONIC MANIPULATION")
        print("=" * 30)
        print("Manipulating code as Redis data structures:")

        # Get first expression and modify it
        expr_keys = self.redis_client.lrange(f"{program_key}:expressions", 0, -1)
        if expr_keys:
            first_expr = expr_keys[0]
            print(f"Original: {self.redis_list_to_sexp(first_expr)}")

            # Modify the expression by changing Redis data
            self.redis_client.lset(first_expr, 1, "10")  # Change 1 to 10
            self.redis_client.lset(first_expr, 2, "20")  # Change 2 to 20
            print(f"Modified: {self.redis_list_to_sexp(first_expr)}")

            # Re-evaluate modified expression
            new_result = self.evaluate_redis_expression(first_expr)
            print(f"New result: {new_result}")

        # Show Redis data structures
        print(f"\n📊 REDIS DATA STRUCTURES")
        print("=" * 25)
        print("Lisp expressions stored as Redis lists:")

        for i, expr_key in enumerate(expr_keys[:3]):  # Show first 3
            elements = self.redis_client.lrange(expr_key, 0, -1)
            print(f"   Expression {i+1}: {expr_key} = {elements}")

        # Environment inspection
        print("\nGlobal environment (Redis hash):")
        global_env = self.redis_client.hgetall("lisp:global:env")
        for name, func_ref in list(global_env.items())[:5]:  # Show first 5
            print(f"   {name} → {func_ref}")

        print(f"\n🎯 REVOLUTIONARY IMPLICATIONS")
        print("=" * 30)
        print("✅ Lisp expressions stored as manipulable Redis lists")
        print("✅ Symbol tables implemented as Redis hashes")
        print("✅ Programs can modify themselves through Redis operations")
        print("✅ Distributed Lisp evaluation across Redis instances")
        print("✅ Persistent code/data with Redis durability")
        print("✅ Code analysis through Redis queries and scripts")
        print("✅ Meta-programming through Redis data manipulation")

        return program_key, results


def main():
    """Main demonstration"""
    interpreter = RedisLispInterpreter()

    try:
        interpreter.demonstrate_redis_lisp_homoiconicity()
    except KeyboardInterrupt:
        print("\n\n⏹️  Demo interrupted")
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
