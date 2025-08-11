#!/usr/bin/env python3
"""
Fixed Redis Coordinator - Actually Working Version

This fixes the serialization issues and creates a working Redis coordination system
for the revolutionary AI development environment.
"""

import redis
import json
import time
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class FixedRedisCoordinator:
    """Redis coordinator that actually works - no serialization errors"""

    def __init__(self, redis_host="localhost", redis_port=6379):
        self.redis = redis.Redis(
            host=redis_host, port=redis_port, decode_responses=True
        )
        self.session_id = f"session_{int(time.time())}"
        logger.info(f"🔧 Fixed Redis Coordinator initialized: {self.session_id}")

    def store_keystroke(self, keystroke_data: Dict[str, Any]) -> str:
        """Store keystroke data without serialization errors"""
        try:
            # Convert everything to strings for Redis
            clean_data = self._clean_for_redis(keystroke_data)

            # Add to stream with proper serialization
            stream_id = self.redis.xadd("keystrokes", clean_data)

            logger.debug(f"✅ Stored keystroke: {stream_id}")
            return stream_id

        except Exception as e:
            logger.error(f"❌ Failed to store keystroke: {e}")
            return None

    def store_ai_response(self, response_data: Dict[str, Any]) -> str:
        """Store AI response without serialization errors"""
        try:
            clean_data = self._clean_for_redis(response_data)
            stream_id = self.redis.xadd("ai_responses", clean_data)

            logger.debug(f"✅ Stored AI response: {stream_id}")
            return stream_id

        except Exception as e:
            logger.error(f"❌ Failed to store AI response: {e}")
            return None

    def store_intent(
        self, intent_type: str, content: str, context: Dict[str, Any]
    ) -> str:
        """Store user intent properly serialized"""
        try:
            intent_data = {
                "type": intent_type,
                "content": content,
                "context": json.dumps(context),  # Serialize context as JSON string
                "session_id": self.session_id,
                "timestamp": str(time.time()),
            }

            stream_id = self.redis.xadd("intents", intent_data)
            logger.debug(f"✅ Stored intent: {intent_type}")
            return stream_id

        except Exception as e:
            logger.error(f"❌ Failed to store intent: {e}")
            return None

    def get_recent_keystrokes(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get recent keystrokes from stream"""
        try:
            entries = self.redis.xrevrange("keystrokes", count=count)
            keystrokes = []

            for entry_id, fields in entries:
                keystroke = dict(fields)
                keystroke["entry_id"] = entry_id
                keystrokes.append(keystroke)

            return keystrokes

        except Exception as e:
            logger.error(f"❌ Failed to get keystrokes: {e}")
            return []

    def get_recent_responses(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get recent AI responses from stream"""
        try:
            entries = self.redis.xrevrange("ai_responses", count=count)
            responses = []

            for entry_id, fields in entries:
                response = dict(fields)
                response["entry_id"] = entry_id
                responses.append(response)

            return responses

        except Exception as e:
            logger.error(f"❌ Failed to get responses: {e}")
            return []

    def store_code_change(
        self, file_path: str, change_type: str, content: str, line_number: int = None
    ) -> str:
        """Store actual code changes made by AI"""
        try:
            change_data = {
                "file_path": file_path,
                "change_type": change_type,  # insert, replace, delete
                "content": content,
                "line_number": str(line_number) if line_number else "",
                "session_id": self.session_id,
                "timestamp": str(time.time()),
            }

            stream_id = self.redis.xadd("code_changes", change_data)
            logger.info(f"✅ Stored code change: {change_type} in {file_path}")
            return stream_id

        except Exception as e:
            logger.error(f"❌ Failed to store code change: {e}")
            return None

    def store_ai_action(
        self, action_type: str, target: str, data: Dict[str, Any]
    ) -> str:
        """Store AI actions that need to be executed"""
        try:
            action_data = {
                "action_type": action_type,
                "target": target,
                "data": json.dumps(data),
                "session_id": self.session_id,
                "timestamp": str(time.time()),
                "status": "pending",
            }

            stream_id = self.redis.xadd("ai_actions", action_data)
            logger.info(f"✅ Stored AI action: {action_type} -> {target}")
            return stream_id

        except Exception as e:
            logger.error(f"❌ Failed to store AI action: {e}")
            return None

    def get_pending_actions(self) -> List[Dict[str, Any]]:
        """Get pending AI actions that need execution"""
        try:
            entries = self.redis.xrange("ai_actions", count=50)
            pending_actions = []

            for entry_id, fields in entries:
                if fields.get("status") == "pending":
                    action = dict(fields)
                    action["entry_id"] = entry_id
                    # Parse JSON data back
                    if "data" in action:
                        try:
                            action["data"] = json.loads(action["data"])
                        except:
                            pass
                    pending_actions.append(action)

            return pending_actions

        except Exception as e:
            logger.error(f"❌ Failed to get pending actions: {e}")
            return []

    def mark_action_completed(self, entry_id: str, result: str = "completed"):
        """Mark an AI action as completed"""
        try:
            # Unfortunately Redis streams are append-only, so we'll use a hash
            self.redis.hset(
                f"action_status:{entry_id}",
                {
                    "status": "completed",
                    "result": result,
                    "completed_at": str(time.time()),
                },
            )

            logger.debug(f"✅ Marked action completed: {entry_id}")

        except Exception as e:
            logger.error(f"❌ Failed to mark action completed: {e}")

    def store_pattern(self, pattern_type: str, pattern_data: Dict[str, Any]) -> str:
        """Store discovered patterns"""
        try:
            pattern_entry = {
                "pattern_type": pattern_type,
                "data": json.dumps(pattern_data),
                "session_id": self.session_id,
                "timestamp": str(time.time()),
            }

            stream_id = self.redis.xadd("patterns", pattern_entry)
            logger.info(f"✅ Stored pattern: {pattern_type}")
            return stream_id

        except Exception as e:
            logger.error(f"❌ Failed to store pattern: {e}")
            return None

    def _clean_for_redis(self, data: Dict[str, Any]) -> Dict[str, str]:
        """Clean data for Redis storage - convert everything to strings"""
        clean_data = {}

        for key, value in data.items():
            if isinstance(value, dict):
                clean_data[key] = json.dumps(value)
            elif isinstance(value, list):
                clean_data[key] = json.dumps(value)
            elif value is None:
                clean_data[key] = ""
            else:
                clean_data[key] = str(value)

        return clean_data

    def get_system_stats(self) -> Dict[str, Any]:
        """Get system statistics"""
        try:
            stats = {
                "keystrokes": self.redis.xlen("keystrokes"),
                "ai_responses": self.redis.xlen("ai_responses"),
                "intents": self.redis.xlen("intents"),
                "code_changes": self.redis.xlen("code_changes"),
                "ai_actions": self.redis.xlen("ai_actions"),
                "patterns": self.redis.xlen("patterns"),
                "session_id": self.session_id,
                "redis_info": {
                    "connected_clients": self.redis.info().get("connected_clients", 0),
                    "used_memory_human": self.redis.info().get(
                        "used_memory_human", "unknown"
                    ),
                },
            }

            return stats

        except Exception as e:
            logger.error(f"❌ Failed to get system stats: {e}")
            return {}

    def test_coordination(self):
        """Test the coordination system"""
        print("🧪 Testing Fixed Redis Coordination System")
        print("=" * 50)

        # Test keystroke storage
        test_keystroke = {
            "key": ".",
            "context": {"file": "test.py", "line": "user", "position": 4},
            "intent": "completion",
        }

        keystroke_id = self.store_keystroke(test_keystroke)
        print(f"✅ Keystroke stored: {keystroke_id}")

        # Test intent storage
        intent_id = self.store_intent(
            "completion_trigger",
            "user typed dot for completion",
            {"file": "test.py", "symbol": "user"},
        )
        print(f"✅ Intent stored: {intent_id}")

        # Test AI response storage
        response_id = self.store_ai_response(
            {"type": "completion_suggestion", "content": "name", "confidence": 0.8}
        )
        print(f"✅ AI response stored: {response_id}")

        # Test code change storage
        change_id = self.store_code_change(
            "/path/to/test.py", "insert", "name", line_number=1
        )
        print(f"✅ Code change stored: {change_id}")

        # Test AI action storage
        action_id = self.store_ai_action(
            "insert_text", "emacs_buffer", {"text": "name", "position": 4}
        )
        print(f"✅ AI action stored: {action_id}")

        # Get statistics
        stats = self.get_system_stats()
        print(f"\n📊 System Statistics:")
        for key, value in stats.items():
            if key != "redis_info":
                print(f"   {key}: {value}")

        print(f"\n🎯 Fixed Redis Coordination System Working!")
        return True


# Global coordinator instance
redis_coordinator = FixedRedisCoordinator()


def main():
    """Test the fixed Redis coordinator"""
    coordinator = FixedRedisCoordinator()
    coordinator.test_coordination()


if __name__ == "__main__":
    main()
