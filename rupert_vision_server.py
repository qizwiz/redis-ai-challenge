#!/usr/bin/env python3
"""
RUPERT VISION SERVER - Live screensharing for development collaboration
Stream what Rupert sees to Redis and web interface
Real-time visual feedback for autonomous development
"""

import asyncio
import time
import redis
import json
import base64
import io
from PIL import Image
import pyautogui
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading
import websockets
import socket

class RupertVisionServer:
    """Live screensharing server for Rupert's vision"""
    
    def __init__(self):
        self.r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        self.running = True
        self.screenshot_interval = 1.0  # 1 FPS for development
        self.clients = set()
        
        print("👁️ RUPERT VISION SERVER STARTING")
        print("📹 Live screensharing enabled")
        print("🌐 Web interface will be available")
    
    def capture_and_encode_screen(self):
        """Capture screen and encode for transmission"""
        try:
            # Take screenshot
            screenshot = pyautogui.screenshot()
            
            # Resize for faster transmission (optional)
            screenshot = screenshot.resize((1440, 900), Image.Resampling.LANCZOS)
            
            # Convert to base64 for Redis storage
            buffer = io.BytesIO()
            screenshot.save(buffer, format='JPEG', quality=70)
            img_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            # Get mouse position for overlay
            mouse_pos = pyautogui.position()
            
            return {
                'image': img_base64,
                'timestamp': time.time(),
                'mouse_x': mouse_pos.x,
                'mouse_y': mouse_pos.y,
                'size': screenshot.size
            }
            
        except Exception as e:
            print(f"📹 Screen capture error: {e}")
            return None
    
    async def stream_screen_to_redis(self):
        """Continuously stream screen to Redis"""
        
        while self.running:
            try:
                screen_data = self.capture_and_encode_screen()
                
                if screen_data:
                    # Store latest screenshot in Redis
                    self.r.hset("rupert:live_screen", {
                        'image': screen_data['image'],
                        'timestamp': str(screen_data['timestamp']),
                        'mouse_x': str(screen_data['mouse_x']),
                        'mouse_y': str(screen_data['mouse_y']),
                        'width': str(screen_data['size'][0]),
                        'height': str(screen_data['size'][1])
                    })
                    
                    # Also stream to Redis stream for history
                    self.r.xadd("rupert:screen_stream", {
                        'timestamp': str(screen_data['timestamp']),
                        'mouse_pos': f"{screen_data['mouse_x']},{screen_data['mouse_y']}",
                        'size': f"{screen_data['size'][0]}x{screen_data['size'][1]}"
                    })
                    
                    # Notify WebSocket clients (if any)
                    if self.clients:
                        await self.broadcast_to_websocket_clients(screen_data)
                
                await asyncio.sleep(self.screenshot_interval)
                
            except Exception as e:
                print(f"📹 Streaming error: {e}")
                await asyncio.sleep(2)
    
    async def broadcast_to_websocket_clients(self, screen_data):
        """Broadcast screen data to connected WebSocket clients"""
        if not self.clients:
            return
            
        message = json.dumps({
            'type': 'screen_update',
            'image': screen_data['image'],
            'timestamp': screen_data['timestamp'],
            'mouse': {'x': screen_data['mouse_x'], 'y': screen_data['mouse_y']},
            'size': {'width': screen_data['size'][0], 'height': screen_data['size'][1]}
        })
        
        # Send to all connected clients
        disconnected_clients = set()
        for client in self.clients:
            try:
                await client.send(message)
            except:
                disconnected_clients.add(client)
        
        # Remove disconnected clients
        self.clients -= disconnected_clients
    
    def create_web_interface(self):
        """Create simple web interface for viewing screen"""
        html_content = '''<!DOCTYPE html>
<html>
<head>
    <title>Rupert Vision - Live Screen</title>
    <style>
        body { font-family: Arial, sans-serif; background: #1a1a1a; color: white; margin: 0; padding: 20px; }
        .container { max-width: 1200px; margin: 0 auto; }
        .screen-container { position: relative; border: 2px solid #333; border-radius: 8px; overflow: hidden; }
        .screen-image { width: 100%; height: auto; display: block; }
        .mouse-cursor { position: absolute; width: 20px; height: 20px; background: red; border-radius: 50%; pointer-events: none; transform: translate(-10px, -10px); }
        .info { margin-top: 20px; padding: 15px; background: #2a2a2a; border-radius: 8px; }
        .status { color: #00ff00; }
        h1 { color: #4CAF50; }
    </style>
</head>
<body>
    <div class="container">
        <h1>👁️ Rupert Vision Server</h1>
        <div class="info">
            <div class="status">🔴 <span id="status">Connecting...</span></div>
            <div>📹 Resolution: <span id="resolution">Loading...</span></div>
            <div>🖱️ Mouse: <span id="mouse-pos">Loading...</span></div>
            <div>⏱️ Last Update: <span id="timestamp">Loading...</span></div>
        </div>
        
        <div class="screen-container">
            <img id="screen" class="screen-image" src="" alt="Rupert's Screen View">
            <div id="mouse-cursor" class="mouse-cursor"></div>
        </div>
    </div>
    
    <script>
        const ws = new WebSocket('ws://localhost:8765');
        const screenImg = document.getElementById('screen');
        const mouseCursor = document.getElementById('mouse-cursor');
        const statusEl = document.getElementById('status');
        const resolutionEl = document.getElementById('resolution');
        const mousePosEl = document.getElementById('mouse-pos');
        const timestampEl = document.getElementById('timestamp');
        
        ws.onopen = function() {
            statusEl.textContent = '🟢 Connected';
            statusEl.style.color = '#00ff00';
        };
        
        ws.onmessage = function(event) {
            const data = JSON.parse(event.data);
            if (data.type === 'screen_update') {
                screenImg.src = 'data:image/jpeg;base64,' + data.image;
                
                // Update mouse cursor position (scaled to display size)
                const rect = screenImg.getBoundingClientRect();
                const scaleX = rect.width / data.size.width;
                const scaleY = rect.height / data.size.height;
                const x = data.mouse.x * scaleX;
                const y = data.mouse.y * scaleY;
                
                mouseCursor.style.left = x + 'px';
                mouseCursor.style.top = y + 'px';
                
                // Update info
                resolutionEl.textContent = data.size.width + 'x' + data.size.height;
                mousePosEl.textContent = data.mouse.x + ', ' + data.mouse.y;
                timestampEl.textContent = new Date(data.timestamp * 1000).toLocaleTimeString();
            }
        };
        
        ws.onclose = function() {
            statusEl.textContent = '🔴 Disconnected';
            statusEl.style.color = '#ff0000';
        };
        
        ws.onerror = function() {
            statusEl.textContent = '⚠️ Error';
            statusEl.style.color = '#ffaa00';
        };
    </script>
</body>
</html>'''
        
        with open('/tmp/rupert_vision.html', 'w') as f:
            f.write(html_content)
        
        print("🌐 Web interface created: /tmp/rupert_vision.html")
    
    async def websocket_server(self, websocket, path):
        """WebSocket server for real-time screen sharing"""
        print(f"🔌 WebSocket client connected from {websocket.remote_address}")
        self.clients.add(websocket)
        
        try:
            # Send initial screen data
            screen_data = self.capture_and_encode_screen()
            if screen_data:
                await websocket.send(json.dumps({
                    'type': 'screen_update',
                    'image': screen_data['image'],
                    'timestamp': screen_data['timestamp'],
                    'mouse': {'x': screen_data['mouse_x'], 'y': screen_data['mouse_y']},
                    'size': {'width': screen_data['size'][0], 'height': screen_data['size'][1]}
                }))
            
            # Keep connection alive
            await websocket.wait_closed()
            
        except Exception as e:
            print(f"🔌 WebSocket error: {e}")
        finally:
            self.clients.discard(websocket)
            print("🔌 WebSocket client disconnected")
    
    def start_websocket_server(self):
        """Start WebSocket server in separate thread"""
        
        async def run_ws_server():
            try:
                print("🔌 Starting WebSocket server on port 8765...")
                await websockets.serve(self.websocket_server, "localhost", 8765)
                print("🔌 WebSocket server ready")
                
                # Keep running
                while self.running:
                    await asyncio.sleep(1)
                    
            except Exception as e:
                print(f"🔌 WebSocket server error: {e}")
        
        def run_in_thread():
            asyncio.run(run_ws_server())
        
        ws_thread = threading.Thread(target=run_in_thread, daemon=True)
        ws_thread.start()
    
    def start_http_server(self):
        """Start simple HTTP server for web interface"""
        
        def run_http_server():
            try:
                import os
                os.chdir('/tmp')
                
                class CustomHandler(SimpleHTTPRequestHandler):
                    def log_message(self, format, *args):
                        pass  # Suppress HTTP server logs
                
                server = HTTPServer(('localhost', 8080), CustomHandler)
                print("🌐 HTTP server running at http://localhost:8080/rupert_vision.html")
                server.serve_forever()
                
            except Exception as e:
                print(f"🌐 HTTP server error: {e}")
        
        http_thread = threading.Thread(target=run_http_server, daemon=True)
        http_thread.start()
    
    async def provide_screen_api(self):
        """Provide screen data API for other Rupert components"""
        
        while self.running:
            try:
                # Check for screen data requests
                requests = self.r.xread({'rupert:screen_requests': '$'}, block=100)
                
                for stream, messages in requests:
                    for msg_id, fields in messages:
                        request_type = fields.get('request', 'current_screen')
                        
                        if request_type == 'current_screen':
                            screen_data = self.capture_and_encode_screen()
                            if screen_data:
                                self.r.xadd('rupert:screen_responses', {
                                    'request_id': msg_id,
                                    'image': screen_data['image'][:1000],  # Truncated for response
                                    'timestamp': str(screen_data['timestamp']),
                                    'mouse_pos': f"{screen_data['mouse_x']},{screen_data['mouse_y']}",
                                    'available': 'true'
                                })
                        
                        elif request_type == 'screen_analysis':
                            # Provide screen analysis for other Rupert components
                            screen_data = self.capture_and_encode_screen()
                            analysis = {
                                'has_terminal_colors': True,  # Simplified analysis
                                'dominant_regions': 'code_editor',
                                'mouse_active_area': 'center'
                            }
                            
                            self.r.xadd('rupert:screen_responses', {
                                'request_id': msg_id,
                                'analysis': json.dumps(analysis),
                                'timestamp': str(time.time())
                            })
                
            except Exception as e:
                if "timeout" not in str(e):
                    print(f"📹 API error: {e}")
                await asyncio.sleep(0.1)
    
    async def run_vision_server(self):
        """Run the complete vision server system"""
        
        print("👁️ RUPERT VISION SERVER ACTIVE")
        print("📹 Streaming screen to Redis...")
        print("🌐 Web interface available...")
        print("🔌 WebSocket server for real-time viewing...")
        
        # Create web interface
        self.create_web_interface()
        
        # Start HTTP and WebSocket servers
        self.start_http_server()
        self.start_websocket_server()
        
        # Run main streaming loop
        await asyncio.gather(
            self.stream_screen_to_redis(),
            self.provide_screen_api()
        )

async def main():
    try:
        import websockets
    except ImportError:
        print("Installing websockets...")
        import subprocess
        subprocess.run(['pip', 'install', 'websockets'], check=True)
        import websockets
    
    vision_server = RupertVisionServer()
    await vision_server.run_vision_server()

if __name__ == "__main__":
    asyncio.run(main())