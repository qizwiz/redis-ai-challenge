#!/usr/bin/env python3
"""
Redis OS Bridge - Connects Redis commands to actual OS control
Using existing infrastructure without adding new code concepts
"""

import redis
import subprocess
import json
import time

# Use existing Redis connection
r = redis.Redis(decode_responses=True)

def execute_redis_command(command_data):
    """Execute OS commands from Redis using existing infrastructure"""
    action = command_data.get('action')
    command = command_data.get('command') 
    
    if command == 'get_windows':
        # Use existing window enumeration code
        script = '''
        tell application "System Events"
            set windowList to {}
            repeat with proc in (every process whose visible is true)
                try
                    repeat with win in (every window of proc)
                        set windowInfo to (name of win) & " - " & (name of proc)
                        set end of windowList to windowInfo
                    end repeat
                end try
            end repeat
            return windowList
        end tell
        '''
        result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
        windows = result.stdout.strip().split(", ")
        
        # Store result back to Redis
        r.xadd("ai:results", "*", {
            "action": action,
            "command": command,
            "result": f"Found {len(windows)} windows: " + ", ".join(windows[:3]) + "...",
            "timestamp": int(time.time()),
            "status": "completed"
        })
        print(f"✅ Executed {command}: Found {len(windows)} windows")
        return True
        
    return False

# Check for commands and execute
print("🔌 Checking Redis for AI commands...")
try:
    # Check ai:commands stream
    messages = r.xread({"ai:commands": "$"}, count=10, block=1000)
    
    for stream, msgs in messages:
        for msg_id, fields in msgs:
            print(f"📨 Found command: {fields}")
            if execute_redis_command(fields):
                print("✅ Command executed successfully")
            
except Exception as e:
    print(f"No new commands: {e}")

# Also check existing commands
try:
    recent_commands = r.xrevrange("ai:commands", count=5)
    print(f"📋 Found {len(recent_commands)} recent commands in Redis")
    
    for msg_id, fields in recent_commands:
        print(f"   {fields}")
        if fields.get('command') == 'get_windows':
            execute_redis_command(fields)
            break
            
except Exception as e:
    print(f"Error reading commands: {e}")

print("🔌 Redis OS Bridge check complete")