#!/usr/bin/env python3
"""
Position Claude and Emacs side-by-side using working window access
"""

import subprocess
import json
import time

def osascript(script):
    """Execute AppleScript and return result"""
    result = subprocess.run(['osascript', '-e', script], 
                          capture_output=True, text=True)
    return result.stdout.strip(), result.stderr.strip()

def get_app_window(app_name):
    """Get window info for specific app"""
    script = f'''
    tell application "System Events"
        try
            set targetProc to first process whose name is "{app_name}"
            tell targetProc
                if (count of windows) > 0 then
                    set frontWindow to window 1
                    return {{name of frontWindow, position of frontWindow, size of frontWindow}}
                else
                    return {{"no windows", {{0, 0}}, {{0, 0}}}}
                end if
            end tell
        on error
            return {{"not found", {{0, 0}}, {{0, 0}}}}
        end try
    end tell
    '''
    
    stdout, stderr = osascript(script)
    if stderr or "error" in stdout.lower():
        return None
        
    # Parse the result: {title, {x, y}, {w, h}}
    parts = stdout.split(', ')
    if len(parts) >= 6:
        return {
            'title': parts[0],
            'x': int(parts[1]),
            'y': int(parts[2]), 
            'width': int(parts[3]),
            'height': int(parts[4])
        }
    return None

def position_window(app_name, x, y, width=None, height=None):
    """Position a window"""
    if width and height:
        script = f'''
        tell application "System Events"
            tell process "{app_name}"
                if (count of windows) > 0 then
                    set position of window 1 to {{{x}, {y}}}
                    set size of window 1 to {{{width}, {height}}}
                end if
            end tell
        end tell
        '''
    else:
        script = f'''
        tell application "System Events"
            tell process "{app_name}"
                if (count of windows) > 0 then
                    set position of window 1 to {{{x}, {y}}}
                end if
            end tell
        end tell
        '''
    
    stdout, stderr = osascript(script)
    return not stderr

def arrange_side_by_side():
    """Arrange Claude and Emacs side-by-side"""
    print("📐 Arranging windows side-by-side...")
    
    # Screen: 1440x900 from facade
    screen_width = 1440
    screen_height = 900
    
    # Calculate half-screen layout
    left_x = 0
    right_x = screen_width // 2
    window_width = screen_width // 2
    window_height = screen_height - 100  # Leave space for dock
    
    # Get current window states
    claude_info = get_app_window("Claude")
    emacs_info = get_app_window("Emacs")
    
    print(f"📱 Before positioning:")
    if claude_info:
        print(f"   Claude: {claude_info['x']},{claude_info['y']} {claude_info['width']}x{claude_info['height']}")
    if emacs_info:
        print(f"   Emacs: {emacs_info['x']},{emacs_info['y']} {emacs_info['width']}x{emacs_info['height']}")
    
    # Position Claude on left
    success1 = position_window("Claude", left_x, 30, window_width, window_height)
    time.sleep(0.5)
    
    # Position Emacs on right  
    success2 = position_window("Emacs", right_x, 30, window_width, window_height)
    time.sleep(0.5)
    
    # Verify final positions
    claude_after = get_app_window("Claude") 
    emacs_after = get_app_window("Emacs")
    
    print(f"📱 After positioning:")
    if claude_after:
        print(f"   Claude: {claude_after['x']},{claude_after['y']} {claude_after['width']}x{claude_after['height']}")
    if emacs_after:
        print(f"   Emacs: {emacs_after['x']},{emacs_after['y']} {emacs_after['width']}x{emacs_after['height']}")
    
    # Calculate screen coverage
    total_coverage = 0
    if claude_after:
        total_coverage += claude_after['width'] * claude_after['height']
    if emacs_after:
        total_coverage += emacs_after['width'] * emacs_after['height'] 
        
    coverage_percent = (total_coverage / (screen_width * screen_height)) * 100
    
    print(f"✅ Positioning complete!")
    print(f"   Screen coverage: {coverage_percent:.1f}%")
    print(f"   Claude positioned: {success1}")
    print(f"   Emacs positioned: {success2}")
    
    return claude_after, emacs_after

if __name__ == '__main__':
    arrange_side_by_side()