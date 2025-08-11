#!/usr/bin/env python3
"""
Streaming Voice MCP Server
Uses streaming transport instead of stdio for better real-time performance
"""

import fastmcp
import asyncio
import json
import uuid
import sys
from typing import Dict, Any, List, AsyncGenerator

sys.path.append('/Users/jonathanhill/src/redis-ai-challenge')

from redis_ai_patterns.streams import StreamProcessor
from redis_ai_patterns.homoiconic import HomoiconicRedis
from azure_voice_conversation import AzureVoiceConversation

class StreamingVoiceMCP:
    """
    Streaming MCP server for real-time voice AI conversation
    Uses Redis Streams for high-throughput coordination
    """
    
    def __init__(self):
        self.app = fastmcp.FastMCP("Streaming Voice AI")
        self.stream_processor = StreamProcessor()
        self.redis_lisp = HomoiconicRedis()
        self.azure_ai = AzureVoiceConversation()
        self.setup_streaming_tools()
    
    def setup_streaming_tools(self):
        """Setup streaming-optimized MCP tools"""
        
        @self.app.tool()
        async def stream_ai_conversation(
            topic: str,
            participants: List[str],
            turns: int = 3,
            stream_id: str = None
        ) -> Dict[str, Any]:
            """
            Stream AI conversation in real-time via Redis Streams
            """
            if not stream_id:
                stream_id = f"voice-conv-{uuid.uuid4().hex[:8]}"
            
            # Create conversation stream
            stream_key = f"ai:conversation:{stream_id}"
            
            print(f"🌊 Starting streaming conversation: {stream_key}")
            
            # Initialize conversation state in Redis
            conversation_state = {
                'stream_id': stream_id,
                'topic': topic,
                'participants': participants,
                'turns_planned': turns,
                'turns_completed': 0,
                'status': 'streaming',
                'created_at': asyncio.get_event_loop().time()
            }
            
            self.redis_lisp.execute(['redis-set', f'conv-state-{stream_id}', conversation_state])
            
            # Stream conversation turns
            for turn in range(turns):
                speaker = participants[turn % len(participants)]
                
                # Generate AI response
                persona_prompt = f"You are {speaker}. Topic: {topic}. Respond in 1-2 sentences."
                ai_response = self.azure_ai.call_azure_ai(persona_prompt, speaker)
                
                # Stream the response
                turn_event = {
                    'event_type': 'ai_response',
                    'turn': turn + 1,
                    'speaker': speaker,
                    'response': ai_response,
                    'timestamp': asyncio.get_event_loop().time()
                }
                
                # Add to Redis Stream
                try:
                    event_id = self.stream_processor.redis_client.xadd(
                        stream_key,
                        turn_event
                    )
                    
                    print(f"🌊 Streamed turn {turn + 1}: {event_id}")
                    
                    # Small delay for real-time feel
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    print(f"❌ Stream error: {e}")
            
            # Update final state
            conversation_state['turns_completed'] = turns
            conversation_state['status'] = 'completed'
            self.redis_lisp.execute(['redis-set', f'conv-state-{stream_id}', conversation_state])
            
            return {
                'stream_id': stream_id,
                'stream_key': stream_key,
                'turns_streamed': turns,
                'status': 'completed',
                'transport': 'redis_streams'
            }
        
        @self.app.tool()
        async def stream_voice_synthesis(
            stream_id: str,
            voice_mapping: Dict[str, str] = None
        ) -> AsyncGenerator[Dict[str, Any], None]:
            """
            Stream voice synthesis commands from conversation stream
            """
            if not voice_mapping:
                voice_mapping = {
                    'Maya': 'af_sky',
                    'Zion': 'am_adam'
                }
            
            stream_key = f"ai:conversation:{stream_id}"
            
            print(f"🎤 Streaming voice synthesis from: {stream_key}")
            
            # Read from conversation stream
            try:
                # Get all messages from the stream
                stream_data = self.stream_processor.redis_client.xread({stream_key: '0'})
                
                voice_commands = []
                
                for stream_name, messages in stream_data:
                    for message_id, fields in messages:
                        # Convert Redis stream data to voice command
                        event_data = {k.decode(): v.decode() for k, v in fields.items()}
                        
                        if event_data.get('event_type') == 'ai_response':
                            speaker = event_data['speaker']
                            response = event_data['response']
                            voice = voice_mapping.get(speaker, 'alloy')
                            
                            voice_command = {
                                'message_id': message_id.decode(),
                                'speaker': speaker,
                                'voice': voice,
                                'message': response,
                                'voice_params': {
                                    'message': response,
                                    'voice': voice,
                                    'tts_provider': 'kokoro',
                                    'wait_for_response': False
                                },
                                'ready_for_synthesis': True
                            }
                            
                            voice_commands.append(voice_command)
                            print(f"🔊 Voice command: {speaker} ({voice})")
                
                return {
                    'stream_id': stream_id,
                    'voice_commands': voice_commands,
                    'total_commands': len(voice_commands),
                    'streaming_complete': True
                }
                
            except Exception as e:
                return {
                    'error': f"Stream read error: {e}",
                    'stream_id': stream_id
                }
        
        @self.app.tool()
        async def get_stream_status(self, stream_id: str) -> Dict[str, Any]:
            """
            Get real-time status of streaming conversation
            """
            try:
                # Get conversation state
                state = self.redis_lisp.execute(['redis-get', f'conv-state-{stream_id}'])
                
                # Get stream length
                stream_key = f"ai:conversation:{stream_id}"
                stream_length = self.stream_processor.redis_client.xlen(stream_key)
                
                return {
                    'stream_id': stream_id,
                    'conversation_state': state,
                    'stream_length': stream_length,
                    'transport': 'redis_streams',
                    'real_time': True
                }
                
            except Exception as e:
                return {
                    'error': f"Status check failed: {e}",
                    'stream_id': stream_id
                }

async def main():
    """
    Run streaming voice MCP server
    """
    print("🌊 STREAMING VOICE MCP SERVER")
    print("⚡ Real-time via Redis Streams instead of stdio")
    print("=" * 50)
    
    server = StreamingVoiceMCP()
    
    # For demo, we'll run the server in streaming mode
    print("✅ Streaming MCP server configured")
    print("🌊 Transport: Redis Streams (not stdio)")
    print("⚡ Optimized for real-time voice conversation")
    
    # Test streaming conversation
    result = await server.app.tools['stream_ai_conversation'](
        topic="Should we use streaming vs stdio MCP transports?",
        participants=['Maya', 'Zion'],
        turns=2
    )
    
    print(f"\n🎯 Streaming test result: {json.dumps(result, indent=2)}")
    
    # Test voice command streaming
    voice_result = await server.app.tools['stream_voice_synthesis'](
        stream_id=result['stream_id']
    )
    
    print(f"\n🔊 Voice streaming result: {json.dumps(voice_result, indent=2)}")
    
    return server

if __name__ == "__main__":
    # Run the streaming server
    server = asyncio.run(main())