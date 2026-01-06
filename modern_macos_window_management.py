#!/usr/bin/env python3
"""
Learn modern macOS window management for side-by-side positioning
"""

import subprocess
import time
import json

def cliclick(command):
    """Execute cliclick command for precise mouse control"""
    result = subprocess.run(['cliclick'] + command.split(), 
                          capture_output=True, text=True)
    return result.returncode == 0, result.stdout.strip(), result.stderr.strip()

def osascript(script):
    """Execute AppleScript"""
    result = subprocess.run(['osascript', '-e', script], 
                          capture_output=True, text=True)
    return result.stdout.strip(), result.stderr.strip()

def get_mouse_pos():
    """Get current mouse position using cliclick"""
    success, stdout, stderr = cliclick('p')
    if success:
        x, y = stdout.split(',')
        return int(x), int(y)
    return None, None

def modern_window_management():
    """Learn modern macOS window management techniques"""
    print("🪟 MODERN macOS WINDOW MANAGEMENT")
    print("=" * 40)
    
    # Get current state
    mouse_x, mouse_y = get_mouse_pos()
    print(f"📍 Mouse at: ({mouse_x}, {mouse_y})")
    
    print("\n🎯 Technique 1: Native macOS Split View")
    print("   1. Hold Option + Green Button (Zoom) for split view")
    print("   2. Or drag window to edge for tiling")
    
    # Method 1: Try keyboard shortcuts for window management
    print("\n1. Testing window tiling shortcuts...")
    
    # First, ensure Emacs is active
    osascript('tell application "Emacs" to activate')
    time.sleep(0.5)
    
    # Try Control+Command+Left to dock Emacs to left side
    stdout, stderr = osascript('''
        tell application "System Events"
            key code 123 using {control down, command down}
        end tell
    ''')
    print(f"   Emacs tiling attempt: {not stderr}")
    
    time.sleep(1)
    
    # Activate iTerm2
    osascript('tell application "iTerm2" to activate')
    time.sleep(0.5)
    
    # Try Control+Command+Right to dock iTerm2 to right side
    stdout, stderr = osascript('''
        tell application "System Events"
            key code 124 using {control down, command down}
        end tell
    ''')
    print(f"   iTerm2 tiling attempt: {not stderr}")
    
    time.sleep(2)
    
    print("\n2. Testing Mission Control split screen...")
    
    # Method 2: Use Mission Control + drag to create split screen
    # First, bring Emacs to current space
    osascript('tell application "Emacs" to activate')
    time.sleep(0.5)
    
    # Try F3 (Mission Control) and programmatic split
    stdout, stderr = osascript('''
        tell application "System Events"
            -- Open Mission Control
            key code 160 -- F3
            delay 1
            -- ESC to exit for now
            key code 53
        end tell
    ''')
    print(f"   Mission Control access: {not stderr}")
    
    print("\n3. Testing Rectangle/Spectacle-style shortcuts...")
    
    # Method 3: Manual positioning with precise coordinates
    print("   Positioning Emacs left half...")
    success = position_window_precise("Emacs", 0, 30, 720, 870)
    print(f"   Emacs positioned: {success}")
    
    time.sleep(0.5)
    
    print("   Positioning iTerm2 right half...")
    success = position_window_precise("iTerm2", 720, 30, 720, 870)
    print(f"   iTerm2 positioned: {success}")
    
    print("\n4. Testing Stage Manager control...")
    
    # Method 4: Stage Manager manipulation
    # Move mouse to left edge to trigger Stage Manager
    print("   Triggering Stage Manager...")
    cliclick('m 1,400')  # Move to left edge
    time.sleep(1)
    
    # Click in Stage Manager area if visible
    cliclick('m 100,300')  # Move to potential Stage Manager sidebar
    time.sleep(0.5)
    
    # Click to select if there's something there
    cliclick('c .')  # Click at current position
    time.sleep(0.5)
    
    # Move back to main area
    cliclick('m 720,400')
    time.sleep(0.5)
    
    print("\n5. Verification - checking final positions...")
    verify_positions()
    
    print("\n✅ Modern macOS window management techniques tested")

def position_window_precise(app_name, x, y, width, height):
    """Position window with precise coordinates"""
    stdout, stderr = osascript(f'''
        tell application "System Events"
            tell process "{app_name}"
                if (count of windows) > 0 then
                    set position of window 1 to {{{x}, {y}}}
                    set size of window 1 to {{{width}, {height}}}
                    return true
                else
                    return false
                end if
            end tell
        end tell
    ''')
    return 'true' in stdout.lower() and not stderr

def verify_positions():
    """Verify final window positions"""
    apps = ["iTerm2", "Emacs"]
    for app in apps:
        stdout, stderr = osascript(f'''
            tell application "System Events"
                tell process "{app}"
                    if (count of windows) > 0 then
                        set pos to position of window 1
                        set sz to size of window 1
                        return (item 1 of pos) & "," & (item 2 of pos) & "," & (item 1 of sz) & "," & (item 2 of sz)
                    end if
                end tell
            end tell
        ''')
        print(f"   {app}: {stdout}")

def rectangle_style_positioning():
    """Try Rectangle app style shortcuts"""
    print("\n🔲 Rectangle-style positioning...")
    
    # Activate Emacs and position left
    osascript('tell application "Emacs" to activate')
    time.sleep(0.3)
    
    # Option+Command+Left Arrow (common left half shortcut)
    osascript('''
        tell application "System Events"
            key code 123 using {option down, command down}
        end tell
    ''')
    
    time.sleep(0.5)
    
    # Activate iTerm2 and position right  
    osascript('tell application "iTerm2" to activate')
    time.sleep(0.3)
    
    # Option+Command+Right Arrow (common right half shortcut)
    osascript('''
        tell application "System Events"
            key code 124 using {option down, command down}
        end tell
    ''')
    
    print("   Rectangle-style shortcuts attempted")

if __name__ == '__main__':
    modern_window_management()
    rectangle_style_positioning()