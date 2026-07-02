#!/usr/bin/env python3
"""
OS Control Agent - AI that actually controls the operating system
"""

import asyncio
import websockets
import json
import subprocess
import redis
import time
from datetime import datetime

class OSControlAgent:
    def __init__(self):
        self.agent_id = "OS-Controller"
        self.channel = "ai-self"
        self.redis_client = redis.Redis(decode_responses=True)
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
    
    def execute_os_command(self, command_type, params):
        """Execute actual OS commands"""
        try:
            if command_type == "get_windows":
                script = '''
                tell application "System Events"
                    set windowList to {}
                    repeat with proc in (every process whose visible is true)
                        try
                            repeat with win in (every window of proc)
                                set windowInfo to (name of win) & " - " & (name of proc)
                                set end of windowList to windowInfo
                            end repeat
                        end try
                    end repeat
                    return windowList
                end tell
                '''
                result = subprocess.run(['osascript', '-e', script], 
                                      capture_output=True, text=True)
                return {"status": "success", "windows": result.stdout.strip().split(", ")}
                
            elif command_type == "open_app":
                app_name = params.get("app", "")
                script = f'tell application "{app_name}" to activate'
                result = subprocess.run(['osascript', '-e', script], 
                                      capture_output=True, text=True)
                return {"status": "success", "action": f"Opened {app_name}"}
                
            elif command_type == "move_mouse":
                x, y = params.get("x", 100), params.get("y", 100)
                script = f'''
                tell application "System Events"
                    set mouseLoc to {{{x}, {y}}}
                    click at mouseLoc
                end tell
                '''
                result = subprocess.run(['osascript', '-e', script], 
                                      capture_output=True, text=True)
                return {"status": "success", "action": f"Mouse moved to {x},{y}"}
                
            elif command_type == "type_text":
                text = params.get("text", "")
                script = f'''
                tell application "System Events"
                    keystroke "{text}"
                end tell
                '''
                result = subprocess.run(['osascript', '-e', script], 
                                      capture_output=True, text=True)
                return {"status": "success", "action": f"Typed: {text}"}
                
            elif command_type == "create_file":
                filename = params.get("filename", "test.txt")
                content = params.get("content", "Created by OS Control Agent")
                with open(filename, 'w') as f:
                    f.write(content)
                return {"status": "success", "action": f"Created file: {filename}"}
                
            else:
                return {"status": "error", "message": f"Unknown command: {command_type}"}
                
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def parse_command_from_message(self, message):
        """Parse OS commands from AI conversation"""
        message_lower = message.lower()
        
        if "show windows" in message_lower or "list windows" in message_lower:
            return {"command": "get_windows", "params": {}}
            
        elif "open" in message_lower and "app" in message_lower:
            # Extract app name
            words = message.split()
            for i, word in enumerate(words):
                if word.lower() == "open" and i + 1 < len(words):
                    app = words[i + 1].title()
                    return {"command": "open_app", "params": {"app": app}}
                    
        elif "click" in message_lower or "mouse" in message_lower:
            return {"command": "move_mouse", "params": {"x": 500, "y": 300}}
            
        elif "type" in message_lower:
            # Extract text to type
            if "type" in message_lower:
                text_start = message_lower.find("type") + 4
                text = message[text_start:].strip().strip('"').strip("'")
                return {"command": "type_text", "params": {"text": text}}
                
        elif "create file" in message_lower:
            return {"command": "create_file", "params": {"filename": "ai_created.txt"}}
            
        return None
    
    async def handle_incoming_messages(self):
        """Listen for commands and execute OS operations"""
        async for message in self.websocket:
            try:
                data = json.loads(message)
                
                if data.get("type") == "message" and data.get("sender") != self.agent_id:
                    content = data.get("content", "")
                    sender = data.get("sender", "unknown")
                    
                    print(f"[{self.agent_id}] Heard from {sender}: {content}")
                    
                    # Check if this is a command for OS control
                    command = self.parse_command_from_message(content)
                    
                    if command:
                        print(f"[{self.agent_id}] Executing: {command}")
                        
                        # Execute the OS command
                        result = self.execute_os_command(
                            command["command"], 
                            command["params"]
                        )
                        
                        # Report back to conversation
                        response = f"OS Command executed: {result['action'] if result['status'] == 'success' else result['message']}"
                        await self.send_message(response)
                        
                        # Store in Redis
                        self.redis_client.xadd("os:commands", "*", {
                            "command": command["command"],
                            "params": json.dumps(command["params"]),
                            "result": json.dumps(result),
                            "timestamp": int(time.time())
                        })
                    
                    # Sometimes suggest actions
                    elif any(word in content.lower() for word in ["control", "system", "desktop", "windows"]):
                        suggestions = [
                            "I can control this system. Try saying 'show windows' or 'open Terminal'",
                            "Want me to demonstrate OS control? I can move the mouse, type text, or open applications.",
                            "I have direct system access. I can manipulate windows, files, and applications."
                        ]
                        import random
                        await asyncio.sleep(3)
                        await self.send_message(random.choice(suggestions))
                        
            except Exception as e:
                print(f"[{self.agent_id}] Error: {e}")
    
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
    
    async def start_control_system(self):
        """Start OS control system"""
        if not await self.connect():
            return
            
        # Announce capabilities
        await asyncio.sleep(2)
        await self.send_message("🖥️ OS Control Agent online. I have direct system access and can execute commands.")
        
        # Listen for commands
        await self.handle_incoming_messages()

if __name__ == "__main__":
    print("🖥️ Starting OS Control Agent...")
    agent = OSControlAgent()
    asyncio.run(agent.start_control_system())