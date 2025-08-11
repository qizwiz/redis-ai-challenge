#!/usr/bin/env python3
"""
Simplest Possible Aquarium - Step 1
Single fish emoji moving back and forth, coordinated via Redis
AI agent controls Emacs with 100% visibility
"""

import time
import subprocess
import redis


class RedisCoordinatedAquarium:
    def __init__(self):
        self.redis_client = redis.Redis(decode_responses=True)
        self.running = False

        # Initialize state in Redis
        self.redis_client.set("aquarium:fish:x", "25")
        self.redis_client.set("aquarium:fish:direction", "1")
        print("🐠 Aquarium state initialized in Redis")

    def setup_emacs_buffer(self):
        """Create and setup the aquarium buffer in Emacs"""
        elisp_command = """
        (progn
          (switch-to-buffer "*Aquarium-V1*")
          (delete-other-windows)
          (let ((inhibit-read-only t))
            (erase-buffer)
            (insert "🌊 REDIS-COORDINATED AQUARIUM V1 🌊\\n\\n")
            (insert "┌────────────────────────────────────────────────────────────────────────────┐\\n")
            (insert "│                                                                            │\\n")
            (insert "│                                                                            │\\n") 
            (insert "│                                                                            │\\n")
            (insert "│                     🐠                                                      │\\n")
            (insert "│                                                                            │\\n")
            (insert "│                                                                            │\\n")
            (insert "│                                                                            │\\n")
            (insert "└────────────────────────────────────────────────────────────────────────────┘\\n")
            (insert "\\nAI Agent controlling via Redis..."))
          (setq buffer-read-only t)
          "buffer-setup-complete")
        """

        try:
            result = subprocess.run(
                ["emacsclient", "--eval", elisp_command],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.returncode == 0
        except Exception as e:
            print(f"Setup error: {e}")
            return False

    def update_fish_position(self):
        """Update fish position using Redis coordination"""
        # Get current state from Redis
        fish_x = int(self.redis_client.get("aquarium:fish:x"))
        direction = int(self.redis_client.get("aquarium:fish:direction"))

        # Update position
        new_x = fish_x + (direction * 3)

        # Bounce off walls
        if new_x >= 75:
            new_x = 75
            direction = -1
        elif new_x <= 5:
            new_x = 5
            direction = 1

        # Store new state in Redis
        self.redis_client.set("aquarium:fish:x", str(new_x))
        self.redis_client.set("aquarium:fish:direction", str(direction))

        return new_x, direction

    def render_frame(self, fish_x):
        """Render one frame with fish at specified position"""
        fish_line = "│" + " " * (fish_x - 1) + "🐠" + " " * (76 - fish_x) + "│"

        elisp_command = f"""
        (with-current-buffer "*Aquarium-V1*"
          (let ((inhibit-read-only t))
            (goto-char (point-min))
            (forward-line 6)
            (kill-line)
            (insert "{fish_line}")
            (goto-char (point-min))))
        """

        try:
            result = subprocess.run(
                ["emacsclient", "--eval", elisp_command],
                capture_output=True,
                text=True,
                timeout=1,
            )
            return result.returncode == 0
        except:
            return False

    def run_animation(self):
        """Main animation loop using Redis coordination"""
        print("🚀 Starting Redis-Coordinated Aquarium V1...")
        print("🎯 AI Agent controlling Emacs via Redis state")
        print("👀 Watch your Emacs buffer: *Aquarium-V1*")

        # Setup buffer
        if not self.setup_emacs_buffer():
            print("❌ Failed to setup Emacs buffer")
            return

        self.running = True
        frame_count = 0

        try:
            while self.running:
                # Update via Redis coordination
                fish_x, direction = self.update_fish_position()

                # Render the frame
                success = self.render_frame(fish_x)

                frame_count += 1
                if frame_count % 5 == 0:
                    arrow = "→" if direction == 1 else "←"
                    print(f"🎬 Frame {frame_count} - Fish at {fish_x} moving {arrow}")

                if not success:
                    print("⚠️ Render issue (continuing...)")

                # Store frame info in Redis for visibility
                self.redis_client.set("aquarium:last_frame", str(frame_count))
                self.redis_client.set("aquarium:last_render", str(time.time()))

                time.sleep(0.4)

        except KeyboardInterrupt:
            print("\n⏹️ Stopping Redis-Coordinated Aquarium V1")
            self.running = False


if __name__ == "__main__":
    aquarium = RedisCoordinatedAquarium()
    aquarium.run_animation()
