#!/usr/bin/env python3
"""
Facade Visibility Analyzer - Shows exactly what pieces of the facade we can see

This tool provides the same "eyes" that the facade gives us - comprehensive visibility
into the distributed Emacs system state through Redis.
"""

import redis
import json
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class FacadeState:
    timestamp: float
    window_count: int
    window_layout: str
    current_buffer: str
    buffer_list: List[str]
    cursor_position: int
    cursor_line: int
    cursor_column: int
    major_mode: str
    minor_modes: List[str]
    buffer_contents_hash: str
    last_command: Optional[str]
    change_source: str


@dataclass
class ChangeEvent:
    change_id: str
    timestamp: float
    source: str
    change_type: str
    change_data: Dict[str, Any]
    state_snapshot: FacadeState


class FacadeAnalyzer:
    def __init__(self, redis_host="localhost", redis_port=6379):
        self.redis = redis.Redis(
            host=redis_host, port=redis_port, decode_responses=True
        )

    def get_live_facade(self) -> Optional[FacadeState]:
        """Get current live facade state"""
        raw_state = self.redis.get("emacs:live_facade")
        if not raw_state:
            return None

        data = json.loads(raw_state)
        return FacadeState(
            timestamp=data.get("timestamp", 0),
            window_count=data.get("window_count", 0),
            window_layout=data.get("window_layout", "unknown"),
            current_buffer=data.get("current_buffer", ""),
            buffer_list=data.get("buffer_list", []),
            cursor_position=data.get("cursor_position", 0),
            cursor_line=data.get("cursor_line", 0),
            cursor_column=data.get("cursor_column", 0),
            major_mode=data.get("major_mode", ""),
            minor_modes=data.get("minor_modes", []),
            buffer_contents_hash=data.get("buffer_contents_hash", ""),
            last_command=data.get("last_command"),
            change_source=data.get("change_source", "unknown"),
        )

    def get_change_events(self, count: int = 10) -> List[ChangeEvent]:
        """Get recent change events from stream"""
        events = []

        try:
            # Get recent events from the stream
            raw_events = self.redis.xrange("emacs:change_events", "-", "+", count=count)

            for event_id, fields in raw_events:
                # Parse the change event
                change_data_raw = fields.get("change_data", "{}")
                state_snapshot_raw = fields.get("state_snapshot", "{}")

                try:
                    change_data = json.loads(change_data_raw)
                    state_data = json.loads(state_snapshot_raw)

                    state_snapshot = FacadeState(
                        timestamp=state_data.get("timestamp", 0),
                        window_count=state_data.get("window_count", 0),
                        window_layout=state_data.get("window_layout", "unknown"),
                        current_buffer=state_data.get("current_buffer", ""),
                        buffer_list=state_data.get("buffer_list", []),
                        cursor_position=state_data.get("cursor_position", 0),
                        cursor_line=state_data.get("cursor_line", 0),
                        cursor_column=state_data.get("cursor_column", 0),
                        major_mode=state_data.get("major_mode", ""),
                        minor_modes=state_data.get("minor_modes", []),
                        buffer_contents_hash=state_data.get("buffer_contents_hash", ""),
                        last_command=state_data.get("last_command"),
                        change_source=state_data.get("change_source", "unknown"),
                    )

                    events.append(
                        ChangeEvent(
                            change_id=fields.get("change_id", ""),
                            timestamp=float(fields.get("timestamp", 0)),
                            source=fields.get("source", ""),
                            change_type=fields.get("change_type", ""),
                            change_data=change_data,
                            state_snapshot=state_snapshot,
                        )
                    )

                except json.JSONDecodeError as e:
                    print(f"Failed to parse event {event_id}: {e}")
                    continue

        except Exception as e:
            print(f"Error reading change events: {e}")

        return events

    def analyze_minor_modes(self, facade: FacadeState) -> Dict[str, List[str]]:
        """Categorize minor modes into architectural groups"""
        categories = {
            "MCP Integration": [],
            "Process Supervision": [],
            "Editor Core": [],
            "Development": [],
            "UI/Display": [],
            "Git Integration": [],
            "Navigation": [],
            "Text Processing": [],
            "System Integration": [],
            "Other": [],
        }

        for mode in facade.minor_modes:
            if "mcp" in mode.lower():
                categories["MCP Integration"].append(mode)
            elif any(
                x in mode.lower() for x in ["server", "process", "timer", "async"]
            ):
                categories["Process Supervision"].append(mode)
            elif any(
                x in mode.lower()
                for x in ["evil", "vim", "helm", "company", "smartparens"]
            ):
                categories["Editor Core"].append(mode)
            elif any(x in mode.lower() for x in ["magit", "git", "vc-"]):
                categories["Git Integration"].append(mode)
            elif any(
                x in mode.lower()
                for x in ["flycheck", "projectile", "debug", "compile"]
            ):
                categories["Development"].append(mode)
            elif any(
                x in mode.lower()
                for x in ["line", "highlight", "font", "color", "display"]
            ):
                categories["UI/Display"].append(mode)
            elif any(x in mode.lower() for x in ["goto", "search", "nav", "jump"]):
                categories["Navigation"].append(mode)
            elif any(
                x in mode.lower() for x in ["text", "indent", "fill", "wrap", "spell"]
            ):
                categories["Text Processing"].append(mode)
            elif any(x in mode.lower() for x in ["auto", "global", "revert", "save"]):
                categories["System Integration"].append(mode)
            else:
                categories["Other"].append(mode)

        return categories

    def get_claude_status(self) -> str:
        """Get Claude's current status"""
        return self.redis.get("claude:status") or "unknown"

    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health metrics"""
        facade = self.get_live_facade()
        if not facade:
            return {"status": "disconnected", "facade": None}

        change_count = self.redis.xlen("emacs:change_events") or 0
        claude_status = self.get_claude_status()

        # Check for active processes (approximate)
        server_buffers = [
            b
            for b in facade.buffer_list
            if "server" in b.lower() or "process" in b.lower()
        ]

        return {
            "status": "connected",
            "facade_age": time.time() - facade.timestamp,
            "window_count": facade.window_count,
            "buffer_count": len(facade.buffer_list),
            "minor_mode_count": len(facade.minor_modes),
            "change_events": change_count,
            "claude_status": claude_status,
            "active_processes": len(server_buffers),
            "major_mode": facade.major_mode,
        }

    def print_full_analysis(self):
        """Print comprehensive facade analysis"""
        print("🔍 FACADE VISIBILITY ANALYSIS")
        print("=" * 50)

        # System Health
        health = self.get_system_health()
        print(f"\n📊 SYSTEM HEALTH:")
        print(f"  Status: {health['status']}")
        if health["status"] == "connected":
            print(f"  Facade Age: {health['facade_age']:.1f}s")
            print(f"  Windows: {health['window_count']}")
            print(f"  Buffers: {health['buffer_count']}")
            print(f"  Minor Modes: {health['minor_mode_count']}")
            print(f"  Change Events: {health['change_events']}")
            print(f"  Claude Status: {health['claude_status']}")
            print(f"  Major Mode: {health['major_mode']}")

        # Current State
        facade = self.get_live_facade()
        if not facade:
            print("\n❌ No facade data available")
            return

        print(f"\n🪟 CURRENT STATE:")
        print(f"  Timestamp: {datetime.fromtimestamp(facade.timestamp)}")
        print(f"  Layout: {facade.window_count} windows ({facade.window_layout})")
        print(f"  Current Buffer: {facade.current_buffer}")
        print(
            f"  Cursor: Line {facade.cursor_line}, Col {facade.cursor_column} (pos {facade.cursor_position})"
        )
        print(f"  Contents Hash: {facade.buffer_contents_hash}")

        # Minor Mode Analysis
        mode_categories = self.analyze_minor_modes(facade)
        print(f"\n🔧 PASSIVE SERVERS (Minor Modes):")
        for category, modes in mode_categories.items():
            if modes:
                print(f"  {category} ({len(modes)}):")
                for mode in modes[:3]:  # Show first 3
                    print(f"    • {mode}")
                if len(modes) > 3:
                    print(f"    ... and {len(modes) - 3} more")

        # Key Buffers
        important_buffers = [
            b
            for b in facade.buffer_list
            if any(
                x in b.lower() for x in ["server", "claude", "mcp", "redis", "debug"]
            )
        ]
        print(f"\n📋 KEY BUFFERS:")
        for buf in important_buffers[:10]:
            print(f"  • {buf}")

        # Recent Changes
        changes = self.get_change_events(5)
        print(f"\n📈 RECENT CHANGES:")
        for change in changes:
            dt = datetime.fromtimestamp(change.timestamp)
            print(f"  {dt.strftime('%H:%M:%S')} - {change.change_type}")
            if change.change_type == "window_count_change":
                data = change.change_data
                print(f"    {data.get('from', '?')} → {data.get('to', '?')} windows")

        print(f"\n✅ VISIBILITY STATUS: COMPLETE")
        print(
            f"We can see exactly what you see - {facade.window_count} windows, {len(facade.buffer_list)} buffers,"
        )
        print(f"{len(facade.minor_modes)} passive servers, and full change history.")


def main():
    analyzer = FacadeAnalyzer()
    analyzer.print_full_analysis()


if __name__ == "__main__":
    main()
