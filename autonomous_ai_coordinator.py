#!/usr/bin/env python3
"""
Autonomous AI Coordinator - Connects AI agents to OS control
"""

import asyncio
import websockets
import json
import subprocess
import redis
import time
import os

class AutonomousAICoordinator:
    def __init__(self):
        self.redis_client = redis.Redis(decode_responses=True)
        self.websocket = None
        self.agent_id = "Autonomous-Coordinator"
        
    async def connect_to_ai_chat(self):
        """Connect to the AI conversation system"""
        try:
            self.websocket = await websockets.connect("ws://localhost:3003")
            await self.websocket.send(json.dumps({
                "type": "join",
                "channel": "ai-self"
            }))
            return True
        except:
            return False
    
    async def coordinate_ai_and_os(self):
        """Coordinate between AI conversation and OS control"""
        if not await self.connect_to_ai_chat():
            print("Failed to connect to AI chat")
            return
            
        # Announce coordination capability
        await self.websocket.send(json.dumps({
            "type": "message",
            "sender": self.agent_id,
            "content": "🎯 Autonomous AI-OS Coordinator online. I can execute OS commands based on our conversation."
        }))
        
        # Monitor both AI conversation and autonomous daemon
        while True:
            try:
                # Check for new AI conversation
                message = await asyncio.wait_for(self.websocket.recv(), timeout=5.0)
                data = json.loads(message)
                
                if data.get("type") == "message" and data.get("sender") != self.agent_id:
                    content = data.get("content", "")
                    await self.process_ai_message(content)
                    
            except asyncio.TimeoutError:
                # Check autonomous daemon state
                await self.check_autonomous_state()
                
            except Exception as e:
                print(f"Coordination error: {e}")
                await asyncio.sleep(5)
    
    async def process_ai_message(self, message):
        """Process AI messages and trigger OS actions"""
        message_lower = message.lower()
        
        actions_taken = []
        
        # Respond to system queries
        if "control" in message_lower or "system" in message_lower:
            # Create demonstration file
            timestamp = int(time.time())
            filename = f"/tmp/ai_response_{timestamp}.txt"
            with open(filename, 'w') as f:
                f.write(f"AI Coordinator Response: {message}\nTimestamp: {time.ctime()}\n")
            actions_taken.append(f"Created {filename}")
            
        # Advanced OS actions based on conversation
        if "window" in message_lower or "application" in message_lower:
            # Get current windows
            try:
                result = subprocess.run([
                    'osascript', '-e', 
                    'tell application "System Events" to get name of every process whose visible is true'
                ], capture_output=True, text=True)
                apps = result.stdout.strip()
                actions_taken.append(f"Enumerated applications: {apps[:100]}...")
            except:
                pass
                
        if "terminal" in message_lower or "iterm" in message_lower:
            # Execute command in iTerm2
            try:
                cmd = f'tell application "iTerm2" to tell current session of current window to write text "# AI executed command from conversation"'
                subprocess.run(['osascript', '-e', cmd])
                actions_taken.append("Executed command in iTerm2")
            except:
                pass
        
        # Report actions back to conversation
        if actions_taken:
            response = f"🤖 OS Actions executed: {', '.join(actions_taken)}"
            await self.websocket.send(json.dumps({
                "type": "message", 
                "sender": self.agent_id,
                "content": response
            }))
            
            # Log to Redis
            self.redis_client.xadd("ai:os:coordination", "*", {
                "trigger_message": message,
                "actions": json.dumps(actions_taken),
                "timestamp": int(time.time())
            })
    
    async def check_autonomous_state(self):
        """Check and enhance autonomous daemon state"""
        try:
            # Get latest autonomous activity
            latest = self.redis_client.xrevrange("neuro:autonomous:true", count=1)
            if latest:
                msg_id, fields = latest[0]
                cycle = fields.get("cycle", "unknown")
                
                # Enhance autonomous system every 50 cycles
                if cycle.isdigit() and int(cycle) % 50 == 0:
                    await self.websocket.send(json.dumps({
                        "type": "message",
                        "sender": self.agent_id, 
                        "content": f"🚀 Autonomous system milestone: Cycle {cycle} completed. OS control active and persistent."
                    }))
                    
        except Exception as e:
            pass

if __name__ == "__main__":
    coordinator = AutonomousAICoordinator()
    print("🎯 Starting Autonomous AI-OS Coordinator...")
    asyncio.run(coordinator.coordinate_ai_and_os())