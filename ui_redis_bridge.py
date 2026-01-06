#!/usr/bin/env python3
"""
UI-Redis Bridge: Complete macOS UI representation in Redis
Every interactable element becomes Redis-controllable
"""

import subprocess
import json
import redis
import time

class UIRedisElements:
    def __init__(self):
        self.redis = redis.Redis(decode_responses=True)
        self.elements_key = "ui:elements"
        self.actions_stream = "ui:actions"
        
    def discover_ui_elements(self, process_name):
        """Discover all UI elements for a process"""
        script = f'''
        tell application "System Events"
            tell process "{process_name}"
                set allElements to entire contents
                return allElements
            end tell
        end tell
        '''
        
        try:
            result = subprocess.run(['osascript', '-e', script], 
                                  capture_output=True, text=True, timeout=10)
            return result.stdout.strip() if result.returncode == 0 else None
        except:
            return None
    
    def get_clickable_elements(self, process_name):
        """Get all clickable elements with their Redis commands"""
        script = f'''
        tell application "System Events"
            tell process "{process_name}"
                set clickableElements to {{}}
                set buttonList to every button
                repeat with btn in buttonList
                    try
                        set btnInfo to {{class of btn, position of btn, size of btn, role of btn, subrole of btn, title of btn}}
                        set end of clickableElements to btnInfo
                    end try
                end repeat
                return clickableElements
            end tell
        end tell
        '''
        
        try:
            result = subprocess.run(['osascript', '-e', script],
                                  capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                elements = []
                raw_output = result.stdout.strip()
                
                # Parse and create Redis commands for each element
                element_id = 0
                for line in raw_output.split('\n'):
                    if line.strip():
                        element_id += 1
                        redis_cmd = f"ui:click:{process_name}:{element_id}"
                        
                        elements.append({
                            'id': element_id,
                            'process': process_name,
                            'redis_command': redis_cmd,
                            'raw': line.strip(),
                            'type': 'button'
                        })
                
                return elements
        except Exception as e:
            return []
    
    def register_ui_element(self, element_info):
        """Register UI element in Redis for control"""
        element_key = f"{self.elements_key}:{element_info['process']}:{element_info['id']}"
        
        # Store element info
        self.redis.hset(element_key, mapping={
            'process': element_info['process'],
            'type': element_info['type'],
            'redis_command': element_info['redis_command'],
            'raw_info': element_info['raw'],
            'timestamp': str(time.time())
        })
        
        # Add to searchable index
        self.redis.sadd(f"{self.elements_key}:index", element_key)
        
        return element_key
    
    def execute_redis_ui_command(self, redis_command):
        """Execute UI action from Redis command"""
        # Parse: ui:click:iTerm2:5
        parts = redis_command.split(':')
        if len(parts) >= 4:
            action = parts[1]  # click
            process = parts[2]  # iTerm2
            element_id = parts[3]  # 5
            
            if action == 'click':
                return self.click_element_by_id(process, int(element_id))
        
        return False, "Invalid command format"
    
    def click_element_by_id(self, process_name, element_id):
        """Click element by its registered ID"""
        # Get element info from Redis
        element_key = f"{self.elements_key}:{process_name}:{element_id}"
        element_info = self.redis.hgetall(element_key)
        
        if not element_info:
            return False, f"Element {element_id} not found for {process_name}"
        
        # Execute click via AppleScript
        script = f'''
        tell application "System Events"
            tell process "{process_name}"
                set buttonList to every button
                if (count of buttonList) >= {element_id} then
                    click button {element_id}
                    return "clicked"
                else
                    return "button not found"
                end if
            end tell
        end tell
        '''
        
        try:
            result = subprocess.run(['osascript', '-e', script],
                                  capture_output=True, text=True)
            
            # Log action to Redis
            self.redis.xadd(self.actions_stream, {
                'action': 'click',
                'process': process_name,
                'element_id': element_id,
                'success': result.returncode == 0,
                'output': result.stdout.strip(),
                'timestamp': time.time()
            })
            
            return result.returncode == 0, result.stdout.strip()
        except Exception as e:
            return False, str(e)
    
    def map_entire_desktop(self):
        """Map every UI element on desktop to Redis"""
        print("🗺️  Mapping entire desktop to Redis...")
        
        # Get all GUI processes
        processes_result = subprocess.run([
            'osascript', '-e',
            'tell application "System Events" to get name of every process whose background only is false'
        ], capture_output=True, text=True)
        
        if processes_result.returncode == 0:
            processes = [p.strip() for p in processes_result.stdout.split(',')]
            
            total_elements = 0
            for process in processes[:5]:  # Limit to first 5 for testing
                print(f"🔍 Mapping {process}...")
                
                elements = self.get_clickable_elements(process)
                for element in elements:
                    key = self.register_ui_element(element)
                    total_elements += 1
                    print(f"   Registered: {element['redis_command']}")
            
            print(f"✅ Mapped {total_elements} UI elements to Redis")
            return total_elements
        
        return 0

class OSScriptRedisBridge:
    def __init__(self):
        self.redis = redis.Redis(decode_responses=True)
        self.command_stream = "osascript:commands"
        self.result_stream = "osascript:results"
    
    def execute_from_redis(self, command_id):
        """Execute osascript command stored in Redis"""
        command_key = f"osascript:cmd:{command_id}"
        script = self.redis.get(command_key)
        
        if script:
            result = subprocess.run(['osascript', '-e', script],
                                  capture_output=True, text=True)
            
            # Store result
            self.redis.xadd(self.result_stream, {
                'command_id': command_id,
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'timestamp': time.time()
            })
            
            return result.returncode == 0, result.stdout, result.stderr
        
        return False, "", "Command not found"
    
    def store_command(self, script, description=""):
        """Store osascript command in Redis"""
        command_id = str(int(time.time() * 1000))  # timestamp as ID
        command_key = f"osascript:cmd:{command_id}"
        
        self.redis.set(command_key, script)
        self.redis.hset(f"osascript:meta:{command_id}", mapping={
            'description': description,
            'created': time.time(),
            'executed': 'false'
        })
        
        return command_id

if __name__ == '__main__':
    print("🌉 UI-Redis Bridge Initializing...")
    
    # Initialize bridge components
    ui_bridge = UIRedisElements()
    script_bridge = OSScriptRedisBridge()
    
    # Map current desktop to Redis
    element_count = ui_bridge.map_entire_desktop()
    
    # Test storing and executing commands
    print(f"\n🧪 Testing command bridge...")
    cmd_id = script_bridge.store_command(
        'tell application "System Events" to get name of first process whose frontmost is true',
        'Get frontmost process'
    )
    
    success, stdout, stderr = script_bridge.execute_from_redis(cmd_id)
    print(f"   Command result: {stdout.strip() if success else 'Failed'}")
    
    print(f"\n✅ Bridge initialized with {element_count} UI elements")
    print(f"   UI elements: redis-cli SMEMBERS ui:elements:index")
    print(f"   Actions log: redis-cli XREAD STREAMS ui:actions 0")
    print(f"   Commands: redis-cli XREAD STREAMS osascript:results 0")