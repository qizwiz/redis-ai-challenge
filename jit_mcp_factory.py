#!/usr/bin/env python3
"""
Just-In-Time MCP Server Factory
Creates specialized MCP servers on demand for any function call
"""

import os
import subprocess
import tempfile
from typing import Dict, List, Any

class JITMCPFactory:
    """
    Creates MCP servers on-demand for any function signature
    """
    
    def __init__(self):
        self.created_servers = {}
        self.server_template = '''#!/usr/bin/env python3
from fastmcp import FastMCP

mcp = FastMCP("{server_name}")

{tool_definitions}

if __name__ == "__main__":
    mcp.run()
'''
    
    def create_server_for_function(self, func_name: str, args_spec: List[str], description: str = "") -> str:
        """
        Create a specialized MCP server for a specific function
        """
        server_name = f"jit-{func_name.replace('_', '-')}"
        server_file = f"/Users/jonathanhill/src/redis-ai-challenge/jit_{func_name}_server.py"
        
        # Generate tool definition
        tool_def = self._generate_tool_definition(func_name, args_spec, description)
        
        # Create server file
        server_code = self.server_template.format(
            server_name=server_name,
            tool_definitions=tool_def
        )
        
        with open(server_file, 'w') as f:
            f.write(server_code)
        
        os.chmod(server_file, 0o755)
        
        # Register with Claude Code
        register_cmd = f"claude mcp add {server_name} python3 {server_file}"
        try:
            result = subprocess.run(register_cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ Created JIT MCP server: {server_name}")
                self.created_servers[func_name] = {
                    'server_name': server_name,
                    'file_path': server_file,
                    'registration_result': result.stdout
                }
                return server_name
            else:
                print(f"❌ Failed to register {server_name}: {result.stderr}")
                return None
        except Exception as e:
            print(f"❌ Error creating JIT server: {e}")
            return None
    
    def _generate_tool_definition(self, func_name: str, args_spec: List[str], description: str) -> str:
        """Generate FastMCP tool definition code"""
        
        # Fix invalid Python function names (replace hyphens with underscores)
        python_func_name = func_name.replace('-', '_')
        
        # Generate parameter list
        params = []
        for i, arg_type in enumerate(args_spec):
            params.append(f"arg{i}: {arg_type}")
        param_str = ", ".join(params)
        
        # Generate function body based on function name
        if 'redis' in func_name:
            body = self._redis_function_body(func_name)
        elif 'emacs' in func_name:
            body = self._emacs_function_body(func_name)
        elif 'voice' in func_name:
            body = self._voice_function_body(func_name)
        elif 'ai' in func_name or 'llm' in func_name:
            body = self._ai_function_body(func_name)
        else:
            body = f'    return f"Executed {func_name} with args: {{locals()}}"'
        
        tool_code = f'''
@mcp.tool()
def {python_func_name}({param_str}) -> str:
    """{description or f"JIT-generated tool for {func_name}"}"""
{body}
'''
        return tool_code
    
    def _redis_function_body(self, func_name: str) -> str:
        return '''    import redis
    r = redis.Redis(decode_responses=True)
    # Redis operation logic here
    return f"Redis operation {func_name} completed"'''
    
    def _emacs_function_body(self, func_name: str) -> str:
        return '''    import subprocess
    # Emacs operation logic here
    result = subprocess.run(['emacsclient', '-e', f'({func_name})'], capture_output=True, text=True)
    return f"Emacs operation {func_name}: {result.stdout}"'''
    
    def _voice_function_body(self, func_name: str) -> str:
        return '''    # Voice operation logic here
    print(f"Voice operation: {func_name}")
    return f"Voice operation {func_name} completed"'''
    
    def _ai_function_body(self, func_name: str) -> str:
        return '''    # AI/LLM operation logic here
    return f"AI operation {func_name} completed"'''
    
    def create_servers_from_lisp_expression(self, expr: List) -> Dict[str, str]:
        """
        Analyze Lisp expression and create JIT servers for unknown functions
        """
        created = {}
        
        def analyze_expr(e):
            if not isinstance(e, list) or len(e) == 0:
                return
            
            func_name = e[0]
            args = e[1:]
            
            # Skip built-in functions
            if func_name in ['parallel', 'sequence', 'if', 'lambda', 'define']:
                for arg in args:
                    if isinstance(arg, list):
                        analyze_expr(arg)
                return
            
            # Check if we need to create a server for this function
            if func_name not in self.created_servers:
                # Infer argument types from usage
                arg_types = []
                for arg in args:
                    if isinstance(arg, str):
                        arg_types.append('str')
                    elif isinstance(arg, (int, float)):
                        arg_types.append('float')
                    elif isinstance(arg, list):
                        arg_types.append('List')
                        analyze_expr(arg)  # Recursive analysis
                    else:
                        arg_types.append('Any')
                
                server_name = self.create_server_for_function(
                    func_name, 
                    arg_types,
                    f"JIT-created server for {func_name} operation"
                )
                
                if server_name:
                    created[func_name] = server_name
            
            # Continue analyzing nested expressions
            for arg in args:
                if isinstance(arg, list):
                    analyze_expr(arg)
        
        analyze_expr(expr)
        return created
    
    def list_created_servers(self) -> Dict:
        """List all JIT-created servers"""
        return self.created_servers
    
    def cleanup_server(self, func_name: str) -> bool:
        """Remove a JIT-created server"""
        if func_name in self.created_servers:
            server_info = self.created_servers[func_name]
            try:
                # Remove from Claude Code
                subprocess.run(f"claude mcp remove {server_info['server_name']}", shell=True)
                # Remove file
                os.remove(server_info['file_path'])
                del self.created_servers[func_name]
                print(f"🗑️ Removed JIT server: {server_info['server_name']}")
                return True
            except Exception as e:
                print(f"❌ Error removing server: {e}")
                return False
        return False

# Test the JIT factory
if __name__ == "__main__":
    factory = JITMCPFactory()
    
    print("🏭 JIT MCP Factory Test")
    print("=" * 50)
    
    # Test expression with unknown functions
    test_expr = [
        'parallel',
        ['database-query', 'SELECT * FROM users', 'main_db'],
        ['api-call', 'https://api.example.com/data', 'GET'],
        ['file-processor', '/path/to/file.txt', 'process'],
        ['ml-inference', 'sentiment', 'This is a test sentence']
    ]
    
    print(f"📄 Test expression: {test_expr}")
    print("\n🔧 Creating JIT servers...")
    
    created = factory.create_servers_from_lisp_expression(test_expr)
    
    print(f"\n✅ Created {len(created)} JIT servers:")
    for func, server in created.items():
        print(f"  {func} → {server}")
    
    print(f"\n📊 Total JIT servers: {len(factory.list_created_servers())}")
    
    # Show all available servers now
    print("\n🌐 Checking updated server list...")
    result = subprocess.run("claude mcp list", shell=True, capture_output=True, text=True)
    print(result.stdout)