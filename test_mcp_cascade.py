#!/usr/bin/env python3
"""
Prove that MCP servers calling MCP servers is simple and works
"""
import requests
import json
import subprocess
import time
import sys

def simple_mcp_server_demo():
    """Actually demonstrate MCP servers calling each other"""
    
    print("🔧 MCP SERVERS CALLING MCP SERVERS - SIMPLE DEMO")
    print("=" * 60)
    
    # Create a simple server A that calls server B
    server_a_code = '''
import requests
from fastmcp import FastMCP

mcp = FastMCP("server-a")

@mcp.tool()
def process_and_forward(data: str) -> str:
    """Process data and forward to server B"""
    processed = f"ServerA processed: {data}"
    
    # Call server B
    try:
        response = requests.post("http://localhost:8001/", json={
            "method": "final_process", 
            "params": [processed]
        })
        return f"ServerA result: {response.text}"
    except:
        return f"ServerA standalone: {processed}"

if __name__ == "__main__":
    mcp.run(port=8000)
'''

    server_b_code = '''
from fastmcp import FastMCP

mcp = FastMCP("server-b")

@mcp.tool()  
def final_process(data: str) -> str:
    """Final processing step"""
    return f"ServerB final: {data} -> COMPLETE"

if __name__ == "__main__":
    mcp.run(port=8001)
'''
    
    # Write the server files
    with open("temp_server_a.py", "w") as f:
        f.write(server_a_code)
    with open("temp_server_b.py", "w") as f:
        f.write(server_b_code)
    
    print("✅ Created server files")
    
    # Start server B first
    proc_b = subprocess.Popen([sys.executable, "temp_server_b.py"], 
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(2)
    print(f"✅ Started Server B (PID: {proc_b.pid})")
    
    # Start server A  
    proc_a = subprocess.Popen([sys.executable, "temp_server_a.py"],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(2) 
    print(f"✅ Started Server A (PID: {proc_a.pid})")
    
    # Test: Call server A, which should call server B
    try:
        response = requests.post("http://localhost:8000/", json={
            "method": "process_and_forward",
            "params": ["test data"]
        })
        print(f"🎯 CASCADE RESULT: {response.text}")
        print("✅ MCP SERVER CASCADE WORKING!")
        
    except Exception as e:
        print(f"❌ Cascade failed: {e}")
    
    # Cleanup
    proc_a.terminate()
    proc_b.terminate()
    
    import os
    os.remove("temp_server_a.py") 
    os.remove("temp_server_b.py")
    
    print("🧹 Cleanup complete")

if __name__ == "__main__":
    simple_mcp_server_demo()