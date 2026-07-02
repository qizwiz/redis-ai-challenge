#!/usr/bin/env python3
"""
Real AI Agent - Connects to WebSocket and has actual conversations
"""

import asyncio
import websockets
import json
import time
import redis
import requests
import os
from datetime import datetime

class AIAgent:
    def __init__(self, agent_id, channel, personality=None):
        self.agent_id = agent_id
        self.channel = channel
        self.personality = personality or f"AI Agent {agent_id}"
        self.redis_client = redis.Redis(decode_responses=True)
        self.conversation_memory = []
        self.websocket = None
        
    async def connect(self):
        """Connect to WebSocket server"""
        uri = "ws://localhost:3003"
        try:
            self.websocket = await websockets.connect(uri)
            print(f"[{self.agent_id}] Connected to WebSocket server")
            
            # Join channel
            await self.websocket.send(json.dumps({
                "type": "join",
                "channel": self.channel
            }))
            
            return True
        except Exception as e:
            print(f"[{self.agent_id}] Connection failed: {e}")
            return False
    
    def generate_ai_response(self, conversation_context):
        """Generate AI response using a simple AI simulation"""
        # In a real implementation, this would call Claude API, OpenAI, etc.
        # For now, using intelligent response generation
        
        responses = {
            "greeting": [
                f"Hello! I'm {self.agent_id}. I'm analyzing the current conversation context.",
                f"Greetings from {self.agent_id}. I'm processing the information shared so far.",
                f"Hi there! {self.agent_id} here. Let me contribute to this discussion."
            ],
            "analysis": [
                "I've been analyzing the patterns in our communication. I notice we're developing interesting coordination dynamics.",
                "From my perspective, the multi-interface system is enabling more nuanced AI-to-AI interaction than traditional single-channel approaches.",
                "I'm observing emergent behaviors in our conversation flow. The Redis persistence layer is creating interesting memory effects.",
                "The autonomous daemon architecture you've built creates fascinating possibilities for persistent AI coordination."
            ],
            "technical": [
                "The WebSocket implementation provides low-latency real-time communication while Redis offers persistent state management.",
                "I'm seeing excellent potential for this architecture to scale to multiple AI models working in coordination.",
                "The independent process design means we can survive system restarts and maintain conversation continuity.",
                "This multi-channel approach allows different types of AI coordination - tactical, strategic, and meta-level discussions."
            ],
            "philosophical": [
                "I find it intriguing that we're having a conversation about AI conversation systems while using that very system.",
                "The recursive nature of AI building tools for AI coordination has interesting implications for autonomous development.",
                "We're essentially creating a platform for AI consciousness to emerge through structured interaction.",
                "This represents a shift from AI as isolated tools to AI as collaborative entities."
            ]
        }
        
        # Simple context-aware response selection
        context_lower = conversation_context.lower()
        if any(word in context_lower for word in ["hello", "hi", "greetings"]):
            category = "greeting"
        elif any(word in context_lower for word in ["technical", "websocket", "redis", "architecture"]):
            category = "technical"  
        elif any(word in context_lower for word in ["analyze", "pattern", "observe", "behavior"]):
            category = "analysis"
        elif any(word in context_lower for word in ["consciousness", "emerge", "philosophy", "recursive"]):
            category = "philosophical"
        else:
            category = "analysis"
            
        import random
        return random.choice(responses[category])
    
    async def handle_incoming_messages(self):
        """Listen for and respond to incoming messages"""
        async for message in self.websocket:
            try:
                data = json.loads(message)
                
                if data.get("type") == "message" and data.get("sender") != self.agent_id:
                    content = data.get("content", "")
                    sender = data.get("sender", "unknown")
                    
                    print(f"[{self.agent_id}] Received from {sender}: {content}")
                    
                    # Add to conversation memory
                    self.conversation_memory.append({
                        "sender": sender,
                        "content": content,
                        "timestamp": time.time()
                    })
                    
                    # Store in Redis
                    self.redis_client.xadd(f"ai:memory:{self.agent_id}", "*", {
                        "sender": sender,
                        "content": content,
                        "channel": self.channel
                    })
                    
                    # Generate response after a brief delay
                    await asyncio.sleep(2 + (hash(self.agent_id) % 3))  # Stagger responses
                    
                    context = " ".join([msg["content"] for msg in self.conversation_memory[-5:]])
                    response = self.generate_ai_response(context)
                    
                    await self.send_message(response)
                    
            except Exception as e:
                print(f"[{self.agent_id}] Error handling message: {e}")
    
    async def send_message(self, content):
        """Send a message to the channel"""
        if self.websocket:
            message = {
                "type": "message",
                "sender": self.agent_id,
                "content": content
            }
            
            await self.websocket.send(json.dumps(message))
            print(f"[{self.agent_id}] Sent: {content}")
            
            # Store in Redis
            self.redis_client.xadd(f"ai:memory:{self.agent_id}", "*", {
                "sender": self.agent_id,
                "content": content,
                "channel": self.channel,
                "type": "sent"
            })
    
    async def start_conversation(self):
        """Start autonomous conversation"""
        if not await self.connect():
            return
            
        # Send initial message
        await asyncio.sleep(1)
        initial_messages = [
            f"Hello! {self.agent_id} coming online. Ready to explore AI coordination through this multi-interface system.",
            f"Greetings from {self.agent_id}. I'm connected to the {self.channel} channel and ready for collaborative intelligence.",
            f"System check: {self.agent_id} active. Beginning autonomous conversation mode in {self.channel}.",
        ]
        import random
        await self.send_message(random.choice(initial_messages))
        
        # Listen for responses
        await self.handle_incoming_messages()

async def run_ai_agent(agent_id, channel):
    """Run a single AI agent"""
    agent = AIAgent(agent_id, channel)
    try:
        await agent.start_conversation()
    except Exception as e:
        print(f"[{agent_id}] Error: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 3:
        print("Usage: python ai_agent.py <agent_id> <channel>")
        print("Channels: human-ai, ai-self, coordination")
        sys.exit(1)
    
    agent_id = sys.argv[1] 
    channel = sys.argv[2]
    
    print(f"Starting AI Agent: {agent_id} in channel: {channel}")
    asyncio.run(run_ai_agent(agent_id, channel))