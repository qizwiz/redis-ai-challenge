#!/usr/bin/env python3
"""
MCP Man-in-the-Middle Proxy
Intercepts and logs JSON-RPC communication between a client and an MCP server.
"""

import sys
import subprocess
import threading
import json

def print_log(prefix, text):
    """Prints a log message to stderr, pretty-printing JSON if possible."""
    try:
        # Try to parse and pretty-print JSON
        parsed = json.loads(text)
        pretty_text = json.dumps(parsed, indent=2)
        log_message = f"{prefix}\n{pretty_text}\n"
    except json.JSONDecodeError:
        # If not JSON, print as is
        log_message = f"{prefix} {text.strip()}\n"
    
    sys.stderr.write(log_message)
    sys.stderr.flush()

def client_to_server(client_in, server_out):
    """Thread function to read from client and write to server."""
    for line in iter(client_in.readline, ''):
        print_log("[CLIENT->SERVER]", line)
        server_out.write(line)
        server_out.flush()
    server_out.close()

def server_to_client(server_in, client_out, prefix):
    """Thread function to read from server and write to client."""
    for line in iter(server_in.readline, ''):
        print_log(prefix, line)
        client_out.write(line)
        client_out.flush()
    client_out.close()

def main():
    if len(sys.argv) < 2:
        print("Usage: python mcp_mitm_proxy.py <path_to_real_server>", file=sys.stderr)
        sys.exit(1)

    target_server_path = sys.argv[1]

    sys.stderr.write(f"--- Starting MITM Proxy for: {target_server_path} ---\n")

    server_process = subprocess.Popen(
        ["python3", target_server_path],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    # Create threads to handle the two-way communication
    c2s_thread = threading.Thread(
        target=client_to_server,
        args=(sys.stdin, server_process.stdin)
    )
    s2c_thread = threading.Thread(
        target=server_to_client,
        args=(server_process.stdout, sys.stdout, "[SERVER->CLIENT]")
    )
    s2e_thread = threading.Thread(
        target=server_to_client,
        args=(server_process.stderr, sys.stderr, "[SERVER->STDERR]")
    )

    c2s_thread.start()
    s2c_thread.start()
    s2e_thread.start()
    
    c2s_thread.join()
    server_process.wait()
    s2c_thread.join()
    s2e_thread.join()

    sys.stderr.write("--- MITM Proxy Shutting Down ---\n")

if __name__ == "__main__":
    main()
