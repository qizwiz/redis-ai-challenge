#!/usr/bin/env python3
"""
macOS Facade - Complete system vision through Redis
Like EmacsFacade, but for entire Mac
"""

import redis
import json
import time
import subprocess
from typing import Dict, Any, List

class MacOSFacade:
    """Complete vision of macOS state through Redis"""

    def __init__(self):
        self.redis = redis.Redis(host='localhost', port=6379, decode_responses=True)
        self.facade_key = "macos:facade"

    def get_current_state(self) -> Dict[str, Any]:
        """Get complete macOS state"""
        try:
            state_json = self.redis.get(self.facade_key)
            if state_json:
                return json.loads(state_json)
            return self._capture_state()
        except Exception as e:
            print(f"Error: {e}")
            return self._capture_state()

    def _capture_state(self) -> Dict[str, Any]:
        """Capture current macOS state"""
        state = {
            'timestamp': time.time(),
            'windows': self._get_window_state(),
            'applications': self._get_app_state(),
            'screen': self._get_screen_state(),
            'input': self._get_input_state(),
            'system': self._get_system_state()
        }

        # Store in Redis
        self.redis.set(self.facade_key, json.dumps(state))
        self.redis.publish('macos:state_changes', json.dumps(state))

        return state

    def _get_window_state(self) -> Dict[str, Any]:
        """Get window information"""
        try:
            # Use osascript to get window info
            script = '''
            tell application "System Events"
                set frontApp to name of first application process whose frontmost is true
                tell process frontApp
                    set windowCount to count of windows
                    if windowCount > 0 then
                        set frontWindow to window 1
                        set windowTitle to name of frontWindow
                        set windowPos to position of frontWindow
                        set windowSize to size of frontWindow
                        return {frontApp, windowTitle, item 1 of windowPos, item 2 of windowPos, item 1 of windowSize, item 2 of windowSize}
                    else
                        return {frontApp, "no windows", 0, 0, 0, 0}
                    end if
                end tell
            end tell
            '''

            result = subprocess.run(['osascript', '-e', script],
                                  capture_output=True, text=True, timeout=2)

            if result.returncode == 0:
                parts = result.stdout.strip().split(', ')
                if len(parts) >= 6:
                    return {
                        'frontmost_app': parts[0],
                        'frontmost_window': parts[1],
                        'position': {'x': parts[2], 'y': parts[3]},
                        'size': {'width': parts[4], 'height': parts[5]}
                    }

            return {'frontmost_app': 'unknown', 'error': result.stderr}
        except Exception as e:
            return {'error': str(e)}

    def _get_app_state(self) -> Dict[str, Any]:
        """Get running applications"""
        try:
            result = subprocess.run(
                ['osascript', '-e', 'tell application "System Events" to get name of every process whose background only is false'],
                capture_output=True, text=True, timeout=2
            )

            if result.returncode == 0:
                apps = [app.strip() for app in result.stdout.split(',')]
                return {
                    'running': apps,
                    'count': len(apps)
                }

            return {'running': [], 'count': 0}
        except:
            return {'running': [], 'count': 0}

    def _get_screen_state(self) -> Dict[str, Any]:
        """Get screen dimensions"""
        try:
            result = subprocess.run(
                ['osascript', '-e', 'tell application "Finder" to get bounds of window of desktop'],
                capture_output=True, text=True, timeout=2
            )

            if result.returncode == 0:
                bounds = result.stdout.strip().split(', ')
                return {
                    'width': int(bounds[2]),
                    'height': int(bounds[3]),
                    'bounds': bounds
                }

            return {'width': 0, 'height': 0}
        except:
            return {'width': 0, 'height': 0}

    def _get_input_state(self) -> Dict[str, Any]:
        """Get input device state"""
        # Mouse position via cliclick or similar
        return {
            'mouse': {'x': 0, 'y': 0},
            'keyboard': {'modifiers': []}
        }

    def _get_system_state(self) -> Dict[str, Any]:
        """Get system information"""
        return {
            'hostname': subprocess.run(['hostname'], capture_output=True, text=True).stdout.strip(),
            'uptime': subprocess.run(['uptime'], capture_output=True, text=True).stdout.strip(),
            'user': subprocess.run(['whoami'], capture_output=True, text=True).stdout.strip()
        }

    def watch_frontmost_app(self, callback=None):
        """Watch for frontmost app changes"""
        last_app = None

        while True:
            state = self._capture_state()
            current_app = state['windows'].get('frontmost_app')

            if current_app != last_app:
                print(f"🔄 Frontmost app changed: {last_app} → {current_app}")

                if callback:
                    callback(current_app, state)

                # Log to Redis
                self.redis.xadd('macos:app_changes', {
                    'from': last_app or 'none',
                    'to': current_app,
                    'timestamp': time.time()
                })

                last_app = current_app

            time.sleep(0.5)

    def format_state_summary(self) -> str:
        """Human-readable state summary"""
        state = self.get_current_state()

        summary = f"""
🖥️  **macOS FACADE STATE**
┌─ Frontmost App: {state['windows'].get('frontmost_app', 'unknown')}
├─ Window: {state['windows'].get('frontmost_window', 'unknown')}
├─ Position: {state['windows'].get('position', {})}
├─ Running Apps: {state['applications'].get('count', 0)}
├─ Screen: {state['screen'].get('width', 0)}x{state['screen'].get('height', 0)}
└─ User: {state['system'].get('user', 'unknown')}@{state['system'].get('hostname', 'unknown')}
"""
        return summary.strip()

def demonstrate_macos_facade():
    """Demonstrate macOS facade"""
    print("🖥️  macOS Facade Demo")
    print("=" * 60)

    facade = MacOSFacade()

    # Capture current state
    print("\n📸 Capturing macOS state...")
    state = facade._capture_state()

    # Display summary
    print("\n" + facade.format_state_summary())

    # Show what's in Redis
    print("\n📊 State stored in Redis:")
    print(f"   Key: {facade.facade_key}")
    print(f"   Size: {len(json.dumps(state))} bytes")

    print("\n✅ macOS facade active!")
    print("   - Complete system vision through Redis")
    print("   - Window positions tracked")
    print("   - App switches logged")
    print("   - All queryable")

if __name__ == '__main__':
    demonstrate_macos_facade()
