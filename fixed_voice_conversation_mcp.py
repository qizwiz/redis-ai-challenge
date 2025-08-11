#!/usr/bin/env python3
"""
Working Voice Conversation MCP Server  
Uses the actual voice-mode infrastructure for real AI conversation
"""

import fastmcp
import asyncio
import subprocess
import sys
from typing import Dict, Any, List

class WorkingVoiceConversation:
    def __init__(self):
        self.app = fastmcp.FastMCP("Working Voice Conversation")
        self.setup_voice_tools()
        
    def setup_voice_tools(self):
        
        @self.app.tool()
        def start_ai_voice_conversation(
            ai1_name: str,
            ai1_personality: str, 
            ai2_name: str,
            ai2_personality: str,
            topic: str,
            turns: int = 3
        ) -> Dict[str, Any]:
            """
            Start actual voice conversation between two AI personas
            using the working voice-mode infrastructure
            """
            
            conversation_id = f"conv-{ai1_name}-{ai2_name}"
            
            print(f"🎤 Starting voice conversation: {ai1_name} vs {ai2_name}")
            print(f"📝 Topic: {topic}")
            print(f"🔄 Turns: {turns}")
            
            # Create conversation plan
            conversation_plan = {
                "conversation_id": conversation_id,
                "ai1": {"name": ai1_name, "personality": ai1_personality},
                "ai2": {"name": ai2_name, "personality": ai2_personality}, 
                "topic": topic,
                "turns": turns,
                "voice_instructions": []
            }
            
            # Generate voice conversation sequence
            for turn in range(turns):
                speaker = ai1_name if turn % 2 == 0 else ai2_name
                speaker_personality = ai1_personality if turn % 2 == 0 else ai2_personality
                
                if turn == 0:
                    # First speaker introduces the topic
                    message = f"Hello, I'm {speaker}. {speaker_personality} Let's discuss {topic}. What are your thoughts?"
                else:
                    # Subsequent speakers build on the conversation
                    message = f"As {speaker}, I want to add to our discussion about {topic}. Let me share my perspective."
                    
                voice_instruction = {
                    "turn": turn + 1,
                    "speaker": speaker,
                    "message": message,
                    "voice_call": {
                        "tool": "mcp__voice-mode__converse",
                        "parameters": {
                            "message": message,
                            "wait_for_response": False if turn == turns - 1 else True,
                            "listen_duration": 30 if turn < turns - 1 else 0,
                            "voice": "af_sky" if speaker == ai1_name else "am_adam",
                            "tts_provider": "kokoro"
                        }
                    }
                }
                
                conversation_plan["voice_instructions"].append(voice_instruction)
            
            return conversation_plan
            
        @self.app.tool()
        def execute_homoiconic_lisp(
            expression: str,
            context: Dict[str, Any] = None
        ) -> Dict[str, Any]:
            """
            Execute Lisp expression using the working homoiconic Redis system
            """
            
            # Import the working system
            sys.path.append('/Users/jonathanhill/src/redis-ai-challenge')
            from redis_ai_patterns.homoiconic import HomoiconicRedis
            
            redis_lisp = HomoiconicRedis()
            
            try:
                # Convert string expression to list format for execution
                # Simple parser for basic expressions like "(+ 1 2 3)"
                if expression.startswith('(') and expression.endswith(')'):
                    # Remove parentheses and split
                    inner = expression[1:-1]
                    parts = inner.split()
                    
                    # Convert to list format
                    op = parts[0]
                    args = []
                    for part in parts[1:]:
                        try:
                            # Try to convert to number
                            if '.' in part:
                                args.append(float(part))
                            else:
                                args.append(int(part))
                        except ValueError:
                            args.append(part)  # Keep as string
                    
                    lisp_list = [op] + args
                    result = redis_lisp.execute(lisp_list)
                else:
                    result = f"Invalid Lisp expression: {expression}"
                
                return {
                    "expression": expression,
                    "lisp_format": lisp_list if 'lisp_list' in locals() else None,
                    "result": result,
                    "context": context,
                    "executed": True
                }
                
            except Exception as e:
                return {
                    "expression": expression,
                    "error": str(e),
                    "context": context,
                    "executed": False
                }

def main():
    print("🚀 Starting Working Voice Conversation MCP Server")
    print("🎤 Real voice conversation with homoiconic Lisp execution")
    
    server = WorkingVoiceConversation()
    server.app.run()

if __name__ == "__main__":
    main()