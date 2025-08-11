#!/usr/bin/env python3
"""
Voice-Claude Bridge Launcher and Test
Start the voice bridge MCP server and demonstrate usage.
"""

import subprocess
import sys
import os
import time
import json
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are available"""
    print("🔍 Checking dependencies...")
    
    missing = []
    
    # Check fastmcp
    try:
        import fastmcp
        print("✅ fastmcp available")
    except ImportError:
        print("❌ fastmcp missing")
        missing.append("fastmcp")
    
    # Check voice-mode tools
    try:
        # We can't easily test the MCP tools directly, but we can check if the voice status works
        result = subprocess.run([
            sys.executable, "-c", 
            "import sys; sys.path.append('.'); from mcp__voice_mode__voice_status import *; print('Voice mode available')"
        ], capture_output=True, text=True, cwd=Path(__file__).parent, timeout=5)
        
        if result.returncode == 0:
            print("✅ Voice mode tools available")
        else:
            print("⚠️  Voice mode tools may not be fully available")
    except Exception as e:
        print(f"⚠️  Could not verify voice mode: {e}")
    
    if missing:
        print(f"\n📦 Installing missing dependencies: {missing}")
        for dep in missing:
            subprocess.run([sys.executable, "-m", "pip", "install", dep], check=True)
        print("✅ Dependencies installed")
    
    return True

def start_bridge_server(port=8766, background=False):
    """Start the voice bridge server"""
    bridge_script = Path(__file__).parent / "voice_claude_bridge.py"
    
    if not bridge_script.exists():
        print(f"❌ Bridge script not found: {bridge_script}")
        return None
    
    cmd = [sys.executable, str(bridge_script), str(port)]
    
    if background:
        # Start in background
        print(f"🚀 Starting Voice-Claude Bridge in background on port {port}...")
        process = subprocess.Popen(
            cmd,
            cwd=Path(__file__).parent,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        time.sleep(2)  # Give it time to start
        
        # Check if it's still running
        if process.poll() is None:
            print(f"✅ Bridge server started (PID: {process.pid})")
            return process
        else:
            print("❌ Bridge server failed to start")
            return None
    else:
        # Start in foreground
        print(f"🚀 Starting Voice-Claude Bridge on port {port}...")
        print("Press Ctrl+C to stop")
        
        try:
            subprocess.run(cmd, cwd=Path(__file__).parent)
            return True
        except KeyboardInterrupt:
            print("\n🛑 Bridge server stopped")
            return True
        except Exception as e:
            print(f"❌ Error starting bridge: {e}")
            return False

def create_usage_demo():
    """Create a demo showing how to use the voice bridge"""
    demo_content = '''
# Voice-Claude Bridge Usage Demo

## 1. Start Voice Session
```
Tool: start_voice_session
Parameters: {
    "greeting": "Hello! I'm Claude and I'm ready for a voice conversation. What would you like to discuss?",
    "voice": "af_sky",
    "tts_provider": "kokoro"
}
```

## 2. Conversation Loop

### Step A: Claude speaks and listens
```
Tool: converse_step  
Parameters: {
    "claude_response": "That's interesting! Can you tell me more about that?",
    "voice": "af_sky",
    "tts_provider": "kokoro", 
    "listen_duration": 45.0
}
```

This returns instructions to call:
```
Tool: mcp__voice-mode__converse
Parameters: {
    "message": "That's interesting! Can you tell me more about that?",
    "voice": "af_sky",
    "tts_provider": "kokoro",
    "listen_duration": 45.0,
    "wait_for_response": true
}
```

### Step B: Process user response
```
Tool: handle_user_response
Parameters: {
    "user_transcription": "Well, I was thinking about machine learning..."
}
```

### Step C: Repeat with Claude's next response
Continue the loop with `converse_step` → voice call → `handle_user_response`

## 3. End Session
```
Tool: end_voice_session
Parameters: {}
```

## Quick Commands

### Speak Only (no listening)
```
Tool: speak_only
Parameters: {
    "text": "Thank you for the conversation!",
    "voice": "af_sky"
}
```

### Listen Only (no speaking)
```
Tool: listen_only
Parameters: {
    "listen_duration": 30.0
}
```

### Check Status
```
Tool: get_conversation_status
Parameters: {}
```
'''
    
    demo_file = Path(__file__).parent / "VOICE_BRIDGE_DEMO.md"
    with open(demo_file, 'w') as f:
        f.write(demo_content.strip())
    
    return demo_file

def main():
    """Main launcher"""
    print("🎤 Voice-Claude Bridge Launcher")
    print("=" * 40)
    
    # Check dependencies
    if not check_dependencies():
        print("❌ Dependency check failed")
        sys.exit(1)
    
    # Create usage demo
    demo_file = create_usage_demo()
    print(f"📖 Usage demo created: {demo_file}")
    
    # Parse arguments
    port = 8766
    background = False
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--background" or sys.argv[1] == "-b":
            background = True
            if len(sys.argv) > 2:
                port = int(sys.argv[2])
        else:
            port = int(sys.argv[1])
    
    print(f"\n🌐 Server will run on: http://localhost:{port}")
    print(f"📝 Mode: {'Background' if background else 'Foreground'}")
    
    print("\n🎯 Available MCP Tools:")
    print("  • start_voice_session - Begin conversation")
    print("  • converse_step - Speak & listen cycle")  
    print("  • handle_user_response - Process user input")
    print("  • speak_only - TTS without listening")
    print("  • listen_only - STT without speaking")
    print("  • end_voice_session - End conversation")
    print("  • get_conversation_status - Session info")
    
    print("\n💡 Usage Pattern:")
    print("  1. Call start_voice_session(greeting)")
    print("  2. Call converse_step(claude_response)")
    print("  3. Execute the returned voice_tool_call")
    print("  4. Call handle_user_response(result)")  
    print("  5. Repeat 2-4 for conversation flow")
    
    if background:
        print(f"\n🚀 Starting in background...")
        process = start_bridge_server(port, background=True)
        if process:
            print(f"✅ Bridge server running (PID: {process.pid})")
            print(f"📡 Connect via MCP to: http://localhost:{port}")
            print(f"🛑 To stop: kill {process.pid}")
        else:
            print("❌ Failed to start server")
            sys.exit(1)
    else:
        print(f"\n🚀 Starting in foreground...")
        success = start_bridge_server(port, background=False)
        if not success:
            sys.exit(1)

if __name__ == "__main__":
    main()