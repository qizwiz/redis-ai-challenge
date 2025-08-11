#!/usr/bin/env python3
"""
Spatial AI Agent - Redis-coordinated intelligent Emacs control
Novel use cases: spatial pattern recognition, intelligent navigation, contextual actions
"""

import redis
import json
import time
import random


class SpatialAIAgent:
    def __init__(self):
        self.redis = redis.Redis(decode_responses=True)
        self.session_id = f"spatial_ai_{int(time.time())}"
        print(f"🤖 Spatial AI Agent started - {self.session_id}")

    def get_spatial_state(self):
        """Get current spatial state from Redis"""
        try:
            state_raw = self.redis.get("emacs:spatial_state")
            if state_raw:
                return eval(state_raw)  # Parse Lisp-style data
            return []
        except:
            return []

    def execute_emacs(self, command):
        """Execute Emacs command via Redis"""
        self.redis.lpush("emacs:commands", command)
        time.sleep(0.5)
        result = self.redis.get("emacs:last_command_result")
        return result

    def spatial_hunt(self, target_pattern):
        """Novel: Hunt for patterns across windows spatially"""
        print(f"🎯 Spatial Hunt: Looking for '{target_pattern}'")

        spatial_state = self.get_spatial_state()

        for window_info in spatial_state:
            buffer_name = window_info[1]  # Extract buffer name
            edges = window_info[3]  # Extract edges

            print(f"  🔍 Searching in {buffer_name} at coordinates {edges}")

            # Search for pattern in this buffer
            search_cmd = f'(with-current-buffer "{buffer_name}" (save-excursion (goto-char 1) (search-forward "{target_pattern}" nil t)))'
            result = self.execute_emacs(search_cmd)

            if result and result != "nil":
                print(f"  ✅ Found '{target_pattern}' in {buffer_name}")

                # Move to the pattern and highlight it
                goto_cmd = f'(progn (select-window (get-buffer-window "{buffer_name}")) (search-forward "{target_pattern}") (set-mark (point)) (search-backward "{target_pattern}") (list "hunted" (current-column) (line-number-at-pos)))'
                position = self.execute_emacs(goto_cmd)

                return {
                    "found": True,
                    "buffer": buffer_name,
                    "position": position,
                    "edges": edges,
                }

        print(f"  ❌ Pattern '{target_pattern}' not found in any window")
        return {"found": False}

    def spatial_dance(self, pattern="random"):
        """Novel: Perform coordinated movements across windows"""
        print(f"💃 Spatial Dance: {pattern}")

        spatial_state = self.get_spatial_state()

        if pattern == "random":
            # Random dance across windows
            for i in range(5):
                window_info = random.choice(spatial_state)
                buffer_name = window_info[1]

                # Random position in buffer
                size_cmd = f'(with-current-buffer "{buffer_name}" (buffer-size))'
                size = self.execute_emacs(size_cmd)

                if size and size.isdigit():
                    random_pos = random.randint(1, min(int(size), 1000))

                    dance_cmd = f'(progn (select-window (get-buffer-window "{buffer_name}")) (goto-char {random_pos}) (sit-for 0.3) (list "dance-step" {i} (line-number-at-pos) (current-column)))'
                    position = self.execute_emacs(dance_cmd)
                    print(f"  🕺 Dance step {i}: {buffer_name} -> {position}")
                    time.sleep(0.5)

        elif pattern == "spiral":
            # Spiral pattern across coordinate space
            print("  🌀 Spiral dance across windows")

            for window_info in spatial_state:
                buffer_name = window_info[1]
                edges = window_info[3]

                # Create spiral movement within window bounds
                for radius in range(1, 4):
                    spiral_cmd = f'(progn (select-window (get-buffer-window "{buffer_name}")) (goto-line {radius * 3}) (move-to-column {radius * 10}) (sit-for 0.2) (list "spiral" {radius}))'
                    self.execute_emacs(spiral_cmd)
                    time.sleep(0.3)

    def spatial_mirror(self):
        """Novel: Mirror actions across windows"""
        print("🪞 Spatial Mirror: Synchronized window actions")

        spatial_state = self.get_spatial_state()

        if len(spatial_state) >= 2:
            window1 = spatial_state[0]
            window2 = spatial_state[1]

            buffer1 = window1[1]
            buffer2 = window2[1]

            print(f"  🔄 Mirroring between {buffer1} and {buffer2}")

            # Synchronized movements
            for line in [5, 10, 15]:
                # Move both cursors to same line
                mirror_cmd = f'(progn (select-window (get-buffer-window "{buffer1}")) (goto-line {line}) (select-window (get-buffer-window "{buffer2}")) (goto-line {line}) (list "mirrored-line" {line}))'
                result = self.execute_emacs(mirror_cmd)
                print(f"    ↔️  Mirrored to line {line}: {result}")
                time.sleep(0.4)

    def spatial_pathfind(self, start_pattern, end_pattern):
        """Novel: Find path between two text patterns"""
        print(f"🗺️  Spatial Pathfinding: {start_pattern} -> {end_pattern}")

        # Find start location
        start_result = self.spatial_hunt(start_pattern)
        if not start_result["found"]:
            return {"error": "Start pattern not found"}

        # Find end location
        end_result = self.spatial_hunt(end_pattern)
        if not end_result["found"]:
            return {"error": "End pattern not found"}

        print(f"  🚩 Start: {start_result}")
        print(f"  🏁 End: {end_result}")

        # Create visual path (if in same buffer)
        if start_result["buffer"] == end_result["buffer"]:
            buffer_name = start_result["buffer"]

            # Animate path
            path_cmd = f"""
            (progn 
              (select-window (get-buffer-window "{buffer_name}"))
              (search-forward "{start_pattern}")
              (sit-for 0.5)
              (search-forward "{end_pattern}")
              (message "Path complete: {start_pattern} -> {end_pattern}")
              "path-complete")
            """

            result = self.execute_emacs(path_cmd)
            return {"path": "complete", "same_buffer": True, "result": result}

        return {"path": "cross-buffer", "start": start_result, "end": end_result}

    def demo_novel_spatial_intelligence(self):
        """Demonstrate novel spatial AI capabilities"""
        print("🚀 NOVEL SPATIAL AI AGENT DEMO")
        print("=" * 40)

        # 1. Spatial Hunt
        print("\n1️⃣  SPATIAL HUNT")
        self.spatial_hunt("Emacs")

        time.sleep(2)

        # 2. Spatial Dance
        print("\n2️⃣  SPATIAL DANCE")
        self.spatial_dance("random")

        time.sleep(2)

        # 3. Spatial Mirror
        print("\n3️⃣  SPATIAL MIRROR")
        self.spatial_mirror()

        time.sleep(2)

        # 4. Spatial Pathfinding
        print("\n4️⃣  SPATIAL PATHFINDING")
        self.spatial_pathfind("tutorial", "commands")

        print("\n🎉 Novel Spatial AI Demo Complete!")


if __name__ == "__main__":
    agent = SpatialAIAgent()
    agent.demo_novel_spatial_intelligence()
