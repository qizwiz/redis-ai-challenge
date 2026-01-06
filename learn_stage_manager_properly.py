#!/usr/bin/env python3
"""
Learn Stage Manager properly from system preferences and behavior
"""

import subprocess
import time
import json

def defaults_read(domain, key=None):
    """Read macOS defaults"""
    if key:
        cmd = ['defaults', 'read', domain, key]
    else:
        cmd = ['defaults', 'read', domain]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout.strip() if result.returncode == 0 else None

def osascript(script):
    """Execute AppleScript"""
    result = subprocess.run(['osascript', '-e', script], 
                          capture_output=True, text=True)
    return result.stdout.strip(), result.stderr.strip()

def cliclick(command):
    """Execute cliclick command"""
    result = subprocess.run(['cliclick'] + command.split(), 
                          capture_output=True, text=True)
    return result.returncode == 0, result.stdout.strip(), result.stderr.strip()

def learn_stage_manager_configuration():
    """Learn Stage Manager from system configuration"""
    print("🎭 LEARNING STAGE MANAGER FROM SYSTEM CONFIG")
    print("=" * 50)
    
    # Read Stage Manager settings
    wm_config = defaults_read('com.apple.WindowManager')
    if wm_config:
        print("📋 Window Manager Configuration:")
        for line in wm_config.split('\n')[:10]:
            if any(term in line.lower() for term in ['stage', 'global', 'enabled', 'behavior', 'hide']):
                print(f"   {line.strip()}")
    
    # Check if Stage Manager is enabled
    enabled = defaults_read('com.apple.WindowManager', 'GloballyEnabled')
    print(f"\n🎯 Stage Manager Enabled: {enabled == '1'}")
    
    # Check app grouping behavior  
    grouping = defaults_read('com.apple.WindowManager', 'AppWindowGroupingBehavior')
    print(f"📱 App Grouping Behavior: {grouping}")
    
    # Check hide desktop setting
    hide_desktop = defaults_read('com.apple.WindowManager', 'HideDesktop') 
    print(f"🖥️  Hide Desktop: {hide_desktop == '1'}")
    
    return enabled == '1'

def stage_manager_window_control():
    """Learn Stage Manager window control through experimentation"""
    print("\n🎮 STAGE MANAGER WINDOW CONTROL EXPERIMENTS")
    print("=" * 50)
    
    # Experiment 1: Detect current stage arrangement
    print("1. Detecting current app arrangement...")
    
    # Get all running apps
    stdout, stderr = osascript('''
        tell application "System Events"
            set frontApp to name of first process whose frontmost is true
            set allApps to name of every process whose background only is false
            return {frontApp, count of allApps, allApps}
        end tell
    ''')
    print(f"   Current arrangement: {stdout}")
    
    # Experiment 2: Try to understand Stage Manager groups
    print("\n2. Understanding Stage Manager groups...")
    
    # Check what windows are visible vs hidden
    apps_to_check = ["iTerm2", "Emacs", "Claude"]
    for app in apps_to_check:
        stdout, stderr = osascript(f'''
            tell application "System Events"
                try
                    tell process "{app}"
                        if exists then
                            set visibleWindows to (every window whose value of attribute "AXMinimized" is false)
                            return (count of visibleWindows)
                        else
                            return "not running"
                        end if
                    end tell
                end try
            end tell
        ''')
        print(f"   {app}: {stdout} visible windows")
    
    # Experiment 3: Try Stage Manager edge interaction
    print("\n3. Stage Manager edge interaction...")
    
    # Move mouse to far left edge slowly
    print("   Moving to left edge...")
    success, stdout, stderr = cliclick('m 1,400')
    time.sleep(1)
    
    # Check if Stage Manager sidebar appeared
    # Look for windows at x < 300 (typical sidebar area)
    stdout, stderr = osascript('''
        tell application "System Events"
            set stageApps to {}
            repeat with proc in (every process whose background only is false)
                set procName to name of proc
                tell proc
                    repeat with w in windows
                        try
                            set winPos to position of w
                            if (item 1 of winPos) < 300 then
                                set end of stageApps to {procName, name of w, winPos}
                            end if
                        end try
                    end repeat
                end tell
            end repeat
            return stageApps
        end tell
    ''')
    print(f"   Apps in Stage Manager sidebar: {stdout}")
    
    # Experiment 4: Try to bring Emacs to main stage
    print("\n4. Attempting to bring Emacs to main stage...")
    
    # Method A: Click and drag from sidebar to main area
    if "Emacs" in stdout:
        print("   Emacs found in sidebar - attempting to bring to main stage")
        
        # Try clicking on Emacs in sidebar
        success, mouse_pos, stderr = cliclick('p')
        
        # Move to where Emacs likely is in sidebar (estimate)
        cliclick('m 150,300')
        time.sleep(0.5)
        cliclick('c .')  # Click
        time.sleep(0.5)
        
        # Drag to main area
        cliclick('dd 720,400')  # Drag to center-right of screen
        time.sleep(1)
        
        print("   Drag operation completed")
    
    # Method B: Use keyboard shortcuts for Stage Manager
    print("\n   Trying keyboard shortcuts...")
    
    # Try Control+Up Arrow (Show all windows)
    osascript('''
        tell application "System Events"
            key code 126 using control down
        end tell
    ''')
    time.sleep(1)
    
    # ESC to exit if it opened something
    osascript('''
        tell application "System Events"
            key code 53
        end tell
    ''')
    
    print("   Keyboard shortcuts tested")
    
    # Experiment 5: Final verification
    print("\n5. Final window verification...")
    verify_final_layout()

