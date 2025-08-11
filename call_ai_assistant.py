import asyncio
from fastmcp.client import Client
from fastmcp.client.transports import PythonStdioTransport
import os


async def call_ai_assistant_tool():
    server_script_path = os.path.join(os.getcwd(), "mcp_ai_assistant.py")
    transport = PythonStdioTransport(script_path=server_script_path)

    try:
        async with Client(transport=transport) as client:
            print("Attempting to call 'get_ai_knowledge' on mcp_ai_assistant...")
            result = await client.call_tool("get_ai_knowledge", {})
            print("Result of 'get_ai_knowledge':")
            for content in result.content:
                if content.type == "text":
                    print(content.text)
                else:
                    print(f"Received content of type: {content.type}")
    except Exception as e:
        print(f"Error calling 'get_ai_knowledge': {e}")


if __name__ == "__main__":
    asyncio.run(call_ai_assistant_tool())
