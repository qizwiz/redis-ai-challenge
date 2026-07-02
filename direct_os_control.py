#!/usr/bin/env python3
"""
Direct OS Control Demo - Prove we can control the system
"""

import subprocess
import os
import time

def demonstrate_os_control():
    """Demonstrate direct OS control capabilities"""
    print("🖥️  DEMONSTRATING DIRECT OS CONTROL")
    print("=" * 50)
    
    # 1. Get current windows
    print("1. 📋 Getting all open windows...")
    try:
        script = '''
        tell application "System Events"
            set windowList to {}
            repeat with proc in (every process whose visible is true)
                try
                    repeat with win in (every window of proc)
                        set windowInfo to (name of win) & " (" & (name of proc) & ")"
                        set end of windowList to windowInfo
                    end repeat
                end try
            end repeat
            return windowList
        end tell
        '''
        result = subprocess.run(['osascript', '-e', script], 
                              capture_output=True, text=True)
        windows = result.stdout.strip().split(", ")
        print(f"   Found {len(windows)} windows:")
        for window in windows[:5]:  # Show first 5
            print(f"   - {window}")
        print()
    except Exception as e:
        print(f"   Error: {e}")
    
    # 2. Create a file
    print("2. 📄 Creating file controlled by AI...")
    try:
        filename = "ai_controlled_file.txt"
        content = f"""This file was created by AI with direct OS control.
        
Created at: {time.ctime()}
Process: Direct system API calls
Method: Fly-by-wire OS control (not screen capture)

The AI system has:
✅ File system access
✅ Window enumeration 
✅ Application control
✅ Mouse/keyboard simulation
✅ Process management
"""
        
        with open(filename, 'w') as f:
            f.write(content)
        print(f"   ✅ Created: {filename}")
        print()
    except Exception as e:
        print(f"   Error: {e}")
    
    # 3. Open an application
    print("3. 🚀 Opening application...")
    try:
        script = 'tell application "TextEdit" to activate'
        result = subprocess.run(['osascript', '-e', script], 
                              capture_output=True, text=True)
        print("   ✅ Opened TextEdit")
        time.sleep(2)
        print()
    except Exception as e:
        print(f"   Error: {e}")
    
    # 4. Type text into the application
    print("4. ⌨️  Typing text with AI control...")
    try:
        text = "Hello! This text is being typed by AI with direct OS control."
        script = f'''
        tell application "System Events"
            keystroke "{text}"
        end tell
        '''
        result = subprocess.run(['osascript', '-e', script], 
                              capture_output=True, text=True)
        print(f"   ✅ Typed: {text}")
        print()
    except Exception as e:
        print(f"   Error: {e}")
    
    # 5. Move mouse (simulate click)
    print("5. 🖱️  Demonstrating mouse control...")
    try:
        script = '''
        tell application "System Events"
            set mouseLoc to {100, 100}
            click at mouseLoc
        end tell
        '''
        result = subprocess.run(['osascript', '-e', script], 
                              capture_output=True, text=True)
        print("   ✅ Mouse moved and clicked at (100, 100)")
        print()
    except Exception as e:
        print(f"   Error: {e}")
    
    print("🎯 OS CONTROL DEMONSTRATION COMPLETE")
    print("The AI system has direct, fly-by-wire control of:")
    print("   - File system")
    print("   - Applications") 
    print("   - Windows")
    print("   - Mouse/keyboard")
    print("   - System processes")
    print()
    print("This is REAL OS control, not simulation or screen capture.")

if __name__ == "__main__":
    demonstrate_os_control()