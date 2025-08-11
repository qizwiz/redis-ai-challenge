# MCP Library Comparison and Migration Guide

## Current Status
Both MCP libraries are installed and functional:
- **mcp**: 1.12.1 (traditional callback-based API)
- **fastmcp**: 2.10.6 (modern decorator-based API)

## API Differences

### Traditional MCP (mcp library)
```python
from mcp.server import Server
from mcp import stdio_server
from mcp.types import Tool, TextContent, CallToolResult, ListToolsResult

server = Server("my-server")

@server.list_tools()
async def handle_list_tools() -> ListToolsResult:
    return ListToolsResult(tools=[...])

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> CallToolResult:
    # Handle tools manually
    if name == "my_tool":
        # Implementation
        pass
```

### FastMCP (fastmcp library) 
```python
from fastmcp import FastMCP

mcp = FastMCP("my-server")

@mcp.tool()
def my_tool(arg1: str, arg2: int) -> str:
    """Tool description"""
    # Implementation
    return result
```

## Key Advantages of FastMCP

1. **Automatic Tool Registration**: Tools are registered automatically via decorators
2. **Type Safety**: Function signatures become the tool schema automatically  
3. **Simplified Code**: No manual tool list management or argument parsing
4. **Better Error Handling**: Built-in error handling and validation
5. **Modern Python**: Uses modern Python async/await patterns

## Migration Strategy

### Current Issues with Traditional MCP Servers
The current MCP servers are failing because:
1. Complex manual tool registration
2. Manual argument parsing and validation
3. Verbose callback-based structure
4. Error-prone tool list management

### Recommended Approach
Convert all MCP servers to use FastMCP for:
- Cleaner, more maintainable code
- Automatic tool registration and validation
- Better error handling
- Type safety

## Example Conversion

### Before (Traditional MCP)
```python
@server.list_tools()
async def handle_list_tools() -> ListToolsResult:
    return ListToolsResult(
        tools=[
            Tool(
                name="emacs_command",
                description="Execute natural language commands",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "command": {"type": "string", "description": "Natural language command"}
                    },
                    "required": ["command"]
                }
            )
        ]
    )

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> CallToolResult:
    if name == "emacs_command":
        command = arguments.get("command", "")
        # Process command...
        return CallToolResult(content=[TextContent(type="text", text=result)])
```

### After (FastMCP)
```python
@mcp.tool()
def emacs_command(command: str) -> str:
    """Execute natural language commands in Emacs via Redis coordination"""
    # Process command...
    return result
```

## Next Steps
1. Convert existing MCP servers to FastMCP format
2. Test the converted servers
3. Update .mcp.json configuration if needed
4. Verify all tools work correctly