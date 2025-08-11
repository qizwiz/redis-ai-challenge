#!/usr/bin/env python3
"""
Demo Voice Conversation with Claude Code
Shows how to use the voice bridge MCP server for turn-by-turn voice conversation.
"""

import time
import sys
from pathlib import Path

def demo_voice_conversation():
    """Demonstrate voice conversation flow"""
    print("🎤 Voice Conversation with Claude Code Demo")
    print("=" * 50)
    print()
    
    print("This demo shows how to use the Voice-Claude Bridge MCP server")
    print("for seamless voice conversation with Claude Code in your vterm.")
    print()
    
    print("🔧 Setup Steps:")
    print("1. The voice bridge MCP server is ready: voice_claude_bridge.py")
    print("2. Voice services are running (Whisper STT + Kokoro TTS)")
    print("3. MCP config created: mcp_voice_config.json")
    print()
    
    print("💬 Conversation Flow:")
    print()
    
    print("Step 1: Start Voice Session")
    print("=" * 30)
    print("Tool Call: start_voice_session")
    print("Parameters: {")
    print('  "greeting": "Hello! I\'m Claude and ready for voice conversation. What shall we discuss?",')
    print('  "voice": "af_sky",')
    print('  "tts_provider": "kokoro"')
    print("}")
    print("→ Returns session_started status")
    print()
    
    print("Step 2: Conversation Loop")
    print("=" * 30)
    print("A. Call: converse_step")
    print("   Parameters: {")
    print('     "claude_response": "That\'s fascinating! Tell me more about that.",')
    print('     "voice": "af_sky",')
    print('     "listen_duration": 45.0')
    print("   }")
    print("   → Returns voice_tool_call instructions")
    print()
    
    print("B. Execute: mcp__voice-mode__converse")
    print("   Parameters: {")
    print('     "message": "That\'s fascinating! Tell me more about that.",')
    print('     "voice": "af_sky",')
    print('     "tts_provider": "kokoro",')
    print('     "listen_duration": 45.0,')
    print('     "wait_for_response": true')
    print("   }")
    print("   → Speaks message and returns user's response")
    print()
    
    print("C. Call: handle_user_response")
    print("   Parameters: {")
    print('     "user_transcription": "Well, I was thinking about AI development..."')
    print("   }")
    print("   → Processes user input and updates context")
    print()
    
    print("D. Repeat A-C for continued conversation")
    print()
    
    print("Step 3: End Session")
    print("=" * 30) 
    print("Tool Call: end_voice_session")
    print("→ Returns session summary and cleanup")
    print()
    
    print("🎯 Key Features:")
    print("• Seamless voice input/output in vterm")
    print("• Automatic transcription with Whisper") 
    print("• Natural speech with Kokoro TTS")
    print("• Conversation context tracking")
    print("• Flexible voice and provider selection")
    print("• Error handling and recovery")
    print()
    
    print("🚀 Quick Start Commands:")
    print()
    print("# Start the MCP server (in another terminal)")
    print("python voice_claude_bridge.py")
    print()
    print("# In Claude Code, use these tools:")
    print("start_voice_session(greeting='Hello! Let\\'s chat.')")
    print("# → Then follow the voice_tool_call instructions")
    print("# → Use handle_user_response with the transcription result")
    print()
    
    print("✨ This enables natural voice conversation with Claude Code")
    print("   directly in your vterm environment!")

def show_mcp_config():
    """Show the MCP configuration"""
    config_file = Path(__file__).parent / "mcp_voice_config.json"
    if config_file.exists():
        print("\n📄 MCP Configuration (mcp_voice_config.json):")
        print("-" * 50)
        with open(config_file) as f:
            print(f.read())
    else:
        print("\n❌ MCP config file not found")

def main():
    """Main demo"""
    demo_voice_conversation()
    show_mcp_config()
    
    print("\n🎤 Ready to start voice conversation!")
    print("Launch the MCP server and begin chatting with Claude Code.")

if __name__ == "__main__":
    main()