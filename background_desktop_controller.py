#!/usr/bin/env python3
"""
Background Desktop Controller - Full visibility and control without activation
"""

import subprocess
import json
import time
import redis

class BackgroundDesktopController:
    def __init__(self):
        self.redis = redis.Redis(decode_responses=True)
        self.state_key = "facade:background:state"
        
    def get_all_app_windows(self):
        """Get all app windows without activating them"""
        apps = ["iTerm2", "Emacs", "Safari", "Arc", "Messages", "Finder", "Claude"]
        window_state = {}
        
        for app in apps:
            try:
                # Get window count without activation
                result = subprocess.run([
                    'osascript', '-e',
                    f'tell application "{app}" to return count of windows'
                ], capture_output=True, text=True, timeout=2)
                
                if result.returncode == 0:
                    count = int(result.stdout.strip())
                    window_state[app] = {'count': count, 'windows': []}
                    
                    # Get bounds of each window
                    for i in range(1, count + 1):
                        bounds_result = subprocess.run([
                            'osascript', '-e',
                            f'tell application "{app}" to return bounds of window {i}'
                        ], capture_output=True, text=True, timeout=2)
                        
                        if bounds_result.returncode == 0:
                            bounds = bounds_result.stdout.strip()
                            window_state[app]['windows'].append({
                                'index': i,
                                'bounds': bounds
                            })
                else:
                    window_state[app] = {'error': result.stderr.strip()}
                    
            except Exception as e:
                window_state[app] = {'error': str(e)}
        
        return window_state
    
    def get_system_state(self):
        """Get complete system state without changing focus"""
        try:
            # Current frontmost
            frontmost_result = subprocess.run([
                'osascript', '-e',
                'tell application "System Events" to get name of first process whose frontmost is true'
            ], capture_output=True, text=True)
            
            frontmost = frontmost_result.stdout.strip() if frontmost_result.returncode == 0 else "unknown"
            
            # Mouse position
            mouse_result = subprocess.run(['cliclick', 'p'], capture_output=True, text=True)
            mouse_pos = mouse_result.stdout.strip() if mouse_result.returncode == 0 else "unknown"
            
            return {
                'frontmost': frontmost,
                'mouse': mouse_pos,
                'timestamp': time.time()
            }
        except Exception as e:
            return {'error': str(e)}
    
    def position_window_background(self, app_name, window_index, bounds):
        """Position window without bringing app to front"""
        try:
            result = subprocess.run([
                'osascript', '-e',
                f'tell application "{app_name}" to set bounds of window {window_index} to {bounds}'
            ], capture_output=True, text=True)
            
            return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
        except Exception as e:
            return False, "", str(e)
    
    def create_side_by_side_background(self, left_app, right_app):
        """Create side-by-side layout without changing focus"""
        left_bounds = "{0, 0, 720, 900}"
        right_bounds = "{720, 0, 1440, 900}"
        
        left_success, left_out, left_err = self.position_window_background(left_app, 1, left_bounds)
        right_success, right_out, right_err = self.position_window_background(right_app, 1, right_bounds)
        
        result = {
            'action': 'background_side_by_side',
            'left_app': left_app,
            'right_app': right_app,
            'left_success': left_success,
            'right_success': right_success,
            'timestamp': time.time()
        }
        
        # Store in Redis
        self.redis.xadd("facade:background:control", result)
        
        return left_success and right_success
    
    def monitor_desktop(self, duration=10):
        """Monitor all desktop activity in background"""
        print(f"🖥️  Monitoring desktop for {duration} seconds...")
        start_time = time.time()
        
        while time.time() - start_time < duration:
            # Get complete state
            window_state = self.get_all_app_windows()
            system_state = self.get_system_state()
            
            # Combine and store
            full_state = {
                'timestamp': time.time(),
                'windows': window_state,
                'system': system_state
            }
            
            self.redis.set(self.state_key, json.dumps(full_state))
            
            print(f"📊 Frontmost: {system_state.get('frontmost', 'unknown')}")
            time.sleep(1)
        
        print("✅ Background monitoring complete")

if __name__ == '__main__':
    controller = BackgroundDesktopController()
    
    print("🎮 Background Desktop Controller")
    print("=" * 40)
    
    # Test background monitoring
    controller.monitor_desktop(5)
    
    # Test background side-by-side
    print("\n🔧 Testing background side-by-side...")
    success = controller.create_side_by_side_background("Safari", "Messages")
    print(f"Background positioning: {'✅ Success' if success else '❌ Failed'}")