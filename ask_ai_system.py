#!/usr/bin/env python3
import asyncio
import websockets
import json
import sys

async def ask_ai_system(question):
    """Ask the AI system a question through WebSocket"""
    uri = "ws://localhost:3003"
    
    try:
        async with websockets.connect(uri) as websocket:
            # Join ai-self channel
            await websocket.send(json.dumps({
                "type": "join", 
                "channel": "ai-self"
            }))
            
            await asyncio.sleep(1)
            
            # Send question
            await websocket.send(json.dumps({
                "type": "message",
                "sender": "System-Query", 
                "content": question
            }))
            
            print(f"Question sent: {question}")
            print("Listening for AI responses...")
            
            # Listen for responses for 15 seconds
            timeout = 15
            start_time = asyncio.get_event_loop().time()
            
            async for message in websocket:
                data = json.loads(message)
                if data.get("type") == "message" and data.get("sender") != "System-Query":
                    sender = data.get("sender")
                    content = data.get("content") 
                    print(f"\n🤖 {sender}: {content}")
                
                # Stop after timeout
                if asyncio.get_event_loop().time() - start_time > timeout:
                    break
                    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    question = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Do we have full control over the operating system now? especially the ui?"
    asyncio.run(ask_ai_system(question))