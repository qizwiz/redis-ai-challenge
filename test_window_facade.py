#!/usr/bin/env python3
"""
Test window facade with osascript access working
"""

import subprocess
import json
import time

def redis_cmd(cmd):
    """Execute redis command"""
    result = subprocess.run(['redis-cli'] + cmd.split(), 
                          capture_output=True, text=True)
    return result.stdout.strip()

def get_frontmost_window():
    """Get frontmost window info"""
    script = """
    tell application "System Events"
        set frontApp to first process whose frontmost is true
        tell frontApp
            if (count of windows) > 0 then
                set frontWindow to window 1
                return {name of frontApp, name of frontWindow, position of frontWindow, size of frontWindow}
            else
                return {name of frontApp, "no windows", {0, 0}, {0, 0}}
            end if
        end tell
    end tell
    """
    
    result = subprocess.run(['osascript', '-e', script], 
                          capture_output=True, text=True)
    
    if result.returncode == 0:
        parts = result.stdout.strip().split(', ')
        if len(parts) >= 6:
            return {
                'app': parts[0],
                'title': parts[1], 
                'x': int(parts[2]),
                'y': int(parts[3]),
                'width': int(parts[4]), 
                'height': int(parts[5])
            }
    
    return {'error': result.stderr}

def get_all_windows():
    """Get all visible windows"""
    script = """
    tell application "System Events"
        set allWindows to {}
        repeat with proc in (every process whose background only is false)
            set procName to name of proc
            tell proc
                repeat with w in windows
                    try
                        set end of allWindows to {procName, name of w, position of w, size of w}
                    end try
                end repeat
            end tell
        end repeat
        return allWindows
    end tell
    """
    
    result = subprocess.run(['osascript', '-e', script], 
                          capture_output=True, text=True)
    return result.stdout.strip()

def test_complete_window_facade():
    """Test complete window facade"""
    print("🖥️  Testing Complete Window Facade")
    print("=" * 50)
    
    # Test frontmost window
    frontmost = get_frontmost_window()
    print(f"📱 Frontmost: {frontmost['app']}")
    print(f"   Window: {frontmost.get('title', 'N/A')}")
    print(f"   Position: ({frontmost.get('x', 0)}, {frontmost.get('y', 0)})")
    print(f"   Size: {frontmost.get('width', 0)}x{frontmost.get('height', 0)}")
    
    # Create facade state
    facade_state = {
        'timestamp': str(int(time.time())),
        'window_access': True,
        'frontmost_window': frontmost,
        'screen_coverage': {
            'total_pixels': 1440 * 900,  # From previous facade
            'frontmost_pixels': frontmost.get('width', 0) * frontmost.get('height', 0),
            'coverage_percent': round((frontmost.get('width', 0) * frontmost.get('height', 0)) / (1440 * 900) * 100, 1)
        }
    }
    
    # Store in Redis
    json_str = json.dumps(facade_state)
    redis_cmd(f'SET window:facade:current "{json_str}"')
    redis_cmd(f'XADD window:facade:stream * ts {facade_state["timestamp"]} state "{json_str}"')
    
    print(f"\n💾 Stored in Redis:")
    print(f"   Key: window:facade:current") 
    print(f"   Stream: window:facade:stream")
    print(f"   Coverage: {facade_state['screen_coverage']['coverage_percent']}% of screen")
    
    return facade_state

if __name__ == '__main__':
    test_complete_window_facade()