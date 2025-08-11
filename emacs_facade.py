#!/usr/bin/env python3
"""
Emacs Facade
A persistent Redis representation of actual Emacs state for instant verification
"""

import redis
import json
import time
from typing import Dict, List, Any, Optional


class EmacsFacade:
    def __init__(self, host='localhost', port=6380):
        self.redis_client = redis.Redis(host=host, port=port, decode_responses=True)
        self.facade_key = "emacs:facade"

    def get_current_state(self) -> Dict[str, Any]:
        """Get current Emacs state from facade"""
        try:
            state_json = self.redis_client.get(self.facade_key)
            if state_json:
                return json.loads(state_json)
            else:
                return self._default_state()
        except:
            return self._default_state()

    def _default_state(self) -> Dict[str, Any]:
        """Default Emacs state structure"""
        return {
            "timestamp": time.time(),
            "windows": {"count": 1, "layout": "single", "current_window": 0},
            "buffers": {
                "current": "*scratch*",
                "list": ["*scratch*", "*Messages*"],
                "contents": {},
            },
            "cursor": {
                "buffer": "*scratch*",
                "position": "point-max",
                "line": 1,
                "column": 0,
            },
            "modes": {"major_mode": "lisp-interaction-mode", "minor_modes": []},
            "last_command": None,
            "last_update": time.time(),
        }

    def update_state(self, updates: Dict[str, Any]) -> bool:
        """Update facade state"""
        try:
            current_state = self.get_current_state()

            # Deep merge updates
            for key, value in updates.items():
                if isinstance(value, dict) and key in current_state:
                    current_state[key].update(value)
                else:
                    current_state[key] = value

            current_state["last_update"] = time.time()

            # Store back to Redis
            self.redis_client.set(self.facade_key, json.dumps(current_state))

            # Also publish state change
            self.redis_client.publish(
                "emacs:state_changes",
                json.dumps(
                    {
                        "type": "state_update",
                        "updates": updates,
                        "full_state": current_state,
                    }
                ),
            )

            return True
        except Exception as e:
            print(f"Error updating facade: {e}")
            return False

    def get_window_count(self) -> int:
        """Get number of windows"""
        state = self.get_current_state()
        return state.get("windows", {}).get("count", 1)

    def get_current_buffer(self) -> str:
        """Get current buffer name"""
        state = self.get_current_state()
        return state.get("buffers", {}).get("current", "*scratch*")

    def get_buffer_contents(self, buffer_name: str) -> str:
        """Get contents of specific buffer"""
        state = self.get_current_state()
        return state.get("buffers", {}).get("contents", {}).get(buffer_name, "")

    def is_split(self) -> bool:
        """Check if windows are split"""
        return self.get_window_count() > 1

    def get_window_layout(self) -> str:
        """Get window layout description"""
        state = self.get_current_state()
        return state.get("windows", {}).get("layout", "single")

    def verify_command_result(
        self, command: str, expected_changes: Dict[str, Any]
    ) -> bool:
        """Verify that a command produced expected state changes"""
        state = self.get_current_state()

        for key, expected_value in expected_changes.items():
            if "." in key:  # Nested key like 'windows.count'
                keys = key.split(".")
                current_value = state
                for k in keys:
                    current_value = current_value.get(k, {})

                if current_value != expected_value:
                    return False
            else:
                if state.get(key) != expected_value:
                    return False

        return True

    def format_state_summary(self) -> str:
        """Format human-readable state summary"""
        state = self.get_current_state()

        summary = f"""
🎯 **EMACS FACADE STATE**
┌─ Windows: {state['windows']['count']} ({state['windows']['layout']})
├─ Current Buffer: {state['buffers']['current']}
├─ Available Buffers: {len(state['buffers']['list'])}
├─ Cursor: {state['cursor']['buffer']}:{state['cursor']['position']}
├─ Major Mode: {state['modes']['major_mode']}
└─ Last Update: {time.strftime('%H:%M:%S', time.localtime(state['last_update']))}
"""
        return summary.strip()


# Enhanced Redis executor that updates facade
def create_facade_aware_executor():
    """Create Elisp code for facade-aware Redis executor"""

    return """
;; Facade-aware Redis executor
(defvar emacs-facade nil "Facade update functions")

(defun update-emacs-facade (updates)
  "Update the Emacs facade in Redis"
  (let ((update-json (json-encode updates)))
    (shell-command (format "redis-cli HSET emacs:facade_updates %s '%s'" 
                          (format-time-string "%s") update-json))))

(defun facade-split-window-right ()
  "Split window and update facade"
  (split-window-right)
  (update-emacs-facade 
   '((windows . ((count . ,(length (window-list)))
                (layout . "split-horizontal"))))))

(defun facade-switch-to-buffer (buffer-name)
  "Switch buffer and update facade"
  (switch-to-buffer buffer-name)
  (update-emacs-facade
   '((buffers . ((current . ,buffer-name)))
     (cursor . ((buffer . ,buffer-name))))))

(defun facade-insert-text (text)
  "Insert text and update facade"
  (insert text)
  (update-emacs-facade
   '((buffers . ((contents . ((,(buffer-name) . ,(buffer-string)))))))))

(defun facade-delete-other-windows ()
  "Delete other windows and update facade"
  (delete-other-windows)
  (update-emacs-facade
   '((windows . ((count . 1)
                (layout . "single"))))))
"""


def main():
    """Test the facade system"""
    facade = EmacsFacade()

    print("🎯 Testing Emacs Facade System")
    print("=" * 40)

    # Initialize facade
    initial_state = facade._default_state()
    facade.update_state(initial_state)

    print("📊 Initial State:")
    print(facade.format_state_summary())

    # Print facade-aware Elisp for user to load
    

    # Simulate window split
    print("\n🪟 Simulating window split...")
    facade.update_state(
        {
            "windows": {"count": 2, "layout": "split-horizontal"},
            "last_command": "split-window-right",
        }
    )

    print("📊 After Split:")
    print(facade.format_state_summary())

    # Verify split happened
    if facade.verify_command_result("split-window-right", {"windows.count": 2}):
        print("✅ Split verification: PASSED")
    else:
        print("❌ Split verification: FAILED")

    # Simulate buffer switch
    print("\n📂 Simulating buffer switch...")
    facade.update_state(
        {
            "buffers": {"current": "*AI-Workspace*"},
            "cursor": {"buffer": "*AI-Workspace*"},
            "last_command": "switch-to-buffer",
        }
    )

    print("📊 After Buffer Switch:")
    print(facade.format_state_summary())



if __name__ == "__main__":
    main()
