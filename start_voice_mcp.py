#!/usr/bin/env python3
"""
Voice Conversation MCP Server Launcher
Starts the voice conversation MCP server with proper voice-mode integration.
"""

import subprocess
import sys
import os
import json
import time
from pathlib import Path

def check_voice_services():
    """Check if voice services are running"""
    print("🔍 Checking voice services...")
    
    try:
        # Check if voice-mode is available via MCP
        result = subprocess.run([
            sys.executable, "-c", 
            "from mcp__voice_mode__voice_status import voice_status; print('Voice services available')"
        ], capture_output=True, text=True, cwd=Path(__file__).parent)
        
        if result.returncode == 0:
            print("✅ Voice services are available")
            return True
        else:
            print(f"❌ Voice services check failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error checking voice services: {e}")
        return False

def start_mcp_server(port=8765):
    """Start the voice conversation MCP server"""
    print(f"🚀 Starting Voice Conversation MCP Server on port {port}...")
    
    server_script = Path(__file__).parent / "voice_conversation_mcp_server.py"
    
    if not server_script.exists():
        print(f"❌ Server script not found: {server_script}")
        return False
    
    try:
        # Start the MCP server
        cmd = [sys.executable, str(server_script), str(port)]
        print(f"Running: {' '.join(cmd)}")
        
        process = subprocess.Popen(
            cmd,
            cwd=Path(__file__).parent,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        # Print output in real-time
        for line in iter(process.stdout.readline, ''):
            print(line.strip())
            
        process.wait()
        return process.returncode == 0
        
    except KeyboardInterrupt:
        print("\n🛑 Voice conversation server stopped by user")
        if 'process' in locals():
            process.terminate()
        return True
    except Exception as e:
        print(f"❌ Error starting MCP server: {e}")
        return False

def create_mcp_config():
    """Create MCP configuration for the voice server"""
    config = {
        "mcpServers": {
            "voice-conversation": {
                "command": sys.executable,
                "args": [str(Path(__file__).parent / "voice_conversation_mcp_server.py")],
                "cwd": str(Path(__file__).parent)
            }
        }
    }
    
    config_path = Path(__file__).parent / ".mcp_voice.json"
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"✅ MCP config created: {config_path}")
    return config_path

def main():
    """Main launcher"""
    print("🎤 Voice Conversation MCP Server Launcher")
    print("=" * 50)
    
    # Check voice services first
    if not check_voice_services():
        print("\n⚠️  Voice services may not be fully available")
        print("You can still start the server, but voice features may not work")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            print("Exiting...")
            sys.exit(1)
    
    # Create MCP config
    config_path = create_mcp_config()
    
    # Parse port from command line
    port = 8765
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print("❌ Invalid port number")
            sys.exit(1)
    
    print(f"\n📝 MCP Config: {config_path}")
    print(f"🌐 Server Port: {port}")
    print(f"🎯 Server URL: http://localhost:{port}")
    print("\n🎤 Available MCP Tools:")
    print("  - start_voice_conversation: Begin voice chat")
    print("  - continue_voice_conversation: Speak and listen")
    print("  - speak_only: Text-to-speech only")
    print("  - listen_only: Speech-to-text only")
    print("  - end_voice_conversation: End session")
    print("  - get_conversation_context: Get session status")
    
    print(f"\n🚀 Starting server...")
    print("Press Ctrl+C to stop")
    
    # Start the server
    success = start_mcp_server(port)
    
    if success:
        print("✅ Server stopped cleanly")
    else:
        print("❌ Server encountered an error")
        sys.exit(1)

if __name__ == "__main__":
    main()