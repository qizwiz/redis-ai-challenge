#!/usr/bin/env python3
"""
Redis Aquarium REPL - Interactive coordination interface
Applying learned patterns from redis-ai-coordinator subagent
"""

import redis
import json
import time
import subprocess
import math
import random
from typing import Dict, List, Any


class AquariumREPL:
    def __init__(self):
        self.redis_client = redis.Redis(decode_responses=True)
        self.running = True
        self.animation_active = False

        # Apply semantic understanding: aquarium = living ecosystem
        self.commands = {
            "start": self.start_aquarium,
            "stop": self.stop_aquarium,
            "add": self.add_fish,
            "remove": self.remove_fish,
            "list": self.list_fish,
            "status": self.show_status,
            "animate": self.toggle_animation,
            "physics": self.show_physics,
            "clear": self.clear_aquarium,
            "help": self.show_help,
            "quit": self.quit_repl,
        }

        print("🌊 REDIS AQUARIUM REPL - Interactive Living Environment 🌊")
        print("Apply learned UX patterns: visibility + proper coordination")
        print("Type 'help' for commands or 'start' to begin")

    def create_water_container(self):
        """Create aquarium with proper visibility (learned pattern)"""
        elisp_commands = [
            '(switch-to-buffer "*redis-aquarium*")',
            "(delete-other-windows)",  # LEARNED: Always ensure visibility
            "(let ((inhibit-read-only t))",
            "(erase-buffer)",
            "(setq truncate-lines t)",
            '(insert "🌊 REDIS-AI COORDINATED LIVING AQUARIUM 🌊\\n")',
            '(insert "┌" (make-string 76 ?─) "┐\\n")',
            # Create 18 rows of water space
            "(dotimes (row 18)",
            '  (insert "│" (make-string 76 ? ) "│\\n"))',
            '(insert "└" (make-string 76 ?─) "┘\\n")',
            '(insert "\\n💧 Interactive REPL: Type commands in terminal\\n")',
            '(insert "🐠 Fish swim with real 2D physics\\n")',
            "(goto-char (point-min))",
            "(setq buffer-read-only t)",
            "(setq cursor-type nil))",
        ]

        combined_elisp = "(progn " + " ".join(elisp_commands) + ' "container-created")'

        try:
            result = subprocess.run(
                ["emacsclient", "--eval", combined_elisp],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.returncode == 0
        except Exception as e:
            print(f"❌ Container creation failed: {e}")
            return False

    def start_aquarium(self, args):
        """Start the aquarium ecosystem"""
        print("🚀 Starting Redis-coordinated aquarium...")

        # Initialize container in Redis
        container_data = {
            "width": 76,
            "height": 18,
            "boundaries": {"left": 1, "right": 75, "top": 1, "bottom": 17},
            "physics": {"current_x": 0.1, "current_y": 0.05, "viscosity": 0.9},
        }
        self.redis_client.set("aquarium:container", json.dumps(container_data))

        # Create visual container
        if self.create_water_container():
            print("✅ Water container created with proper visibility")

            # Add initial fish (start simple, build iteratively)
            if not args:
                self.add_fish(["nemo", "🐠", "orange", "25", "9"])
                print("🐠 Added starter fish 'nemo' - use 'add' to create more!")

            return True
        else:
            print("❌ Failed to create container")
            return False

    def add_fish(self, args):
        """Add fish to aquarium: add <name> <emoji> <color> [x] [y]"""
        if len(args) < 3:
            print("Usage: add <name> <emoji> <color> [x] [y]")
            print("Example: add bubbles 🐡 yellow 40 12")
            return

        name, emoji, color = args[0], args[1], args[2]

        # Default or specified position
        x = float(args[3]) if len(args) > 3 else random.uniform(10, 65)
        y = float(args[4]) if len(args) > 4 else random.uniform(3, 15)

        # Random swimming behavior
        vx = random.uniform(-0.3, 0.3)
        vy = random.uniform(-0.2, 0.2)

        fish_data = {
            "x": x,
            "y": y,
            "vx": vx,
            "vy": vy,
            "char": emoji,
            "color": color,
            "behavior": random.choice(["curious", "lazy", "energetic", "cautious"]),
            "energy": random.randint(80, 100),
        }

        self.redis_client.hset(f"aquarium:fish:{name}", mapping=fish_data)
        print(
            f"🐟 Added {emoji} '{name}' at ({x:.1f}, {y:.1f}) - {fish_data['behavior']} behavior"
        )

        # Log to Redis stream for coordination
        self.redis_client.xadd(
            "aquarium:events",
            {
                "action": "fish_added",
                "name": name,
                "emoji": emoji,
                "position": f"{x},{y}",
                "timestamp": time.time(),
            },
        )

    def remove_fish(self, args):
        """Remove fish from aquarium"""
        if not args:
            print("Usage: remove <name>")
            return

        name = args[0]
        if self.redis_client.exists(f"aquarium:fish:{name}"):
            self.redis_client.delete(f"aquarium:fish:{name}")
            print(f"🗑️  Removed fish '{name}'")

            # Log removal event
            self.redis_client.xadd(
                "aquarium:events",
                {"action": "fish_removed", "name": name, "timestamp": time.time()},
            )
        else:
            print(f"❓ Fish '{name}' not found")

    def list_fish(self, args):
        """List all fish in aquarium"""
        fish_keys = self.redis_client.keys("aquarium:fish:*")

        if not fish_keys:
            print("🏜️  No fish in aquarium")
            return

        print(f"🐠 Fish in aquarium ({len(fish_keys)} total):")
        for key in fish_keys:
            name = key.split(":")[-1]
            fish = self.redis_client.hgetall(key)
            print(
                f"  {fish['char']} {name} - {fish['color']} - ({float(fish['x']):.1f}, {float(fish['y']):.1f}) - {fish.get('behavior', 'unknown')}"
            )

    def show_status(self, args):
        """Show aquarium system status"""
        container = self.redis_client.get("aquarium:container")
        fish_count = len(self.redis_client.keys("aquarium:fish:*"))
        events_count = (
            self.redis_client.xlen("aquarium:events")
            if self.redis_client.exists("aquarium:events")
            else 0
        )

        print(f"📊 AQUARIUM STATUS:")
        print(f"   🏠 Container: {'✅ Active' if container else '❌ Not initialized'}")
        print(f"   🐟 Fish: {fish_count}")
        print(f"   📝 Events logged: {events_count}")
        print(
            f"   🎬 Animation: {'🟢 Active' if self.animation_active else '🔴 Stopped'}"
        )
        print(
            f"   🔧 Redis: {'✅ Connected' if self.redis_client.ping() else '❌ Disconnected'}"
        )

    def toggle_animation(self, args):
        """Start/stop fish animation"""
        if not self.animation_active:
            self.animation_active = True
            print("🎬 Starting fish animation...")
            self.animate_loop()
        else:
            self.animation_active = False
            print("⏸️  Stopping animation...")

    def animate_loop(self):
        """Animation loop with Redis coordination"""
        while self.animation_active:
            try:
                self.update_fish_physics()
                self.render_aquarium()
                time.sleep(0.4)
            except KeyboardInterrupt:
                self.animation_active = False
                break
            except Exception as e:
                print(f"💥 Animation error: {e}")

    def update_fish_physics(self):
        """Update fish positions using Redis state"""
        if not self.redis_client.exists("aquarium:container"):
            return

        container = json.loads(self.redis_client.get("aquarium:container"))
        bounds = container["boundaries"]
        physics = container["physics"]

        fish_keys = self.redis_client.keys("aquarium:fish:*")
        for fish_key in fish_keys:
            fish = self.redis_client.hgetall(fish_key)

            # Current physics state
            x, y = float(fish["x"]), float(fish["y"])
            vx, vy = float(fish["vx"]), float(fish["vy"])

            # Apply water physics
            vx += physics["current_x"] * 0.1 + (random.random() - 0.5) * 0.15
            vy += physics["current_y"] * 0.1 + (random.random() - 0.5) * 0.08

            # Viscosity (drag)
            vx *= physics["viscosity"]
            vy *= physics["viscosity"]

            # Update position
            new_x, new_y = x + vx, y + vy

            # Boundary collisions
            if new_x <= bounds["left"] or new_x >= bounds["right"]:
                vx = -vx * 0.8
                new_x = max(bounds["left"], min(bounds["right"], new_x))

            if new_y <= bounds["top"] or new_y >= bounds["bottom"]:
                vy = -vy * 0.8
                new_y = max(bounds["top"], min(bounds["bottom"], new_y))

            # Store updated state in Redis
            self.redis_client.hset(
                fish_key, mapping={"x": new_x, "y": new_y, "vx": vx, "vy": vy}
            )

    def render_aquarium(self):
        """Render fish positions in Emacs"""
        # Clear water space and redraw fish
        clear_commands = [
            '(with-current-buffer "*redis-aquarium*"',
            "(let ((inhibit-read-only t))",
            # Clear water area (skip borders)
            "(goto-char (+ (point-min) 78))",  # Skip header
            "(dotimes (row 18)",
            "  (forward-char 1)",  # Skip left border
            "  (delete-char 76)",  # Clear water space
            "  (insert (make-string 76 ? ))",  # Fill with water
            "  (forward-char 2))",  # Skip right border + newline
        ]

        # Add fish at their current positions
        fish_keys = self.redis_client.keys("aquarium:fish:*")
        for fish_key in fish_keys:
            fish = self.redis_client.hgetall(fish_key)
            x, y = int(float(fish["x"])), int(float(fish["y"]))
            char, color = fish["char"], fish["color"]

            clear_commands.extend(
                [
                    f"(goto-char (+ (point-min) 78 (* {y} 78) {x}))",
                    "(delete-char 1)",
                    f'(insert (propertize "{char}" \'face \'(:foreground "{color}" :weight bold)))',
                ]
            )

        clear_commands.append("))")  # Close let and with-current-buffer

        combined_elisp = "(progn " + " ".join(clear_commands) + ' "rendered")'

        try:
            subprocess.run(
                ["emacsclient", "--eval", combined_elisp],
                capture_output=True,
                text=True,
                timeout=2,
            )
        except:
            pass  # Continue animation even if render fails

    def show_physics(self, args):
        """Show physics parameters"""
        if self.redis_client.exists("aquarium:container"):
            container = json.loads(self.redis_client.get("aquarium:container"))
            physics = container["physics"]
            print(f"🌊 WATER PHYSICS:")
            print(f"   Current X: {physics['current_x']}")
            print(f"   Current Y: {physics['current_y']}")
            print(f"   Viscosity: {physics['viscosity']}")
        else:
            print("❌ No aquarium container initialized")

    def clear_aquarium(self, args):
        """Clear all fish and reset"""
        fish_keys = self.redis_client.keys("aquarium:fish:*")
        if fish_keys:
            self.redis_client.delete(*fish_keys)
            print(f"🧹 Removed {len(fish_keys)} fish")

        self.redis_client.delete("aquarium:events")
        print("🗑️  Cleared event log")

    def stop_aquarium(self, args):
        """Stop aquarium and cleanup"""
        self.animation_active = False
        keys = self.redis_client.keys("aquarium:*")
        if keys:
            self.redis_client.delete(*keys)
        print("🛑 Aquarium stopped and Redis state cleared")

    def show_help(self, args):
        """Show available commands"""
        print("\n🎮 AQUARIUM REPL COMMANDS:")
        print("  start          - Initialize aquarium container")
        print("  add <name> <emoji> <color> [x] [y] - Add fish")
        print("  remove <name>  - Remove fish")
        print("  list           - List all fish")
        print("  status         - Show system status")
        print("  animate        - Toggle fish animation")
        print("  physics        - Show water physics")
        print("  clear          - Remove all fish")
        print("  stop           - Stop and cleanup")
        print("  help           - Show this help")
        print("  quit           - Exit REPL")
        print("\n🐠 Example: add bubbles 🐡 yellow 30 8")

    def quit_repl(self, args):
        """Exit the REPL"""
        self.animation_active = False
        self.running = False
        print("👋 Goodbye! Aquarium REPL ended.")

    def run(self):
        """Main REPL loop"""
        while self.running:
            try:
                user_input = input("\n🌊 aquarium> ").strip()

                if not user_input:
                    continue

                parts = user_input.split()
                command = parts[0].lower()
                args = parts[1:] if len(parts) > 1 else []

                if command in self.commands:
                    self.commands[command](args)
                else:
                    print(f"❓ Unknown command: {command}")
                    print("Type 'help' for available commands")

            except KeyboardInterrupt:
                print("\n⏹️  Use 'quit' to exit cleanly")
            except EOFError:
                break
            except Exception as e:
                print(f"💥 Error: {e}")


if __name__ == "__main__":
    repl = AquariumREPL()
    repl.run()
