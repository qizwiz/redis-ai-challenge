import asyncio
import json
import subprocess

SERVER_COMMAND = [
    "python",
    "/Users/jonathanhill/src/redis-ai-challenge/mcp_redis_lisp_server.py",
]
PROXY_PORT = 6381


async def handle_client(reader, writer):
    addr = writer.get_extra_info("peername")
    print(f"Proxy: Client connected: {addr}")

    process = None
    try:
        # Start the MCP server subprocess
        process = await asyncio.create_subprocess_exec(
            *SERVER_COMMAND,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        print(f"Proxy: MCP server subprocess started with PID {process.pid}")

        # Forward data from client to subprocess stdin
        async def client_to_server():
            while True:
                data = await reader.readline()
                if not data:
                    break
                process.stdin.write(data)
                await process.stdin.drain()
                print(f"Proxy: Client -> Server: {data.decode().strip()}")

        # Forward data from subprocess stdout to client
        async def server_to_client():
            while True:
                data = await process.stdout.readline()
                if not data:
                    break
                writer.write(data)
                await writer.drain()
                print(f"Proxy: Server -> Client: {data.decode().strip()}")

        # Forward data from subprocess stderr to proxy's stderr (for debugging)
        async def server_stderr_to_proxy_stderr():
            while True:
                data = await process.stderr.readline()
                if not data:
                    break
                print(f"Proxy: Server STDERR: {data.decode().strip()}")

        await asyncio.gather(
            client_to_server(), server_to_client(), server_stderr_to_proxy_stderr()
        )

    except asyncio.CancelledError:
        print(f"Proxy: Client {addr} disconnected (cancelled).")
    except Exception as e:
        print(f"Proxy: Error with client {addr}: {e}")
    finally:
        if process and process.returncode is None:
            print(f"Proxy: Terminating MCP server subprocess {process.pid}")
            process.terminate()
            await process.wait()
        writer.close()
        await writer.wait_closed()
        print(f"Proxy: Client {addr} disconnected.")


async def main():
    server = await asyncio.start_server(handle_client, "localhost", PROXY_PORT)
    print(f"Proxy: TCP proxy listening on tcp://localhost:{PROXY_PORT}")

    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
