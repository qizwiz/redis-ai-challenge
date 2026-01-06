#!/usr/bin/env python3
"""
ASYNC EMACS DAEMON - The persistent background process
Runs continuously, watches Emacs, responds to Redis commands
While Claude talks to you in the foreground
"""

import asyncio
import subprocess
import time
import redis
import json
import signal
import sys

class AsyncEmacsDaemon:
    """Persistent background process controlling Emacs"""
    
    def __init__(self):
        self.r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        self.emacs_daemon = "work"
        self.running = True
        self.last_state = {}
        print("🔄 ASYNC EMACS DAEMON STARTING")
        print("🎯 Persistent background process for real-time Emacs control")
    
    def emacs_cmd(self, elisp: str) -> str:
        """Quick Emacs command"""
        try:
            result = subprocess.run([
                'emacsclient', '-s', self.emacs_daemon, '-e', elisp
            ], capture_output=True, text=True, timeout=1)
            return result.stdout.strip() if result.returncode == 0 else "error"
        except:
            return "timeout"
    
    async def monitor_emacs_continuously(self):
        """Continuously monitor Emacs state"""
        
        while self.running:
            try:
                # Get current state
                buffer = self.emacs_cmd('(buffer-name)').strip('"')
                point = self.emacs_cmd('(point)')
                line = self.emacs_cmd('(line-number-at-pos)')
                
                current_state = {
                    'buffer': buffer,
                    'point': int(point) if point.isdigit() else 0,
                    'line': int(line) if line.isdigit() else 0,
                    'timestamp': time.time()
                }
                
                # Detect changes
                if self.last_state and current_state != self.last_state:
                    # Stream the change
                    self.r.xadd("emacs:live_state", current_state)
                    print(f"📊 State change: {buffer} line {line}")
                
                self.last_state = current_state
                
                await asyncio.sleep(0.2)  # Check 5 times per second
                
            except Exception as e:
                print(f"⚠️ Monitor error: {e}")
                await asyncio.sleep(1)
    
    async def process_commands(self):
        """Process commands from Redis streams"""
        
        while self.running:
            try:
                # Check for commands from Claude
                commands = self.r.xread({'claude:commands': '$'}, block=100)
                
                for stream, messages in commands:
                    for msg_id, fields in messages:
                        command = fields.get('command', '')
                        
                        if command == 'switch_buffer':
                            buffer_name = fields.get('buffer', '*scratch*')
                            result = self.emacs_cmd(f'(switch-to-buffer "{buffer_name}")')
                            print(f"🔄 Switched to {buffer_name}: {result}")
                            
                        elif command == 'insert_text':
                            text = fields.get('text', '')
                            result = self.emacs_cmd(f'(insert "{text}")')
                            print(f"✏️ Inserted text: {result}")
                            
                        elif command == 'goto_line':
                            line_num = fields.get('line', '1')
                            result = self.emacs_cmd(f'(goto-line {line_num})')
                            print(f"🎯 Went to line {line_num}: {result}")
                            
                        elif command == 'eval_elisp':
                            elisp = fields.get('elisp', '(message "hello")')
                            result = self.emacs_cmd(elisp)
                            print(f"🧠 Eval result: {result}")
                        
                        # Acknowledge command processed
                        self.r.xadd("emacs:responses", {
                            'command_id': msg_id,
                            'result': result if 'result' in locals() else 'processed',
                            'timestamp': str(time.time())
                        })
                        
            except Exception as e:
                if "timeout" not in str(e):
                    print(f"⚠️ Command error: {e}")
                await asyncio.sleep(0.1)
    
    async def health_reporter(self):
        """Report daemon health periodically"""
        
        while self.running:
            try:
                health = {
                    'daemon_status': 'running',
                    'emacs_connection': 'ok' if self.emacs_cmd('(+ 1 1)') == '2' else 'error',
                    'redis_connection': 'ok' if self.r.ping() else 'error',
                    'uptime': time.time(),
                    'last_state': json.dumps(self.last_state)
                }
                
                self.r.hset("daemon:health", mapping=health)
                await asyncio.sleep(5)  # Report every 5 seconds
                
            except Exception as e:
                print(f"⚠️ Health error: {e}")
                await asyncio.sleep(5)
    
    async def run_daemon(self):
        """Run all daemon tasks concurrently"""
        
        print("🚀 ASYNC DAEMON RUNNING")
        print("🔄 Monitoring Emacs continuously")
        print("📨 Listening for Redis commands")
        print("❤️ Reporting health status")
        
        # Run all tasks concurrently
        await asyncio.gather(
            self.monitor_emacs_continuously(),
            self.process_commands(), 
            self.health_reporter()
        )
    
    def signal_handler(self, signum, frame):
        """Handle shutdown gracefully"""
        print("\n🛑 DAEMON SHUTTING DOWN")
        self.running = False
        self.r.hset("daemon:health", "daemon_status", "stopped")
        sys.exit(0)

async def main():
    daemon = AsyncEmacsDaemon()
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, daemon.signal_handler)
    signal.signal(signal.SIGTERM, daemon.signal_handler)
    
    # Run the daemon
    await daemon.run_daemon()

if __name__ == "__main__":
    asyncio.run(main())