def verify_final_layout():
    """Verify final window layout"""
    apps = ["iTerm2", "Emacs"]
    layout = {}
    
    for app in apps:
        stdout, stderr = osascript(f'''
            tell application "System Events"
                try
                    tell process "{app}"
                        if (count of windows) > 0 then
                            set mainWindow to window 1
                            set winPos to position of mainWindow
                            set winSize to size of mainWindow
                            set isMinimized to value of attribute "AXMinimized" of mainWindow
                            return (item 1 of winPos) & "," & (item 2 of winPos) & "," & (item 1 of winSize) & "," & (item 2 of winSize) & "," & isMinimized
                        end if
                    end tell
                end try
            end tell
        ''')
        
        if stdout and ',' in stdout:
            parts = stdout.split(',')
            layout[app] = {
                'x': int(parts[0]) if parts[0].isdigit() else parts[0],
                'y': int(parts[1]) if parts[1].isdigit() else parts[1], 
                'width': int(parts[2]) if parts[2].isdigit() else parts[2],
                'height': int(parts[3]) if parts[3].isdigit() else parts[3],
                'minimized': parts[4] if len(parts) > 4 else 'unknown'
            }
        
        print(f"   {app}: {layout.get(app, 'not found')}")
    
    # Check if they're actually side-by-side
    if 'iTerm2' in layout and 'Emacs' in layout:
        iterm_x = layout['iTerm2']['x']
        emacs_x = layout['Emacs']['x']
        
        if isinstance(iterm_x, int) and isinstance(emacs_x, int):
            side_by_side = abs(iterm_x - emacs_x) > 500  # Significant horizontal separation
            print(f"\n✅ Side-by-side layout: {side_by_side}")
            print(f"   iTerm2 at x={iterm_x}, Emacs at x={emacs_x}")
        else:
            print(f"\n❌ Could not determine positions: iTerm2={iterm_x}, Emacs={emacs_x}")
    
    return layout

def disable_stage_manager_temporarily():
    """Temporarily disable Stage Manager to test normal window management"""
    print("\n🔧 Testing with Stage Manager disabled...")
    
    # Disable Stage Manager
    subprocess.run(['defaults', 'write', 'com.apple.WindowManager', 'GloballyEnabled', '-bool', 'false'])
    
    # Kill Dock to apply changes
    subprocess.run(['killall', 'Dock'])
    
    print("   Stage Manager disabled - Dock restarting...")
    time.sleep(3)  # Wait for Dock to restart
    
    # Now try normal window positioning
    print("   Attempting normal window positioning...")
    
    # Position windows normally
    osascript('''
        tell application "System Events"
            tell process "iTerm2"
                if (count of windows) > 0 then
                    set position of window 1 to {0, 30}
                    set size of window 1 to {720, 870}
                end if
            end tell
            
            tell process "Emacs"
                if (count of windows) > 0 then
                    set position of window 1 to {720, 30} 
                    set size of window 1 to {720, 870}
                end if
            end tell
        end tell
    ''')
    
    time.sleep(2)
    layout = verify_final_layout()
    
    # Re-enable Stage Manager
    subprocess.run(['defaults', 'write', 'com.apple.WindowManager', 'GloballyEnabled', '-bool', 'true'])
    subprocess.run(['killall', 'Dock'])
    
    print("   Stage Manager re-enabled")
    return layout

if __name__ == '__main__':
    # Learn Stage Manager configuration
    stage_manager_enabled = learn_stage_manager_configuration()
    
    if stage_manager_enabled:
        # Try Stage Manager control
        stage_manager_window_control()
        
        # If that doesn't work, try temporarily disabling it
        print(f"\n🔄 If windows aren't visible, trying temporary disable...")
        disable_stage_manager_temporarily()
    else:
        print("\n✅ Stage Manager is disabled - using normal positioning")
        verify_final_layout()