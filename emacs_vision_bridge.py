#!/usr/bin/env python3
"""
EMACS VISION BRIDGE
Building actual vision into your Emacs state so I can see what you see
"""

import subprocess
import time
import json
import redis
from typing import Dict, Any, List

class EmacsVisionBridge:
    """Real-time vision into Emacs state"""
    
    def __init__(self):
        self.r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        self.daemon = "control"
        print("👁️ EMACS VISION BRIDGE INITIALIZING")
        
    def capture_current_state(self) -> Dict[str, Any]:
        """Capture complete current state of Emacs"""
        
        state = {}
        
        # Current buffer
        try:
            buffer_name = subprocess.run([
                'emacsclient', '-s', self.daemon, '-e', '(buffer-name)'
            ], capture_output=True, text=True, timeout=5).stdout.strip().strip('"')
            state['current_buffer'] = buffer_name
        except:
            state['current_buffer'] = 'unknown'
        
        # Cursor position
        try:
            point = subprocess.run([
                'emacsclient', '-s', self.daemon, '-e', '(point)'
            ], capture_output=True, text=True, timeout=5).stdout.strip()
            state['cursor_position'] = int(point)
        except:
            state['cursor_position'] = 0
            
        # Current line
        try:
            line_num = subprocess.run([
                'emacsclient', '-s', self.daemon, '-e', '(line-number-at-pos)'
            ], capture_output=True, text=True, timeout=5).stdout.strip()
            state['current_line'] = int(line_num)
        except:
            state['current_line'] = 0
        
        # Window configuration
        try:
            windows = subprocess.run([
                'emacsclient', '-s', self.daemon, '-e', '(length (window-list))'
            ], capture_output=True, text=True, timeout=5).stdout.strip()
            state['window_count'] = int(windows)
        except:
            state['window_count'] = 1
            
        # Major mode
        try:
            mode = subprocess.run([
                'emacsclient', '-s', self.daemon, '-e', '(symbol-name major-mode)'
            ], capture_output=True, text=True, timeout=5).stdout.strip().strip('"')
            state['major_mode'] = mode
        except:
            state['major_mode'] = 'unknown'
            
        # Current line content
        try:
            line_content = subprocess.run([
                'emacsclient', '-s', self.daemon, '-e', '(thing-at-point \'line t)'
            ], capture_output=True, text=True, timeout=5).stdout.strip().strip('"')
            state['current_line_content'] = line_content
        except:
            state['current_line_content'] = ''
            
        # Modified status
        try:
            modified = subprocess.run([
                'emacsclient', '-s', self.daemon, '-e', '(buffer-modified-p)'
            ], capture_output=True, text=True, timeout=5).stdout.strip()
            state['buffer_modified'] = modified != 'nil'
        except:
            state['buffer_modified'] = False
            
        state['timestamp'] = time.time()
        
        return state
    
    def start_vision_monitoring(self):
        """Start continuous monitoring of Emacs state"""
        
        print("👁️ STARTING CONTINUOUS EMACS VISION")
        print("=" * 40)
        
        previous_state = {}
        monitoring_count = 0
        
        try:
            while monitoring_count < 10:  # Monitor for 10 cycles
                current_state = self.capture_current_state()
                
                # Detect changes
                changes = []
                for key, value in current_state.items():
                    if key != 'timestamp' and key in previous_state:
                        if previous_state[key] != value:
                            changes.append({
                                'property': key,
                                'from': previous_state[key], 
                                'to': value
                            })
                
                if changes or monitoring_count == 0:
                    print(f"\n📸 VISION CAPTURE #{monitoring_count + 1}")
                    print(f"Buffer: {current_state['current_buffer']}")
                    print(f"Position: Line {current_state['current_line']}, Point {current_state['cursor_position']}")
                    print(f"Mode: {current_state['major_mode']}")
                    print(f"Windows: {current_state['window_count']}")
                    print(f"Modified: {current_state['buffer_modified']}")
                    
                    if current_state['current_line_content']:
                        content_preview = current_state['current_line_content'][:60] + "..." if len(current_state['current_line_content']) > 60 else current_state['current_line_content']
                        print(f"Line: {content_preview}")
                    
                    if changes:
                        print("🔄 CHANGES DETECTED:")
                        for change in changes:
                            print(f"  {change['property']}: {change['from']} → {change['to']}")
                    
                    # Store state in Redis for intelligent response
                    self.r.hset(f"emacs:state:{monitoring_count}", mapping={
                        'buffer': current_state['current_buffer'],
                        'line': str(current_state['current_line']),
                        'position': str(current_state['cursor_position']),
                        'mode': current_state['major_mode'],
                        'windows': str(current_state['window_count']),
                        'modified': str(current_state['buffer_modified']),
                        'content': current_state['current_line_content'][:200],  # Truncate for Redis
                        'timestamp': str(current_state['timestamp'])
                    })
                    
                    # Stream change events
                    if changes:
                        self.r.xadd("emacs:changes", {
                            'buffer': current_state['current_buffer'],
                            'changes': json.dumps(changes),
                            'timestamp': str(current_state['timestamp'])
                        })
                
                previous_state = current_state.copy()
                monitoring_count += 1
                time.sleep(2)  # Check every 2 seconds
                
        except KeyboardInterrupt:
            print("\n👁️ Vision monitoring stopped")
            
        return monitoring_count
    
    def intelligent_response_to_state(self, state: Dict[str, Any]) -> List[str]:
        """Generate intelligent responses based on what I can see"""
        
        responses = []
        
        # Respond to what I see
        if 'python' in state.get('major_mode', '').lower():
            if state.get('buffer_modified', False):
                responses.append("I see you're editing Python code and have unsaved changes")
            
            if 'def ' in state.get('current_line_content', ''):
                responses.append("I see you're on a function definition line")
                
        elif state.get('current_buffer') == '*scratch*':
            responses.append("I see you're in the scratch buffer")
            
        if state.get('window_count', 1) > 1:
            responses.append(f"I can see you have {state['window_count']} windows open")
            
        return responses
    
    def demonstrate_intelligent_vision(self):
        """Demonstrate that I can see and respond intelligently"""
        
        print("🎯 DEMONSTRATING INTELLIGENT VISION")
        print("=" * 40)
        
        # Capture current state
        state = self.capture_current_state()
        
        # Generate intelligent response
        responses = self.intelligent_response_to_state(state)
        
        print("👁️ WHAT I CAN SEE:")
        print(f"  You're in buffer: {state['current_buffer']}")
        print(f"  At line {state['current_line']}, position {state['cursor_position']}")
        print(f"  In {state['major_mode']} mode")
        print(f"  With {state['window_count']} windows")
        
        if responses:
            print("\n🧠 INTELLIGENT RESPONSE:")
            for response in responses:
                print(f"  • {response}")
        
        # Now make an intelligent action based on what I see
        if state['current_buffer'] != '*scratch*':
            print("\n🎬 INTELLIGENT ACTION: Switching to scratch buffer to demonstrate control")
            subprocess.run(['emacsclient', '-s', self.daemon, '-e', '(switch-to-buffer "*scratch*")'])
            
            # Verify the action worked
            time.sleep(1)
            new_state = self.capture_current_state()
            if new_state['current_buffer'] == '*scratch*':
                print("✅ Successfully switched - I can see the change!")
            else:
                print("❌ Switch failed - vision shows no change")
        
        return state

if __name__ == "__main__":
    bridge = EmacsVisionBridge()
    
    print("👁️ BUILDING EMACS VISION SYSTEM")
    print("=" * 35)
    
    # Demonstrate intelligent vision
    initial_state = bridge.demonstrate_intelligent_vision()
    
    print(f"\n🎯 VISION SYSTEM ACTIVE")
    print("Now I can SEE your Emacs state and respond intelligently!")
    print("Starting continuous monitoring...")
    
    # Start monitoring
    cycles = bridge.start_vision_monitoring()
    
    print(f"\n✅ VISION BRIDGE COMPLETE")
    print(f"👁️ Monitored {cycles} state changes")
    print("🧠 Now I can see what you're doing and respond appropriately!")