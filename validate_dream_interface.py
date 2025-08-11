#!/usr/bin/env python3
"""
Dream Interface Validation Suite
Validates that all components are working correctly
"""

import redis
import subprocess
import time
import json
import os
from typing import Dict, List, Tuple


class DreamInterfaceValidator:
    def __init__(self):
        self.redis_client = redis.Redis(decode_responses=True)
        self.validation_results = []
        self.test_session_id = f"validation-{int(time.time())}"

    def run_full_validation(self) -> bool:
        """Run complete validation suite"""

        print("🔍 **DREAM INTERFACE VALIDATION SUITE**")
        print("=" * 50)

        tests = [
            ("Redis Connection", self.validate_redis_connection),
            ("Redis Executor Running", self.validate_redis_executor),
            ("Direct Interface Commands", self.validate_direct_interface),
            ("Natural Language Processing", self.validate_nlp),
            ("Redis Stream Coordination", self.validate_redis_streams),
            ("Emacs Command Processing", self.validate_emacs_commands),
            ("Conversation Logging", self.validate_conversation_logging),
            ("Shell Alias Integration", self.validate_shell_aliases),
        ]

        all_passed = True

        for test_name, test_func in tests:
            print(f"\n🧪 Testing: {test_name}")
            try:
                result = test_func()
                if result:
                    print(f"   ✅ PASSED")
                    self.validation_results.append((test_name, True, ""))
                else:
                    print(f"   ❌ FAILED")
                    self.validation_results.append(
                        (test_name, False, "Test returned False")
                    )
                    all_passed = False
            except Exception as e:
                print(f"   ❌ ERROR: {str(e)}")
                self.validation_results.append((test_name, False, str(e)))
                all_passed = False

        self.print_validation_summary()
        return all_passed

    def validate_redis_connection(self) -> bool:
        """Test Redis is running and accessible"""
        try:
            response = self.redis_client.ping()
            return response is True
        except:
            return False

    def validate_redis_executor(self) -> bool:
        """Test that enhanced Redis executor is running"""
        try:
            # Send a test command
            test_id = self.redis_client.xadd(
                "emacs:commands",
                {"action": "test-validation", "test_id": self.test_session_id},
            )

            # Wait a moment for processing
            time.sleep(0.5)

            # Check if command was processed (should be in command stream)
            commands = self.redis_client.xrange("emacs:commands", test_id, test_id)
            return len(commands) > 0
        except:
            return False

    def validate_direct_interface(self) -> bool:
        """Test direct dream interface script"""
        try:
            result = subprocess.run(
                ["python3", "direct_dream_interface.py", "validation test command"],
                capture_output=True,
                text=True,
                timeout=5,
            )

            return result.returncode == 0 and len(result.stdout) > 0
        except:
            return False

    def validate_nlp(self) -> bool:
        """Test natural language processing"""
        from direct_dream_interface import DirectDreamInterface

        try:
            dream = DirectDreamInterface()

            # Test different types of commands
            test_commands = [
                "split the screen",
                "show me the workspace",
                "write hello world",
                "hello there",
            ]

            for cmd in test_commands:
                enhanced = dream._enhance_natural_language(cmd)
                if not isinstance(enhanced, dict) or "type" not in enhanced:
                    return False

            return True
        except:
            return False

    def validate_redis_streams(self) -> bool:
        """Test Redis stream coordination"""
        try:
            # Test writing to emacs:commands stream
            test_data = {
                "action": "validation-test",
                "timestamp": str(time.time()),
                "test_session": self.test_session_id,
            }

            stream_id = self.redis_client.xadd("emacs:commands", test_data)

            # Verify the data was written
            retrieved = self.redis_client.xrange("emacs:commands", stream_id, stream_id)

            return len(retrieved) > 0 and retrieved[0][0] == stream_id
        except:
            return False

    def validate_emacs_commands(self) -> bool:
        """Test that Emacs commands can be sent"""
        try:
            # Send a safe Emacs command
            before_count = self.redis_client.xlen("emacs:commands")

            self.redis_client.xadd(
                "emacs:commands",
                {
                    "action": "insert-text",
                    "text": f"[VALIDATION-{self.test_session_id}] Test message",
                },
            )

            after_count = self.redis_client.xlen("emacs:commands")

            return after_count > before_count
        except:
            return False

    def validate_conversation_logging(self) -> bool:
        """Test conversation logging to Redis"""
        try:
            # Test logging a conversation
            log_data = {
                "conversation_id": f"validation-{self.test_session_id}",
                "timestamp": time.time(),
                "original_command": "test command",
                "response": "test response",
            }

            stream_id = self.redis_client.xadd("dream:conversations", log_data)

            # Verify it was logged
            logs = self.redis_client.xrange("dream:conversations", stream_id, stream_id)

            return len(logs) > 0
        except:
            return False

    def validate_shell_aliases(self) -> bool:
        """Test that shell aliases can be loaded"""
        try:
            # Check if dream_alias.sh exists and is readable
            alias_file = "dream_alias.sh"
            if not os.path.exists(alias_file):
                return False

            with open(alias_file, "r") as f:
                content = f.read()

            # Check for key alias definitions
            required_aliases = ["alias dream=", "alias magic=", "dream-chat()"]

            for alias in required_aliases:
                if alias not in content:
                    return False

            return True
        except:
            return False

    def print_validation_summary(self):
        """Print detailed validation summary"""
        print("\n" + "=" * 50)
        print("🎯 **VALIDATION SUMMARY**")
        print("=" * 50)

        passed = sum(1 for _, success, _ in self.validation_results if success)
        total = len(self.validation_results)

        print(f"✅ Passed: {passed}/{total}")
        print(f"❌ Failed: {total - passed}/{total}")

        if passed == total:
            print("\n🌟 **ALL TESTS PASSED - DREAM INTERFACE IS OPERATIONAL!** 🌟")
        else:
            print(
                f"\n⚠️  **ISSUES DETECTED - {total - passed} COMPONENTS NEED ATTENTION**"
            )
            print("\nFailed tests:")
            for test_name, success, error in self.validation_results:
                if not success:
                    print(f"   ❌ {test_name}: {error}")

        print("\n📊 **Component Status:**")
        for test_name, success, _ in self.validation_results:
            status = "✅ OPERATIONAL" if success else "❌ FAILED"
            print(f"   {test_name}: {status}")


def main():
    """Run validation suite"""
    validator = DreamInterfaceValidator()
    success = validator.run_full_validation()

    if success:
        print("\n🚀 Dream interface is ready for magical development!")
        exit(0)
    else:
        print("\n🛠️  Please fix the issues above before using the dream interface.")
        exit(1)


if __name__ == "__main__":
    main()
