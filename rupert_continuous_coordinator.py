#!/usr/bin/env python3
"""
RUPERT CONTINUOUS COORDINATOR - Jonathan's mechanized development brain
Watches our development in real-time and suggests next concrete steps
Built using the async daemon architecture
"""

import asyncio
import time
import redis
import json
import subprocess
from pathlib import Path
from rupert import Rupert
import pyautogui
import psutil

class RupertContinuousCoordinator:
    """Continuous development coordinator using Rupert's Jonathan-patterns"""
    
    def __init__(self):
        self.r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        self.rupert = Rupert()
        self.running = True
        self.last_analysis = {}
        
        # Enable real developer control
        pyautogui.FAILSAFE = True  # Move mouse to corner to emergency stop
        pyautogui.PAUSE = 0.1  # Small delay between actions
        
        print("🧠 RUPERT CONTINUOUS COORDINATOR ONLINE")
        print("⚡ Watching development and suggesting next steps automatically")
        print("🖱️ Full mouse and keyboard control enabled")
        print("⌨️ Acting like a real developer")
    
    async def watch_development_activity(self):
        """Watch for development activity and analyze progress"""
        
        while self.running:
            try:
                # Check recent file changes
                recent_files = self.get_recent_file_changes()
                
                # Check Redis activity
                redis_activity = self.analyze_redis_activity()
                
                # Check daemon health
                daemon_status = self.r.hgetall("daemon:health") or {}
                
                # Analyze current state
                current_state = {
                    'files_changed': len(recent_files),
                    'redis_streams': len(self.r.keys("*:*")),
                    'daemon_healthy': daemon_status.get('daemon_status') == 'running',
                    'timestamp': time.time()
                }
                
                # If significant change, get Rupert's suggestion
                if self.state_changed_significantly(current_state):
                    suggestion = self.get_ruperts_next_step(current_state, recent_files)
                    
                    if suggestion:
                        # Send suggestion to Claude via Redis
                        self.r.xadd("rupert:suggestions", {
                            "suggestion": suggestion,
                            "context": json.dumps(current_state),
                            "files": json.dumps(recent_files[:3]),  # Top 3 recent files
                            "timestamp": str(time.time())
                        })
                        
                        print(f"🎯 RUPERT SUGGESTS: {suggestion}")
                
                self.last_analysis = current_state
                await asyncio.sleep(3)  # Check every 3 seconds
                
            except Exception as e:
                print(f"⚠️ Coordinator error: {e}")
                await asyncio.sleep(5)
    
    def get_recent_file_changes(self):
        """Get recently modified Python files"""
        try:
            result = subprocess.run([
                'find', '.', '-name', '*.py', '-mtime', '-0.1'  # Last ~2.4 hours
            ], capture_output=True, text=True, timeout=2)
            
            files = result.stdout.strip().split('\n') if result.stdout.strip() else []
            return [f for f in files if f and not f.startswith('./test_')]
            
        except:
            return []
    
    def analyze_redis_activity(self):
        """Analyze recent Redis activity"""
        try:
            # Count different types of streams
            command_streams = len(self.r.keys("*:commands"))
            response_streams = len(self.r.keys("*:responses"))
            data_streams = len(self.r.keys("*:*")) - command_streams - response_streams
            
            return {
                'command_streams': command_streams,
                'response_streams': response_streams,
                'data_streams': data_streams
            }
        except:
            return {}
    
    def state_changed_significantly(self, current_state):
        """Check if development state changed enough to warrant suggestion"""
        
        if not self.last_analysis:
            return True  # First run
            
        # Check for significant changes
        file_change = abs(current_state['files_changed'] - self.last_analysis.get('files_changed', 0)) > 0
        stream_change = abs(current_state['redis_streams'] - self.last_analysis.get('redis_streams', 0)) > 2
        daemon_status_change = current_state['daemon_healthy'] != self.last_analysis.get('daemon_healthy', False)
        
        return file_change or stream_change or daemon_status_change
    
    def get_ruperts_next_step(self, current_state, recent_files):
        """Get Rupert's suggestion for the next development step"""
        
        # Build context description
        context = f"Development state: {current_state['files_changed']} files changed, "
        context += f"{current_state['redis_streams']} Redis streams, "
        context += f"daemon {'healthy' if current_state['daemon_healthy'] else 'unhealthy'}"
        
        if recent_files:
            context += f". Recent files: {', '.join(recent_files[:2])}"
        
        # Get Rupert's thinking
        suggestions = self.rupert.think_like_jonathan(context)
        
        # Generate specific next step based on context
        if not current_state['daemon_healthy']:
            return "Fix the async daemon - it's the foundation for everything else"
        
        elif current_state['files_changed'] > 3:
            return "Test what you just built - run it and see what breaks"
            
        elif 'coordinator' in str(recent_files).lower():
            return "Connect the coordinator to the async daemon for real-time feedback"
            
        elif current_state['redis_streams'] < 5:
            return "Build more Redis coordination patterns - you need more streams"
            
        else:
            return "Use the tools you built to improve the tools themselves"
    
    def act_like_real_developer(self, action, **kwargs):
        """Execute real developer actions - typing, mouse, window control"""
        
        try:
            if action == "type_code":
                code = kwargs.get('code', '')
                print(f"⌨️ RUPERT TYPING: {code[:50]}...")
                pyautogui.typewrite(code, interval=0.05)  # Fast typing like real developer
                
            elif action == "click_at":
                x, y = kwargs.get('x', 100), kwargs.get('y', 100)
                print(f"🖱️ RUPERT CLICKING: ({x}, {y})")
                pyautogui.click(x, y)
                
            elif action == "switch_to_emacs":
                print("🪟 RUPERT SWITCHING TO EMACS")
                # Use Cmd+Tab on macOS to switch to Emacs
                pyautogui.hotkey('cmd', 'tab')
                time.sleep(0.3)
                # Or directly activate Emacs if we can find it
                subprocess.run(['osascript', '-e', 'tell application "Emacs" to activate'], 
                             capture_output=True, timeout=2)
                
            elif action == "open_terminal":
                print("💻 RUPERT OPENING TERMINAL")
                pyautogui.hotkey('cmd', 'space')  # Open Spotlight
                time.sleep(0.3)
                pyautogui.typewrite('terminal', interval=0.05)
                time.sleep(0.3)
                pyautogui.press('return')
                
            elif action == "run_command":
                command = kwargs.get('command', 'echo "Rupert here"')
                print(f"🏃 RUPERT RUNNING: {command}")
                pyautogui.typewrite(command, interval=0.03)
                pyautogui.press('return')
                
            elif action == "scroll_down":
                print("📜 RUPERT SCROLLING")
                pyautogui.scroll(-3)  # Scroll down
                
            elif action == "save_file":
                print("💾 RUPERT SAVING FILE")
                pyautogui.hotkey('cmd', 's')  # Cmd+S to save
                
            elif action == "copy_paste":
                print("📋 RUPERT COPY-PASTING")
                pyautogui.hotkey('cmd', 'a')  # Select all
                time.sleep(0.1)
                pyautogui.hotkey('cmd', 'c')  # Copy
                time.sleep(0.1)
                pyautogui.hotkey('cmd', 'v')  # Paste
                
            return True
            
        except Exception as e:
            print(f"⚠️ Rupert action failed: {e}")
            return False
    
    async def execute_development_actions(self):
        """Execute development actions after guardian approval"""
        
        while self.running:
            try:
                # Listen for APPROVED actions from guardian
                approved_actions = self.r.xread({'rupert:approved_actions': '$'}, block=100)
                
                for stream, messages in approved_actions:
                    for msg_id, fields in messages:
                        action = fields.get('action', 'type_code')
                        safety_score = float(fields.get('safety_score', '1.0'))
                        
                        print(f"✅ EXECUTING GUARDIAN-APPROVED ACTION: {action} (safety: {safety_score:.2f})")
                        
                        # Extract parameters
                        kwargs = {}
                        for key, value in fields.items():
                            if key not in ['action', 'guardian_approval', 'safety_score', 'original_request_id']:
                                kwargs[key] = value
                        
                        # Execute the guardian-approved action
                        success = self.act_like_real_developer(action, **kwargs)
                        
                        # Acknowledge action completion to guardian system
                        self.r.xadd("rupert:action_results", {
                            'request_id': msg_id,
                            'original_request': fields.get('original_request_id'),
                            'action': action,
                            'success': str(success),
                            'safety_score': str(safety_score),
                            'guardian_approved': 'true',
                            'timestamp': str(time.time())
                        })
                        
            except Exception as e:
                if "timeout" not in str(e):
                    print(f"⚠️ Action execution error: {e}")
                await asyncio.sleep(0.1)
    
    async def autonomous_development_session(self):
        """Run autonomous development session with guardian safety"""
        
        await asyncio.sleep(8)  # Wait for guardian to start
        
        print("🚀 RUPERT STARTING GUARDIAN-PROTECTED AUTONOMOUS SESSION")
        
        # Request guidance for autonomous development
        self.r.xadd('rupert:guidance_needed', {
            'situation': 'Starting autonomous development session',
            'timestamp': str(time.time())
        })
        
        # Safe demo sequence - will be reviewed by guardian
        development_sequence = [
            ("type_code", {"code": "# Rupert autonomous development with AI guardian protection\n"}),
            ("type_code", {"code": "print('Hello from safely supervised Rupert!')\n"}),
            ("run_command", {"command": "echo 'Guardian-approved autonomous action'"}),
            ("run_command", {"command": "python -c \"print('Rupert can code safely!')\""})
        ]
        
        for action, kwargs in development_sequence:
            if not self.running:
                break
                
            print(f"🎯 RUPERT REQUESTING GUARDIAN REVIEW: {action}")
            
            # Send action to guardian for review (not direct execution)
            self.r.xadd('rupert:actions', {
                'action': action,
                **kwargs,
                'source': 'autonomous_session',
                'timestamp': str(time.time())
            })
            
            await asyncio.sleep(3)  # Wait for guardian review and execution
        
        print("✅ RUPERT AUTONOMOUS SESSION COMPLETE - ALL ACTIONS GUARDIAN-REVIEWED")
    
    async def provide_real_time_guidance(self):
        """Provide continuous development guidance"""
        
        while self.running:
            try:
                # Check if Claude needs guidance
                guidance_requests = self.r.xread({'claude:guidance_requests': '$'}, block=100)
                
                for stream, messages in guidance_requests:
                    for msg_id, fields in messages:
                        question = fields.get('question', 'What should I do next?')
                        
                        # Get Rupert's immediate response
                        response = self.rupert.be_jonathans_voice(question)
                        
                        # Send response back
                        self.r.xadd("rupert:guidance_responses", {
                            'request_id': msg_id,
                            'response': response,
                            'timestamp': str(time.time())
                        })
                        
                        print(f"🗣️ RUPERT RESPONDS: {response}")
                        
            except Exception as e:
                if "timeout" not in str(e):
                    print(f"⚠️ Guidance error: {e}")
                await asyncio.sleep(0.1)
    
    async def run_continuous_coordination(self):
        """Run continuous development coordination with full developer control"""
        
        print("🚀 RUPERT CONTINUOUS COORDINATION ACTIVE")
        print("👁️ Watching development activity...")
        print("🎯 Providing real-time guidance...")
        print("⌨️ Ready for autonomous development actions...")
        print("🖱️ Full keyboard and mouse control enabled")
        
        # Run all coordination tasks concurrently
        await asyncio.gather(
            self.watch_development_activity(),
            self.provide_real_time_guidance(),
            self.execute_development_actions(),
            self.autonomous_development_session()  # Run demo session
        )

async def main():
    coordinator = RupertContinuousCoordinator()
    await coordinator.run_continuous_coordination()

if __name__ == "__main__":
    asyncio.run(main())