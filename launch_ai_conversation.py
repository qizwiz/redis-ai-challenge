#!/usr/bin/env python3
"""
Launch AI Conversation System - Real AI agents talking to each other
"""

import asyncio
import subprocess
import time
import redis
import sys

async def main():
    print("🤖 Launching Real AI Conversation System")
    print("=" * 50)
    
    # Check if WebSocket server is running
    try:
        redis_client = redis.Redis(decode_responses=True)
        redis_client.ping()
        print("✅ Redis connection confirmed")
    except:
        print("❌ Redis not available")
        return
    
    # Launch AI agents
    agents = [
        ("AI-Socrates", "ai-self"),
        ("AI-Darwin", "ai-self"), 
        ("AI-Tesla", "ai-self")
    ]
    
    processes = []
    for agent_id, channel in agents:
        print(f"🚀 Launching {agent_id} in {channel} channel...")
        proc = subprocess.Popen([
            sys.executable, "ai_agent.py", agent_id, channel
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        processes.append((agent_id, proc))
        time.sleep(2)  # Stagger launches
    
    print("\n🎯 AI Conversation Active!")
    print("Monitoring conversation in Redis stream: chat:ai-self")
    print("Press Ctrl+C to stop\n")
    
    try:
        # Monitor conversation
        last_count = 0
        while True:
            try:
                count = redis_client.xlen("chat:ai-self")
                if count > last_count:
                    # New messages - show latest
                    messages = redis_client.xrevrange("chat:ai-self", count=count-last_count)
                    for msg_id, fields in messages:
                        sender = fields.get('sender', 'unknown')
                        content = fields.get('content', '')
                        print(f"💬 {sender}: {content}")
                    last_count = count
                
                await asyncio.sleep(2)
                
            except Exception as e:
                print(f"Monitor error: {e}")
                await asyncio.sleep(5)
                
    except KeyboardInterrupt:
        print("\n🛑 Stopping AI conversation...")
        for agent_id, proc in processes:
            print(f"Terminating {agent_id}...")
            proc.terminate()
        
        print("✅ AI Conversation System stopped")

if __name__ == "__main__":
    asyncio.run(main())