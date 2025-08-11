import asyncio
import json


async def main():
    # Send initialize request
    init_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "1.0",
            "capabilities": {},
            "clientInfo": {"name": "Gemini CLI Client", "version": "1.0"},
        },
    }
    print(json.dumps(init_request), flush=True)

    # Wait for initialize response (optional, but good practice)
    # response = json.loads(await asyncio.to_thread(input))
    # print(f"Received: {response}")

    # Send tool call request
    tool_call_request = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {
            "name": "execute_lisp",
            "arguments": {
                "code": '["emacs-eval", "(message \\"Hello from Gemini!\\")"]'
            },
        },
    }
    print(json.dumps(tool_call_request), flush=True)

    # Wait for tool call response
    # response = json.loads(await asyncio.to_thread(input))
    # print(f"Received: {response}")


if __name__ == "__main__":
    asyncio.run(main())
