import asyncio
from fastmcp.client import Client
from fastmcp.client.transports import PythonStdioTransport
import os


async def main():
    server_script_path = os.path.join(os.getcwd(), "claude_conversation_mcp.py")
    transport = PythonStdioTransport(script_path=server_script_path)

    async with Client(transport=transport) as client:
        print(f"Connected to MCP server.")

        # Attempt to call a known tool: participate_in_conversation
        try:
            print("Attempting to call 'participate_in_conversation'...")
            result = await client.call_tool("participate_in_conversation", {})
            print("Result of 'participate_in_conversation':")
            for content in result.content:
                if content.type == "text":
                    print(content.text)
                else:
                    print(f"Received content of type: {content.type}")
        except Exception as e:
            print(f"Error calling 'participate_in_conversation': {e}")


if __name__ == "__main__":
    asyncio.run(main())
