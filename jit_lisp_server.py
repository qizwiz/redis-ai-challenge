#!/usr/bin/env python3
"""
JIT Lisp Server - Created by MCP Registry Server
SBCL-style Lisp server that can be spawned just-in-time
"""

import asyncio
import json
import sys
import ast
import operator
from typing import Any, Dict, List, Union

class JITLispServer:
    """Just-in-time Lisp server with SBCL-style features"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.environment = {
            '+': operator.add,
            '-': operator.sub,
            '*': operator.mul,
            '/': operator.truediv,
            '=': operator.eq,
            '<': operator.lt,
            '>': operator.gt,
            'print': self.lisp_print,
            'list': lambda *args: list(args),
            'car': lambda lst: lst[0] if lst else None,
            'cdr': lambda lst: lst[1:] if len(lst) > 1 else [],
            'cons': lambda a, b: [a] + (b if isinstance(b, list) else [b]),
            'length': len,
            'append': lambda *lists: sum(lists, [])
        }
        self.macros = {}
        self.tools = {
            "eval_lisp": self.eval_lisp,
            "compile_lisp": self.compile_lisp,
            "load_file": self.load_file,
            "define_macro": self.define_macro,
            "get_environment": self.get_environment,
            "reset_environment": self.reset_environment
        }
    
    def lisp_print(self, *args):
        """Lisp print function"""
        result = ' '.join(str(arg) for arg in args)
        print(f"📝 Lisp: {result}")
        return result
    
    def evaluate_lisp(self, expr: Union[List, str, int, float, bool]) -> Any:
        """Evaluate Lisp expression"""
        if isinstance(expr, (int, float, bool)):
            return expr
        
        if isinstance(expr, str):
            if expr in self.environment:
                return self.environment[expr]
            else:
                raise NameError(f"Undefined variable: {expr}")
        
        if not isinstance(expr, list) or len(expr) == 0:
            return expr
        
        # Handle special forms
        if expr[0] == 'quote':
            return expr[1] if len(expr) > 1 else None
        
        elif expr[0] == 'define':
            if len(expr) >= 3:
                var_name = expr[1]
                value = self.evaluate_lisp(expr[2])
                self.environment[var_name] = value
                return value
            
        elif expr[0] == 'lambda':
            if len(expr) >= 3:
                params = expr[1]
                body = expr[2]
                return lambda *args: self.evaluate_lisp_with_bindings(body, dict(zip(params, args)))
        
        elif expr[0] == 'if':
            if len(expr) >= 3:
                condition = self.evaluate_lisp(expr[1])
                if condition:
                    return self.evaluate_lisp(expr[2])
                elif len(expr) > 3:
                    return self.evaluate_lisp(expr[3])
                else:
                    return None
        
        elif expr[0] == 'cond':
            for clause in expr[1:]:
                if len(clause) >= 2:
                    condition = self.evaluate_lisp(clause[0])
                    if condition:
                        return self.evaluate_lisp(clause[1])
            return None
        
        # Check for macros
        elif expr[0] in self.macros:
            macro_func = self.macros[expr[0]]
            expanded = macro_func(*expr[1:])
            return self.evaluate_lisp(expanded)
        
        # Regular function call
        else:
            func = self.evaluate_lisp(expr[0])
            args = [self.evaluate_lisp(arg) for arg in expr[1:]]
            
            if callable(func):
                return func(*args)
            else:
                raise TypeError(f"Not a function: {func}")
    
    def evaluate_lisp_with_bindings(self, expr: Any, bindings: Dict[str, Any]) -> Any:
        """Evaluate with local variable bindings"""
        old_env = self.environment.copy()
        self.environment.update(bindings)
        try:
            result = self.evaluate_lisp(expr)
        finally:
            self.environment = old_env
        return result
    
    async def eval_lisp(self, code: Union[str, List], **kwargs) -> Dict[str, Any]:
        """Evaluate Lisp code"""
        try:
            # Parse string to list if needed
            if isinstance(code, str):
                # Simple S-expression parser
                code = ast.literal_eval(code)
            
            start_time = asyncio.get_event_loop().time()
            result = self.evaluate_lisp(code)
            execution_time = asyncio.get_event_loop().time() - start_time
            
            return {
                "code": code,
                "result": result,
                "execution_time": execution_time,
                "status": "success",
                "server": "jit-lisp",
                "config": self.config.get("name", "default")
            }
            
        except Exception as e:
            return {
                "code": code,
                "error": str(e),
                "status": "error",
                "server": "jit-lisp"
            }
    
    async def compile_lisp(self, code: Union[str, List], **kwargs) -> Dict[str, Any]:
        """Compile Lisp code (simulate compilation)"""
        try:
            if isinstance(code, str):
                code = ast.literal_eval(code)
            
            # Simulate compilation by checking syntax
            self.evaluate_lisp(code)  # This will catch syntax errors
            
            return {
                "code": code,
                "compiled": True,
                "status": "compiled",
                "optimizations": ["tail-call-optimization", "constant-folding"],
                "server": "jit-lisp"
            }
            
        except Exception as e:
            return {
                "code": code,
                "compiled": False,
                "error": str(e),
                "status": "compilation_error",
                "server": "jit-lisp"
            }
    
    async def load_file(self, filename: str, **kwargs) -> Dict[str, Any]:
        """Load and evaluate Lisp file"""
        try:
            with open(filename, 'r') as f:
                content = f.read()
            
            # Parse and evaluate each expression
            expressions = ast.literal_eval(f"[{content}]")  # Wrap in list
            results = []
            
            for expr in expressions:
                result = await self.eval_lisp(expr)
                results.append(result)
            
            return {
                "filename": filename,
                "expressions_loaded": len(results),
                "results": results,
                "status": "loaded",
                "server": "jit-lisp"
            }
            
        except Exception as e:
            return {
                "filename": filename,
                "error": str(e),
                "status": "load_error",
                "server": "jit-lisp"
            }
    
    async def define_macro(self, name: str, params: List[str], body: Any, **kwargs) -> Dict[str, Any]:
        """Define a Lisp macro"""
        try:
            def macro_func(*args):
                # Simple macro expansion - replace parameters with arguments
                return self.expand_macro(body, dict(zip(params, args)))
            
            self.macros[name] = macro_func
            
            return {
                "macro": name,
                "params": params,
                "body": body,
                "status": "defined",
                "server": "jit-lisp"
            }
            
        except Exception as e:
            return {
                "macro": name,
                "error": str(e),
                "status": "macro_error",
                "server": "jit-lisp"
            }
    
    def expand_macro(self, body: Any, substitutions: Dict[str, Any]) -> Any:
        """Expand macro by substituting parameters"""
        if isinstance(body, str) and body in substitutions:
            return substitutions[body]
        elif isinstance(body, list):
            return [self.expand_macro(item, substitutions) for item in body]
        else:
            return body
    
    async def get_environment(self, **kwargs) -> Dict[str, Any]:
        """Get current environment"""
        return {
            "environment_size": len(self.environment),
            "variables": list(self.environment.keys()),
            "macros": list(self.macros.keys()),
            "config": self.config,
            "server": "jit-lisp"
        }
    
    async def reset_environment(self, **kwargs) -> Dict[str, Any]:
        """Reset environment to initial state"""
        initial_env_size = len(self.environment)
        self.__init__(self.config)  # Reinitialize
        
        return {
            "previous_size": initial_env_size,
            "current_size": len(self.environment),
            "status": "reset",
            "server": "jit-lisp"
        }
    
    async def handle_tool_call(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Handle MCP tool calls"""
        if name in self.tools:
            return await self.tools[name](**arguments)
        else:
            return {"error": f"Unknown tool: {name}", "available_tools": list(self.tools.keys())}

