#!/usr/bin/env python3
"""
Working State Sync - Push Emacs state commands that actually work
"""

import redis
import subprocess
import time


def force_state_sync():
    """Force Emacs to sync its state to Redis"""

    print("🔧 FORCING EMACS STATE SYNC")

    # Direct elisp to get and set state
    elisp_sync = """
(progn
  (let* ((buf (buffer-name (current-buffer)))
         (pt (point))
         (ln (line-number-at-pos))
         (col (current-column))
         (ts (format-time-string "%s")))
    
    ;; Set current buffer
    (shell-command-to-string (format "redis-cli SET emacs:current '%s'" buf))
    
    ;; Set detailed state  
    (shell-command-to-string 
     (format "redis-cli HSET emacs:state buffer '%s' point %d line %d column %d timestamp %s"
             buf pt ln col ts))
    
    (message "📡 State synced: %s at line %d" buf ln)
    (format "synced-%s-%d-%d" buf pt ln)))
"""

    try:
        # Try GUI Emacs first
        result = subprocess.run(
            ["emacsclient", "--eval", elisp_sync],
            capture_output=True,
            text=True,
            timeout=5,
        )

        if result.returncode == 0:
            print(f"✅ GUI Emacs sync: {result.stdout.strip()}")
            return True
    except:
        pass

    try:
        # Try daemon
        result = subprocess.run(
            ["emacsclient", "-s", "redis-tutorial", "--eval", elisp_sync],
            capture_output=True,
            text=True,
            timeout=5,
        )

        if result.returncode == 0:
            print(f"✅ Daemon sync: {result.stdout.strip()}")
            return True
    except:
        pass

    print("❌ Could not sync state")
    return False


def check_redis_state():
    """Check what's in Redis"""

    redis_client = redis.Redis(decode_responses=True)

    current = redis_client.get("emacs:current")
    state = redis_client.hgetall("emacs:state")

    print(f"\n📊 REDIS STATE:")
    print(f"   Current buffer: {current}")
    if state:
        print(f"   Buffer: {state.get('buffer')}")
        print(f"   Line: {state.get('line')}")
        print(f"   Column: {state.get('column')}")
        print(f"   Point: {state.get('point')}")
    else:
        print("   No state data")


if __name__ == "__main__":
    force_state_sync()
    time.sleep(1)
    check_redis_state()
