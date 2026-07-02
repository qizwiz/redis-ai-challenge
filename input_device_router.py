#!/usr/bin/env python3
import redis
import json
import time
import subprocess
from typing import Dict, List

class InputDeviceRouter:
    def __init__(self):
        self.redis_client = redis.Redis(decode_responses=True)
        self.routing_table = {}
        self.active_routes = set()
        
    def create_input_route(self, device_id: str, target_process: str, 
                          input_type: str = 'all') -> Dict:
        """Create input routing rule"""
        route_id = f"route_{int(time.time())}"
        
        route_config = {
            'route_id': route_id,
            'device_id': device_id,
            'target_process': target_process,
            'input_type': input_type,
            'status': 'active',
            'created': int(time.time()),
            'packets_routed': 0
        }
        
        self.routing_table[route_id] = route_config
        self.active_routes.add(route_id)
        
        # Store in Redis
        self.redis_client.hset(f'input:routes:{route_id}', mapping=route_config)
        
        print(f"Created input route: {device_id} -> {target_process}")
        return route_config
    
    def route_mouse_input(self, device_id: str, x: int, y: int, 
                         button: str = None, target_process: str = None):
        """Route mouse input to target process"""
        if target_process:
            # Route to specific process using PID targeting
            self._send_mouse_to_process(target_process, x, y, button)
        else:
            # Use global mouse control
            self._send_global_mouse(x, y, button)
        
        # Log routing activity
        self.redis_client.xadd('input:mouse:activity', '*',
            'device_id', device_id,
            'x', x,
            'y', y,
            'button', button or 'move',
            'target', target_process or 'global',
            'timestamp', int(time.time())
        )
    
    def route_keyboard_input(self, device_id: str, keys: str, 
                           modifiers: List[str] = None, target_process: str = None):
        """Route keyboard input to target process"""
        if target_process:
            # Route to specific process
            self._send_keys_to_process(target_process, keys, modifiers or [])
        else:
            # Use global keyboard control
            self._send_global_keys(keys, modifiers or [])
        
        # Log routing activity
        self.redis_client.xadd('input:keyboard:activity', '*',
            'device_id', device_id,
            'keys', keys,
            'modifiers', ','.join(modifiers or []),
            'target', target_process or 'global',
            'timestamp', int(time.time())
        )
    
    def _send_mouse_to_process(self, target_process: str, x: int, y: int, button: str = None):
        """Send mouse input to specific process"""
        if button:
            script = f'''
            tell application "System Events"
                tell process "{target_process}"
                    click at {{{x}, {y}}}
                end tell
            end tell
            '''
        else:
            script = f'''
            tell application "System Events"
                tell process "{target_process}"
                    set position of mouse to {{{x}, {y}}}
                end tell
            end tell
            '''
        
        try:
            subprocess.run(['osascript', '-e', script], capture_output=True, check=True)
        except Exception as e:
            print(f"Mouse routing error: {e}")
    
    def _send_global_mouse(self, x: int, y: int, button: str = None):
        """Send mouse input globally"""
        try:
            if button:
                subprocess.run(['cliclick', 'c', f'{x},{y}'], check=True)
            else:
                subprocess.run(['cliclick', 'm', f'{x},{y}'], check=True)
        except Exception as e:
            print(f"Global mouse error: {e}")
    
    def _send_keys_to_process(self, target_process: str, keys: str, modifiers: List[str]):
        """Send keyboard input to specific process"""
        modifier_string = ' using {' + ', '.join(f'{mod} down' for mod in modifiers) + '}' if modifiers else ''
        
        script = f'''
        tell application "System Events"
            tell process "{target_process}"
                keystroke "{keys}"{modifier_string}
            end tell
        end tell
        '''
        
        try:
            subprocess.run(['osascript', '-e', script], capture_output=True, check=True)
        except Exception as e:
            print(f"Keyboard routing error: {e}")
    
    def _send_global_keys(self, keys: str, modifiers: List[str]):
        """Send keyboard input globally"""
        try:
            modifier_flags = []
            for mod in modifiers:
                if mod.lower() == 'cmd':
                    modifier_flags.append('cmd')
                elif mod.lower() in ['ctrl', 'control']:
                    modifier_flags.append('ctrl')
                elif mod.lower() in ['alt', 'option']:
                    modifier_flags.append('alt')
                elif mod.lower() == 'shift':
                    modifier_flags.append('shift')
            
            cmd = ['cliclick', 't', keys]
            if modifier_flags:
                cmd.extend(['-m', ','.join(modifier_flags)])
            
            subprocess.run(cmd, check=True)
        except Exception as e:
            print(f"Global keyboard error: {e}")
    
    def get_routing_stats(self) -> Dict:
        """Get input routing statistics"""
        stats = {
            'active_routes': len(self.active_routes),
            'total_routes': len(self.routing_table),
            'mouse_events': self.redis_client.xlen('input:mouse:activity'),
            'keyboard_events': self.redis_client.xlen('input:keyboard:activity'),
            'timestamp': int(time.time())
        }
        
        self.redis_client.hset('input:routing:stats', mapping=stats)
        return stats

if __name__ == "__main__":
    router = InputDeviceRouter()
    
    # Create example routes
    router.create_input_route('mouse_0', 'Claude Code', 'mouse')
    router.create_input_route('keyboard_0', 'Terminal', 'keyboard')
    
    stats = router.get_routing_stats()
    print(f"Input router initialized: {stats}")
