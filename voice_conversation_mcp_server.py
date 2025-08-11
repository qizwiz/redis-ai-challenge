#!/usr/bin/env python3
"""
Voice Conversation MCP Server
Ad hoc FastMCP server enabling turn-by-turn voice conversation with Claude Code in vterm/emacs.

Usage: python voice_conversation_mcp_server.py
"""

import asyncio
import logging
import sys
import traceback
from typing import Optional, Dict, Any
import json
import os
import subprocess
import tempfile
import time
from pathlib import Path

import fastmcp

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Voice mode integration
try:
    # Import voice mode tools directly
    sys.path.append(str(Path(__file__).parent))
    from mcp__voice_mode__converse import converse
    VOICE_MODE_AVAILABLE = True
    logger.info("✅ Voice mode integration available")
except ImportError as e:
    VOICE_MODE_AVAILABLE = False
    logger.warning(f"❌ Voice mode not available: {e}")

class VoiceConversationServer:
    """FastMCP server for voice conversation with Claude Code"""
    
    def __init__(self):
        self.app = fastmcp.FastMCP("Voice Conversation Server")
        self.conversation_active = False
        self.conversation_context = []
        self.setup_tools()
        
    def setup_tools(self):
        """Register MCP tools for voice conversation"""
        
        @self.app.tool()
        async def start_voice_conversation(
            initial_message: str = "Hello! I'm ready for a voice conversation. What would you like to talk about?",
            voice: str = "af_sky", 
            listen_duration: float = 30.0,
            min_listen_duration: float = 2.0
        ) -> Dict[str, Any]:
            """
            Start a continuous voice conversation loop.
            
            Args:
                initial_message: First message to speak to the user
                voice: TTS voice to use (default: af_sky)
                listen_duration: How long to listen for response (seconds)
                min_listen_duration: Minimum listen time before silence detection
            
            Returns:
                Conversation session status
            """
            self.conversation_active = True
            self.conversation_context = []
            
            logger.info("🎤 Starting voice conversation...")
            
            try:
                # Speak initial message and start listening
                if VOICE_MODE_AVAILABLE:
                    result = await self._voice_interact(
                        initial_message, 
                        voice=voice, 
                        listen_duration=listen_duration,
                        min_listen_duration=min_listen_duration
                    )
                    
                    return {
                        "status": "conversation_started",
                        "initial_response": result,
                        "message": "Voice conversation started successfully",
                        "session_id": int(time.time())
                    }
                else:
                    return {
                        "status": "error", 
                        "message": "Voice mode not available"
                    }
                    
            except Exception as e:
                logger.error(f"Error starting conversation: {e}")
                return {
                    "status": "error",
                    "message": f"Failed to start conversation: {str(e)}"
                }
        
        @self.app.tool()
        async def continue_voice_conversation(
            response_text: str,
            voice: str = "af_sky",
            listen_duration: float = 30.0,
            min_listen_duration: float = 2.0,
            add_context: bool = True
        ) -> Dict[str, Any]:
            """
            Continue the voice conversation by speaking a response and listening for reply.
            
            Args:
                response_text: Text response to speak to the user
                voice: TTS voice to use
                listen_duration: How long to listen for response (seconds) 
                min_listen_duration: Minimum listen time before silence detection
                add_context: Whether to add this exchange to conversation context
                
            Returns:
                User's voice response transcription
            """
            if not self.conversation_active:
                return {
                    "status": "error",
                    "message": "No active conversation. Use start_voice_conversation first."
                }
            
            try:
                # Add to context if requested
                if add_context:
                    self.conversation_context.append({
                        "role": "assistant", 
                        "content": response_text,
                        "timestamp": time.time()
                    })
                
                # Speak response and listen for user reply
                if VOICE_MODE_AVAILABLE:
                    user_response = await self._voice_interact(
                        response_text,
                        voice=voice,
                        listen_duration=listen_duration,
                        min_listen_duration=min_listen_duration
                    )
                    
                    # Add user response to context
                    if add_context and user_response:
                        self.conversation_context.append({
                            "role": "user",
                            "content": user_response,
                            "timestamp": time.time()
                        })
                    
                    return {
                        "status": "success",
                        "user_response": user_response,
                        "context_length": len(self.conversation_context)
                    }
                else:
                    return {
                        "status": "error",
                        "message": "Voice mode not available"
                    }
                    
            except Exception as e:
                logger.error(f"Error in conversation: {e}")
                return {
                    "status": "error", 
                    "message": f"Conversation error: {str(e)}"
                }
        
        @self.app.tool() 
        async def speak_only(
            text: str,
            voice: str = "af_sky",
            wait_for_response: bool = False
        ) -> Dict[str, Any]:
            """
            Just speak text without listening for a response.
            
            Args:
                text: Text to speak
                voice: TTS voice to use
                wait_for_response: Whether to wait for user response
                
            Returns:
                Speech completion status
            """
            try:
                if VOICE_MODE_AVAILABLE:
                    result = await self._voice_speak_only(text, voice, wait_for_response)
                    return {
                        "status": "success",
                        "message": "Text spoken successfully", 
                        "result": result
                    }
                else:
                    return {
                        "status": "error",
                        "message": "Voice mode not available"
                    }
            except Exception as e:
                return {
                    "status": "error",
                    "message": f"Speech error: {str(e)}"
                }
        
        @self.app.tool()
        async def listen_only(
            listen_duration: float = 30.0,
            min_listen_duration: float = 2.0,
            prompt: str = "I'm listening..."
        ) -> Dict[str, Any]:
            """
            Just listen for user input without speaking first.
            
            Args:
                listen_duration: How long to listen (seconds)
                min_listen_duration: Minimum listen time
                prompt: Optional prompt to display (not spoken)
                
            Returns:
                Transcribed user input
            """
            try:
                if VOICE_MODE_AVAILABLE:
                    logger.info(f"🎤 {prompt}")
                    result = await self._voice_listen_only(listen_duration, min_listen_duration)
                    return {
                        "status": "success",
                        "transcription": result,
                        "message": "Successfully captured voice input"
                    }
                else:
                    return {
                        "status": "error",
                        "message": "Voice mode not available"
                    }
            except Exception as e:
                return {
                    "status": "error",
                    "message": f"Listen error: {str(e)}"
                }
        
        @self.app.tool()
        async def end_voice_conversation() -> Dict[str, Any]:
            """
            End the current voice conversation session.
            
            Returns:
                Conversation summary and cleanup status
            """
            if not self.conversation_active:
                return {
                    "status": "info",
                    "message": "No active conversation to end"
                }
            
            self.conversation_active = False
            context_summary = {
                "total_exchanges": len([c for c in self.conversation_context if c["role"] == "user"]),
                "duration_minutes": (time.time() - self.conversation_context[0]["timestamp"]) / 60 if self.conversation_context else 0,
                "context_entries": len(self.conversation_context)
            }
            
            self.conversation_context = []
            
            return {
                "status": "ended",
                "message": "Voice conversation ended",
                "summary": context_summary
            }
        
        @self.app.tool()
        async def get_conversation_context() -> Dict[str, Any]:
            """
            Get the current conversation context and status.
            
            Returns:
                Current conversation state and context
            """
            return {
                "active": self.conversation_active,
                "context_length": len(self.conversation_context),
                "context": self.conversation_context[-5:] if len(self.conversation_context) > 5 else self.conversation_context,  # Last 5 entries
                "voice_mode_available": VOICE_MODE_AVAILABLE
            }
    
    async def _voice_interact(self, text: str, voice: str = "af_sky", listen_duration: float = 30.0, min_listen_duration: float = 2.0) -> Optional[str]:
        """Speak text and listen for response using voice mode"""
        try:
            # Use the voice-mode converse function
            result = await asyncio.to_thread(
                self._call_voice_converse,
                text,
                voice=voice,
                listen_duration=listen_duration,
                min_listen_duration=min_listen_duration,
                wait_for_response=True
            )
            return result
        except Exception as e:
            logger.error(f"Voice interaction error: {e}")
            return None
    
    async def _voice_speak_only(self, text: str, voice: str = "af_sky", wait_for_response: bool = False) -> str:
        """Speak text only using voice mode"""
        try:
            result = await asyncio.to_thread(
                self._call_voice_converse,
                text,
                voice=voice,
                wait_for_response=wait_for_response
            )
            return result
        except Exception as e:
            logger.error(f"Voice speak error: {e}")
            return f"Error: {str(e)}"
    
    async def _voice_listen_only(self, listen_duration: float = 30.0, min_listen_duration: float = 2.0) -> Optional[str]:
        """Listen for voice input only"""
        try:
            # For listen-only, we speak empty/silence and just wait for response
            result = await asyncio.to_thread(
                self._call_voice_converse,
                "",  # Empty message
                listen_duration=listen_duration,
                min_listen_duration=min_listen_duration,
                wait_for_response=True
            )
            return result
        except Exception as e:
            logger.error(f"Voice listen error: {e}")
            return None
    
    def _call_voice_converse(self, message: str, **kwargs) -> str:
        """Synchronous wrapper for voice converse call"""
        try:
            # Use subprocess to call the voice mode converse function
            # This ensures we use the existing voice-mode infrastructure
            cmd = [
                sys.executable, "-c",
                f"""
import sys
sys.path.append('{Path(__file__).parent}')

# Import voice mode directly
try:
    from mcp__voice_mode__converse import converse
    result = converse('{message}', **{kwargs})
    print(result if result else '')
except Exception as e:
    print(f'Error: {{str(e)}}')
"""
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=kwargs.get('listen_duration', 30) + 10)
            
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                logger.error(f"Voice converse error: {result.stderr}")
                return f"Error: {result.stderr.strip()}"
                
        except subprocess.TimeoutExpired:
            logger.error("Voice converse timeout")
            return "Error: Voice interaction timeout"
        except Exception as e:
            logger.error(f"Voice converse call error: {e}")
            return f"Error: {str(e)}"
    
    def run(self, port: int = 8765):
        """Run the FastMCP server"""
        logger.info(f"🚀 Starting Voice Conversation MCP Server on port {port}")
        logger.info("Available tools:")
        logger.info("  - start_voice_conversation: Begin voice chat session")
        logger.info("  - continue_voice_conversation: Speak response and listen for reply")
        logger.info("  - speak_only: Speak text without listening")
        logger.info("  - listen_only: Listen for voice input without speaking")
        logger.info("  - end_voice_conversation: End current session")
        logger.info("  - get_conversation_context: Get current conversation state")
        
        # Run the FastMCP server
        self.app.run(port=port)

def main():
    """Main entry point"""
    # Check for port argument
    port = 8765
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            logger.error("Invalid port number")
            sys.exit(1)
    
    # Create and run server
    server = VoiceConversationServer()
    
    try:
        server.run(port=port)
    except KeyboardInterrupt:
        logger.info("🛑 Voice conversation server stopped")
    except Exception as e:
        logger.error(f"Server error: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()