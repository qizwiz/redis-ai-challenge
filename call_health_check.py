import asyncio
from fastmcp.client import Client
from fastmcp.client.transports import PythonStdioTransport
import os


async def call_emacs_health_check():
    server_script_path = os.path.join(os.getcwd(), "emacs_persistent_vision_mcp.py")
    transport = PythonStdioTransport(script_path=server_script_path)

    try:
        async with Client(transport=transport) as client:
            print("Attempting to call 'emacs_health_check'...")
            result = await client.call_tool("emacs_health_check", {})
            print("Result of 'emacs_health_check':")
            for content in result.content:
                if content.type == "text":
                    print(content.text)
                else:
                    print(f"Received content of type: {content.type}")
    except Exception as e:
        print(f"Error calling 'emacs_health_check': {e}")


if __name__ == "__main__":
    asyncio.run(call_emacs_health_check())
