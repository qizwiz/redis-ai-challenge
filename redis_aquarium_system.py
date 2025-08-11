#!/usr/bin/env python3
"""
Redis Aquarium System - Container knows its boundaries, Redis coordinates all state
"""

import redis
import json
import time
import math
import subprocess
from typing import Dict, List, Tuple


class RedisAquarium:
    def __init__(self):
        self.redis_client = redis.Redis(decode_responses=True)
        self.container_width = 78
        self.container_height = 20
        self.running = False

        # Initialize aquarium container
        self.initialize_container()

    def initialize_container(self):
        """Container knows its own boundaries and physics"""

        container_data = {
            "width": self.container_width,
            "height": self.container_height,
            "boundaries": {
                "left": 1,
                "right": self.container_width - 1,
                "top": 1,
                "bottom": self.container_height - 1,
            },
            "water_physics": {
                "density": 1.0,
                "current_x": 0.1,
                "current_y": 0.0,
                "viscosity": 0.8,
            },
        }

        # Store container properties in Redis
        self.redis_client.set("aquarium:container", json.dumps(container_data))

        # Initialize fish with physics properties
        fish_data = [
            {
                "id": "blue_tang",
                "x": 20.5,
                "y": 8.3,
                "vx": 0.2,
                "vy": -0.1,
                "char": "🐠",
                "color": "blue",
            },
            {
                "id": "clownfish",
                "x": 35.7,
                "y": 12.1,
                "vx": -0.15,
                "vy": 0.05,
                "char": "🐟",
                "color": "orange",
            },
            {
                "id": "pufferfish",
                "x": 50.2,
                "y": 6.8,
                "vx": 0.1,
                "vy": 0.2,
                "char": "🐡",
                "color": "gold",
            },
            {
                "id": "shark",
                "x": 25.9,
                "y": 15.4,
                "vx": 0.3,
                "vy": -0.05,
                "char": "🦈",
                "color": "gray",
            },
            {
                "id": "grouper",
                "x": 60.1,
                "y": 18.2,
                "vx": -0.25,
                "vy": 0.15,
                "char": "🐟",
                "color": "purple",
            },
        ]

        # Store fish state in Redis
        for fish in fish_data:
            self.redis_client.hset(f"aquarium:fish:{fish['id']}", mapping=fish)

        print("🌊 Aquarium container initialized with self-aware boundaries")

    def update_physics(self):
        """Update fish physics based on container boundaries"""

        container = json.loads(self.redis_client.get("aquarium:container"))
        boundaries = container["boundaries"]
        physics = container["water_physics"]

        # Get all fish
        fish_keys = self.redis_client.keys("aquarium:fish:*")

        for fish_key in fish_keys:
            fish = self.redis_client.hgetall(fish_key)

            # Current position and velocity
            x = float(fish["x"])
            y = float(fish["y"])
            vx = float(fish["vx"])
            vy = float(fish["vy"])

            # Apply water physics
            vx += physics["current_x"] * 0.1
            vy += physics["current_y"] * 0.1

            # Add random swimming behavior
            vx += (math.random() - 0.5) * 0.1
            vy += (math.random() - 0.5) * 0.05

            # Apply viscosity (drag)
            vx *= physics["viscosity"]
            vy *= physics["viscosity"]

            # Update position
            new_x = x + vx
            new_y = y + vy

            # Container boundary collisions (container knows its limits)
            if new_x <= boundaries["left"] or new_x >= boundaries["right"]:
                vx = -vx * 0.8  # Bounce with energy loss
                new_x = max(boundaries["left"], min(boundaries["right"], new_x))

            if new_y <= boundaries["top"] or new_y >= boundaries["bottom"]:
                vy = -vy * 0.8  # Bounce with energy loss
                new_y = max(boundaries["top"], min(boundaries["bottom"], new_y))

            # Update fish in Redis
            self.redis_client.hset(
                fish_key, mapping={"x": new_x, "y": new_y, "vx": vx, "vy": vy}
            )

    def render_via_redis_bridge(self):
        """Use Redis-Emacs bridge to render the aquarium"""

        # Get container info
        container = json.loads(self.redis_client.get("aquarium:container"))

        # Build elisp rendering command
        elisp_commands = [
            '(switch-to-buffer "*aquarium*")',
            "(let ((inhibit-read-only t))",
            "(erase-buffer)",
            "(setq truncate-lines t)",
            # Draw container
            '(insert "🌊 REDIS-COORDINATED AQUARIUM 🌊\\n")',
            '(insert "┌" (make-string 78 ?─) "┐\\n")',
            # Draw water space
            f"(dotimes (row {container['height']})",
            '  (insert "│" (make-string 78 ? ) "│\\n"))',
            '(insert "└" (make-string 78 ?─) "┘")',
        ]

        # Get fish positions from Redis and add to render commands
        fish_keys = self.redis_client.keys("aquarium:fish:*")
        for fish_key in fish_keys:
            fish = self.redis_client.hgetall(fish_key)
            x = int(float(fish["x"]))
            y = int(float(fish["y"]))
            char = fish["char"]
            color = fish["color"]

            # Calculate buffer position and place fish
            elisp_commands.extend(
                [
                    f"(goto-char (+ (point-min) 82 (* {y} 80) {x}))",
                    "(delete-char 1)",
                    f'(insert (propertize "{char}" \'face \'(:foreground "{color}" :weight bold)))',
                ]
            )

        # Close let block and make read-only
        elisp_commands.extend(["(setq buffer-read-only t)", "(setq cursor-type nil))"])

        # Combine into single elisp command
        combined_elisp = "(progn " + " ".join(elisp_commands) + ' "aquarium-rendered")'

        # Send via Redis-Emacs bridge
        self.redis_client.set("emacs:aquarium-render", combined_elisp)

        # Execute via emacsclient
        try:
            result = subprocess.run(
                [
                    "emacsclient",
                    "--eval",
                    f'(eval (read (shell-command-to-string "redis-cli GET emacs:aquarium-render")))',
                ],
                capture_output=True,
                text=True,
                timeout=2,
            )

            return result.returncode == 0
        except:
            return False

    def run_aquarium(self):
        """Main aquarium loop using Redis coordination"""

        print("🚀 Starting Redis-coordinated aquarium...")
        self.running = True

        while self.running:
            try:
                # Update physics in Redis
                self.update_physics()

                # Render via Redis-Emacs bridge
                success = self.render_via_redis_bridge()

                if success:
                    print("🐠 Aquarium updated via Redis bridge")
                else:
                    print("❌ Redis bridge render failed")

                # Wait before next update
                time.sleep(0.5)

            except KeyboardInterrupt:
                print("\n⏹️ Stopping aquarium...")
                self.running = False
                break
            except Exception as e:
                print(f"💥 Aquarium error: {e}")
                time.sleep(1)

    def stop_aquarium(self):
        """Stop the aquarium"""
        self.running = False

        # Clear Redis state
        keys_to_clear = self.redis_client.keys("aquarium:*")
        if keys_to_clear:
            self.redis_client.delete(*keys_to_clear)

        print("🛑 Redis aquarium stopped and cleaned up")


if __name__ == "__main__":
    import random

    math.random = random.random  # Fix math.random

    aquarium = RedisAquarium()

    try:
        aquarium.run_aquarium()
    except KeyboardInterrupt:
        aquarium.stop_aquarium()
