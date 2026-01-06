#!/usr/bin/env python3
"""
Force and maintain side-by-side layout despite Stage Manager
"""

import subprocess
import time

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

def force_side_by_side():
    """Force windows side-by-side and make it stick"""
    print("🔄 FORCING SIDE-BY-SIDE LAYOUT")
    print("=" * 35)
    
    # Step 1: Bring both apps to foreground in sequence
    print("1. Activating both apps...")
    osascript('tell application "iTerm2" to activate')
    time.sleep(0.3)
    osascript('tell application "Emacs" to activate') 
    time.sleep(0.3)
    osascript('tell application "iTerm2" to activate')
    time.sleep(0.3)
    
    # Step 2: Force exact positioning multiple times
    print("2. Force positioning (multiple attempts)...")
    
    for attempt in range(3):
        print(f"   Attempt {attempt + 1}...")
        
        # Position iTerm2 left
        osascript('''
            tell application "System Events"
                tell process "iTerm2"
                    if (count of windows) > 0 then
                        set position of window 1 to {0, 30}
                        set size of window 1 to {720, 870}
                    end if
                end tell
            end tell
        ''')
        
        time.sleep(0.2)
        
        # Position Emacs right
        osascript('''
            tell application "System Events"
                tell process "Emacs"
                    if (count of windows) > 0 then
                        set position of window 1 to {720, 30}
                        set size of window 1 to {720, 870}
                    end if
                end tell
            end tell
        ''')
        
        time.sleep(0.2)
        
        # Check if it worked
        iterm_pos, _ = osascript('tell application "System Events" to tell process "iTerm2" to get position of window 1')
        emacs_pos, _ = osascript('tell application "System Events" to tell process "Emacs" to get position of window 1')
        
        print(f"      iTerm2: {iterm_pos}, Emacs: {emacs_pos}")
        
        if "720" in emacs_pos and ("0" in iterm_pos or iterm_pos.startswith("0")):
            print(f"   ✅ Success on attempt {attempt + 1}")
            break
        
        time.sleep(0.3)
    
    # Step 3: Use Stage Manager drag to lock them together
    print("\n3. Using Stage Manager to lock positions...")
    
    # Move to left edge to show Stage Manager
    cliclick('m 1,400')
    time.sleep(0.5)
    
    # If there are apps in sidebar, try to group them
    cliclick('m 720,400')  # Move to main area
    time.sleep(0.3)
    
    # Step 4: Try Split View approach
    print("\n4. Attempting Split View approach...")
    
    # Activate Emacs and try to trigger Split View
    osascript('tell application "Emacs" to activate')
    time.sleep(0.3)
    
    # Try holding Option and clicking green button
    osascript('''
        tell application "System Events"
            tell process "Emacs"
                if (count of windows) > 0 then
                    -- Try to trigger split view
                    -- This simulates Option+Click on green button
                    try
                        click button 3 of window 1
                    end try
                end if
            end tell
        end tell
    ''')
    
    time.sleep(1)
    
    # If split view selector appeared, select iTerm2
    osascript('tell application "iTerm2" to activate')
    time.sleep(0.5)
    
    # Step 5: Final verification and lock
    print("\n5. Final positioning and verification...")
    
    # One more forced positioning
    osascript('''
        tell application "System Events"
            tell process "iTerm2"
                set position of window 1 to {0, 30}
                set size of window 1 to {720, 870}
            end tell
            
            delay 0.1
            
            tell process "Emacs"
                set position of window 1 to {720, 30}
                set size of window 1 to {720, 870}
            end tell
        end tell
    ''')
    
    time.sleep(0.5)
    
    # Verify final positions
    iterm_info, _ = osascript('tell application "System Events" to tell process "iTerm2" to get {position of window 1, size of window 1}')
    emacs_info, _ = osascript('tell application "System Events" to tell process "Emacs" to get {position of window 1, size of window 1}')
    
    print(f"\n📊 FINAL RESULT:")
    print(f"   iTerm2: {iterm_info}")
    print(f"   Emacs:  {emacs_info}")
    
    # Check if we achieved side-by-side
    success = "720" in emacs_info and ("0" in iterm_info or iterm_info.startswith("0"))
    
    if success:
        print(f"\n✅ SUCCESS! Windows are side-by-side")
        print(f"   iTerm2 (this session) on LEFT")
        print(f"   Emacs on RIGHT")
    else:
        print(f"\n⚠️  Partial success - may need manual adjustment")
        print(f"   Try: Hover left edge → Click Emacs → Drag to main area")
    
    return success

def create_persistent_layout_command():
    """Create a command to instantly restore layout"""
    script_content = '''#!/usr/bin/env osascript
tell application "System Events"
    tell process "iTerm2"
        if (count of windows) > 0 then
            set position of window 1 to {0, 30}
            set size of window 1 to {720, 870}
        end if
    end tell
    
    delay 0.1
    
    tell process "Emacs"
        if (count of windows) > 0 then
            set position of window 1 to {720, 30}
            set size of window 1 to {720, 870}
        end if
    end tell
end tell

return "Side-by-side layout applied"'''
    
    with open('/tmp/restore_side_by_side.scpt', 'w') as f:
        f.write(script_content)
    
    print(f"\n💾 Created restore command: /tmp/restore_side_by_side.scpt")
    print(f"   Run: osascript /tmp/restore_side_by_side.scpt")

if __name__ == '__main__':
    success = force_side_by_side()
    create_persistent_layout_command()
    
    if success:
        print(f"\n🎯 Use: osascript /tmp/restore_side_by_side.scpt")
        print(f"   To instantly restore this layout anytime!")
    else:
        print(f"\n🔄 If not working, try running again or use manual Stage Manager")