#!/usr/bin/env python3
"""
Learn how to control macOS Stage Manager
"""

import subprocess
import time

def osascript(script):
    """Execute AppleScript"""
    result = subprocess.run(['osascript', '-e', script], 
                          capture_output=True, text=True)
    return result.stdout.strip(), result.stderr.strip()

def learn_stage_manager():
    """Learn Stage Manager behavior"""
    print("🎭 Learning Stage Manager Control")
    print("=" * 40)
    
    # Check current app arrangement
    print("1. Detecting current app groups...")
    stdout, stderr = osascript('''
        tell application "System Events"
            set frontProc to first process whose frontmost is true
            set allProcs to name of every process whose background only is false
            return {name of frontProc, allProcs}
        end tell
    ''')
    print(f"   Result: {stdout}")
    
    # Try to bring Emacs to same stage as iTerm2
    print("\\n2. Attempting to group Emacs with iTerm2...")
    stdout, stderr = osascript('''
        tell application "System Events"
            -- First activate iTerm2 to establish the main stage
            tell application "iTerm2" to activate
            delay 0.5
            
            -- Then try to bring Emacs to the same space
            tell application "Emacs" to activate
            delay 0.5
            
            -- Position both windows side by side
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
            
            return "Positioning attempted"
        end tell
    ''')
    print(f"   Result: {stdout}")
    
    # Check Stage Manager grouping behavior
    print("\\n3. Testing Stage Manager group behavior...")
    
    # Click near left edge to trigger Stage Manager
    stdout, stderr = osascript('''
        tell application "System Events"
            -- Move mouse to left edge to show stage manager
            -- Note: This requires accessibility permissions
            try
                return "Stage manager interaction would require mouse control"
            end try
        end tell
    ''')
    print(f"   Stage Manager: {stdout}")
    
    # Alternative: Use Mission Control to see all windows
    print("\\n4. Alternative: Using Mission Control approach...")
    stdout, stderr = osascript('''
        tell application "System Events"
            -- Try to use Mission Control to see all spaces
            key code 126 using control down -- F3/Mission Control
            delay 1
            key code 53 -- Escape to exit Mission Control
            return "Mission Control triggered"
        end tell
    ''')
    print(f"   Mission Control: {stdout}")
    
    # Final verification
    print("\\n5. Verifying final window positions...")
    for app in ["iTerm2", "Emacs"]:
        stdout, stderr = osascript(f'''
            tell application "System Events"
                try
                    tell process "{app}"
                        if (count of windows) > 0 then
                            return position of window 1 & size of window 1
                        end if
                    end tell
                end try
            end tell
        ''')
        print(f"   {app}: {stdout}")
    
    print("\\n🎯 Stage Manager Learning Summary:")
    print("   - Apps may be grouped in different stages")
    print("   - Need to activate both apps in sequence") 
    print("   - Window positioning works within each stage")
    print("   - May need manual stage switching")

if __name__ == '__main__':
    learn_stage_manager()