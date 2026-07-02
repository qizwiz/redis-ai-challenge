#!/usr/bin/env python3
import asyncio
import websockets
import json

async def test_os_control():
    """Test OS control through AI conversation"""
    uri = "ws://localhost:3003"
    
    async with websockets.connect(uri) as websocket:
        # Join ai-self channel
        await websocket.send(json.dumps({
            "type": "join", 
            "channel": "ai-self"
        }))
        
        await asyncio.sleep(1)
        
        # Test commands
        commands = [
            "show windows",
            "open Terminal", 
            "create file test.txt"
        ]
        
        for cmd in commands:
            print(f"🧪 Testing: {cmd}")
            
            await websocket.send(json.dumps({
                "type": "message",
                "sender": "Test-System", 
                "content": cmd
            }))
            
            # Wait for response
            await asyncio.sleep(3)
            
            # Listen for a few messages
            try:
                for i in range(3):
                    message = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                    data = json.loads(message)
                    if data.get("sender") == "OS-Controller":
                        print(f"✅ OS Response: {data.get('content')}")
                        break
            except asyncio.TimeoutError:
                print(f"⏰ No response to: {cmd}")
            
            print()

if __name__ == "__main__":
    print("🧪 Testing OS Control Integration")
    print("=" * 40)
    asyncio.run(test_os_control())