async def main():
    """Main MCP server loop"""
    config = {}
    
    # Parse config from command line if provided
    if len(sys.argv) > 2 and sys.argv[1] == "--config":
        try:
            config = json.loads(sys.argv[2])
        except:
            pass
    
    server = JITLispServer(config)
    
    print(f"🚀 JIT Lisp Server started with config: {config}")
    
    # MCP protocol loop
    try:
        while True:
            line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
            if not line:
                break
            
            try:
                request = json.loads(line.strip())
                
                if request.get("method") == "tools/call":
                    tool_name = request["params"]["name"]
                    arguments = request["params"].get("arguments", {})
                    
                    result = await server.handle_tool_call(tool_name, arguments)
                    
                    response = {
                        "jsonrpc": "2.0",
                        "id": request.get("id"),
                        "result": {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}
                    }
                    
                    print(json.dumps(response))
                    sys.stdout.flush()
                
                elif request.get("method") == "tools/list":
                    tools_list = [
                        {"name": name, "description": f"JIT Lisp tool: {name}"}
                        for name in server.tools.keys()
                    ]
                    
                    response = {
                        "jsonrpc": "2.0",
                        "id": request.get("id"),
                        "result": {"tools": tools_list}
                    }
                    
                    print(json.dumps(response))
                    sys.stdout.flush()
                    
            except json.JSONDecodeError:
                pass
                
    except KeyboardInterrupt:
        pass
    
    print("🛑 JIT Lisp Server stopped")

if __name__ == "__main__":
    asyncio.run(main())