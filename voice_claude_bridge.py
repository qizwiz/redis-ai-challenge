#!/usr/bin/env python3
"""
Voice-Claude Bridge MCP Server
Direct voice conversation bridge using existing voice-mode infrastructure.

This server enables turn-by-turn voice conversation by:
1. Listening for voice input via voice-mode
2. Passing transcriptions to Claude Code 
3. Speaking Claude's responses back
4. Maintaining conversation context
"""

import asyncio
import logging
import json
import time
from typing import Dict, Any, List, Optional
from pathlib import Path

# FastMCP for the server framework
try:
    import fastmcp
except ImportError:
    print("❌ fastmcp not available. Installing...")
    import subprocess
    import sys
    subprocess.run([sys.executable, "-m", "pip", "install", "fastmcp"], check=True)
    import fastmcp

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VoiceClaudeBridge:
    """FastMCP server bridging voice input/output with Claude Code"""
    
    def __init__(self):
        self.app = fastmcp.FastMCP("Voice Claude Bridge")
        self.conversation_active = False
        self.conversation_history: List[Dict[str, Any]] = []
        self.session_start_time = None
        self.setup_tools()
    
    def setup_tools(self):
        """Register the voice conversation tools"""
        
        @self.app.tool()
        def start_voice_session(
            greeting: str = "Hello! I'm Claude and I'm ready to have a voice conversation with you. What would you like to talk about?",
            voice: str = "af_sky",
            tts_provider: str = "kokoro"
        ) -> Dict[str, Any]:
            """
            Start a voice conversation session.
            
            Args:
                greeting: Initial message to speak to the user
                voice: TTS voice to use (af_sky, af_sarah, etc.)
                tts_provider: TTS provider (kokoro or openai)
            
            Returns:
                Session start confirmation and user's first response
            """
            self.conversation_active = True
            self.conversation_history = []
            self.session_start_time = time.time()
            
            logger.info("🎤 Starting voice conversation session...")
            
            # Add the greeting to history
            self.conversation_history.append({
                "role": "assistant",
                "content": greeting,
                "timestamp": time.time()
            })
            
            return {
                "status": "session_started",
                "greeting_sent": greeting,
                "voice": voice,
                "provider": tts_provider,
                "session_id": int(self.session_start_time),
                "instructions": "Use 'converse_step' to speak this greeting and get the user's response"
            }
        
        @self.app.tool()
        def converse_step(
            claude_response: str,
            voice: str = "af_sky", 
            tts_provider: str = "kokoro",
            listen_duration: float = 60.0,
            min_listen_duration: float = 2.5,
            speed: float = 1.0
        ) -> Dict[str, Any]:
            """
            Execute one step of voice conversation: speak Claude's response and listen for user reply.
            
            Args:
                claude_response: Claude's response to speak to the user
                voice: TTS voice to use
                tts_provider: TTS provider (kokoro recommended for quality)
                listen_duration: How long to listen for user response (seconds)
                min_listen_duration: Minimum listen time before silence detection
                speed: Speech rate (0.25 to 4.0, 1.0 = normal)
            
            Returns:
                User's voice response transcription
            """
            if not self.conversation_active:
                return {
                    "status": "error",
                    "message": "No active session. Use start_voice_session first."
                }
            
            logger.info(f"🗣️  Speaking: {claude_response[:100]}...")
            logger.info(f"🎤 Then listening for {listen_duration}s...")
            
            # Add Claude's response to history
            self.conversation_history.append({
                "role": "assistant", 
                "content": claude_response,
                "timestamp": time.time()
            })
            
            # This returns the MCP tool call that Claude Code should make
            # We can't directly call the voice-mode tools from here, so we return instructions
            return {
                "status": "ready_for_voice_call",
                "voice_tool_call": {
                    "tool": "mcp__voice-mode__converse",
                    "parameters": {
                        "message": claude_response,
                        "voice": voice,
                        "tts_provider": tts_provider,
                        "listen_duration": listen_duration,
                        "min_listen_duration": min_listen_duration,
                        "speed": speed,
                        "wait_for_response": True
                    }
                },
                "instructions": "Call the mcp__voice-mode__converse tool with the provided parameters, then use handle_user_response with the result"
            }
        
        @self.app.tool()
        def handle_user_response(
            user_transcription: str,
            confidence: Optional[float] = None
        ) -> Dict[str, Any]:
            """
            Process the user's voice response and prepare for Claude's next response.
            
            Args:
                user_transcription: What the user said (from voice-mode converse)
                confidence: Optional transcription confidence score
                
            Returns:
                Processed user input and conversation context
            """
            if not self.conversation_active:
                return {
                    "status": "error", 
                    "message": "No active session"
                }
            
            # Handle empty or error responses
            if not user_transcription or user_transcription.strip() == "":
                return {
                    "status": "no_input",
                    "message": "No user input detected",
                    "suggestions": ["Try speaking again", "Check microphone", "End session if done"]
                }
            
            # Add user response to history
            self.conversation_history.append({
                "role": "user",
                "content": user_transcription,
                "timestamp": time.time(),
                "confidence": confidence
            })
            
            logger.info(f"👤 User said: {user_transcription}")
            
            # Check for conversation end signals
            end_phrases = ["goodbye", "bye", "end conversation", "stop", "that's all", "thank you goodbye"]
            if any(phrase in user_transcription.lower() for phrase in end_phrases):
                return self.end_voice_session()
            
            return {
                "status": "user_response_received",
                "user_said": user_transcription,
                "conversation_length": len(self.conversation_history),
                "session_duration_minutes": (time.time() - self.session_start_time) / 60,
                "ready_for_claude_response": True,
                "context": self._get_recent_context()
            }
        
        @self.app.tool()
        def speak_only(
            text: str,
            voice: str = "af_sky",
            tts_provider: str = "kokoro", 
            speed: float = 1.0
        ) -> Dict[str, Any]:
            """
            Speak text without listening for a response.
            
            Args:
                text: Text to speak
                voice: TTS voice to use
                tts_provider: TTS provider
                speed: Speech rate
            
            Returns:
                Instructions for voice tool call
            """
            if not self.conversation_active:
                return {
                    "status": "error",
                    "message": "No active session"
                }
            
            self.conversation_history.append({
                "role": "assistant",
                "content": text, 
                "timestamp": time.time(),
                "speak_only": True
            })
            
            return {
                "status": "ready_for_voice_call",
                "voice_tool_call": {
                    "tool": "mcp__voice-mode__converse", 
                    "parameters": {
                        "message": text,
                        "voice": voice,
                        "tts_provider": tts_provider,
                        "speed": speed,
                        "wait_for_response": False
                    }
                },
                "instructions": "Call the mcp__voice-mode__converse tool with wait_for_response=False"
            }
        
        @self.app.tool()
        def listen_only(
            listen_duration: float = 30.0,
            min_listen_duration: float = 2.5,
            prompt: str = "Listening..."
        ) -> Dict[str, Any]:
            """
            Listen for user input without speaking first.
            
            Args:
                listen_duration: How long to listen
                min_listen_duration: Minimum listen time
                prompt: Display prompt (not spoken)
                
            Returns:
                Instructions for voice tool call
            """
            if not self.conversation_active:
                return {
                    "status": "error",
                    "message": "No active session"
                }
            
            return {
                "status": "ready_for_voice_call",
                "voice_tool_call": {
                    "tool": "mcp__voice-mode__converse",
                    "parameters": {
                        "message": "",  # Empty message for listen-only
                        "listen_duration": listen_duration,
                        "min_listen_duration": min_listen_duration,
                        "wait_for_response": True
                    }
                },
                "instructions": f"{prompt} Call mcp__voice-mode__converse with empty message to listen only, then use handle_user_response"
            }
        
        @self.app.tool()
        def end_voice_session() -> Dict[str, Any]:
            """
            End the current voice conversation session.
            
            Returns:
                Session summary and cleanup status
            """
            if not self.conversation_active:
                return {
                    "status": "no_active_session",
                    "message": "No active session to end"
                }
            
            # Calculate session stats
            session_duration = (time.time() - self.session_start_time) / 60
            user_messages = [msg for msg in self.conversation_history if msg["role"] == "user"]
            assistant_messages = [msg for msg in self.conversation_history if msg["role"] == "assistant"]
            
            session_summary = {
                "duration_minutes": round(session_duration, 2),
                "total_exchanges": len(user_messages),
                "total_messages": len(self.conversation_history),
                "user_messages": len(user_messages),
                "assistant_messages": len(assistant_messages),
                "session_start": self.session_start_time,
                "session_end": time.time()
            }
            
            # Clean up
            self.conversation_active = False
            self.conversation_history = []
            self.session_start_time = None
            
            logger.info(f"🏁 Voice session ended: {session_summary}")
            
            return {
                "status": "session_ended",
                "message": "Voice conversation session ended successfully",
                "summary": session_summary
            }
        
        @self.app.tool()
        def get_conversation_status() -> Dict[str, Any]:
            """
            Get current conversation status and context.
            
            Returns:
                Current session state and recent conversation history
            """
            if not self.conversation_active:
                return {
                    "status": "no_active_session",
                    "active": False,
                    "message": "No voice conversation session is currently active"
                }
            
            return {
                "status": "active_session",
                "active": True,
                "session_duration_minutes": (time.time() - self.session_start_time) / 60,
                "message_count": len(self.conversation_history),
                "last_message_time": self.conversation_history[-1]["timestamp"] if self.conversation_history else None,
                "recent_context": self._get_recent_context(limit=3),
                "session_start": self.session_start_time
            }
        
        @self.app.tool()
        def get_full_conversation() -> Dict[str, Any]:
            """
            Get the complete conversation history.
            
            Returns:
                Full conversation history and metadata
            """
            return {
                "status": "success",
                "active": self.conversation_active,
                "full_history": self.conversation_history,
                "session_start": self.session_start_time,
                "total_messages": len(self.conversation_history)
            }
    
    def _get_recent_context(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recent conversation context"""
        return self.conversation_history[-limit:] if len(self.conversation_history) > limit else self.conversation_history
    
    def run(self):
        """Run the FastMCP server"""
        logger.info("🎤 Starting Voice-Claude Bridge MCP Server")
        logger.info("")
        logger.info("🔧 Available Tools:")
        logger.info("  1. start_voice_session - Begin voice conversation")
        logger.info("  2. converse_step - Speak response & listen for reply")  
        logger.info("  3. handle_user_response - Process user's voice input")
        logger.info("  4. speak_only - Speak without listening")
        logger.info("  5. listen_only - Listen without speaking")
        logger.info("  6. end_voice_session - End conversation")
        logger.info("  7. get_conversation_status - Get session info")
        logger.info("  8. get_full_conversation - Get complete history")
        logger.info("")
        logger.info("📝 Usage Pattern:")
        logger.info("  1. start_voice_session(greeting)")
        logger.info("  2. converse_step(claude_response) -> get voice_tool_call")
        logger.info("  3. Call mcp__voice-mode__converse with returned parameters")
        logger.info("  4. handle_user_response(transcription_result)")
        logger.info("  5. Repeat steps 2-4 for conversation")
        logger.info("  6. end_voice_session() when done")
        logger.info("")
        
        # FastMCP runs via stdio, not HTTP server
        self.app.run()

def main():
    """Main entry point"""
    import sys
    
    # Create and run the bridge server
    bridge = VoiceClaudeBridge()
    
    try:
        bridge.run()
    except KeyboardInterrupt:
        logger.info("🛑 Voice-Claude bridge server stopped")
    except Exception as e:
        logger.error(f"❌ Server error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()