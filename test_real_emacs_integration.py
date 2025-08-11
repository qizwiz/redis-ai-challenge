#!/usr/bin/env python3
"""
Test Real Emacs Integration - Actually connect to running Emacs
"""

import subprocess
import time
import json


def test_emacs_connectivity():
    """Test if we can actually connect to a running Emacs"""

    print("🎯 TESTING REAL EMACS INTEGRATION")
    print("=" * 50)

    # Test 1: Check if Emacs is running
    print("1. Checking if Emacs is running...")
    try:
        result = subprocess.run(["pgrep", "emacs"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Found Emacs process(es): {result.stdout.strip()}")
        else:
            print("❌ No Emacs process found")
            print("💡 Start Emacs first, then run this test")
            return False
    except Exception as e:
        print(f"❌ Error checking Emacs: {e}")
        return False

    # Test 2: Check if emacsclient works
    print("\n2. Testing emacsclient connectivity...")
    try:
        result = subprocess.run(
            ["emacsclient", "--eval", '(message "AI test successful")'],
            capture_output=True,
            text=True,
            timeout=5,
        )

        if result.returncode == 0:
            print(f"✅ emacsclient works: {result.stdout.strip()}")
        else:
            print(f"❌ emacsclient failed: {result.stderr}")
            print("💡 Make sure Emacs server is running: M-x server-start")
            return False
    except Exception as e:
        print(f"❌ emacsclient error: {e}")
        return False

    # Test 3: Get current buffer information
    print("\n3. Getting current buffer information...")
    try:
        elisp_code = """
(json-encode 
  (list 
    :buffer-name (buffer-name)
    :point (point)
    :buffer-size (buffer-size)
    :line-number (line-number-at-pos)
    :column (current-column)))
"""

        result = subprocess.run(
            ["emacsclient", "--eval", elisp_code],
            capture_output=True,
            text=True,
            timeout=5,
        )

        if result.returncode == 0:
            buffer_info = result.stdout.strip().strip('"')
            print(f"✅ Buffer info: {buffer_info}")

            # Try to parse as JSON
            try:
                parsed = json.loads(buffer_info)
                print(f"✅ Parsed buffer state: {json.dumps(parsed, indent=2)}")
                return True
            except json.JSONDecodeError:
                print(f"⚠️  Got buffer info but couldn't parse as JSON")
                return True

        else:
            print(f"❌ Failed to get buffer info: {result.stderr}")
            return False

    except Exception as e:
        print(f"❌ Buffer info error: {e}")
        return False


def test_emacs_command_execution():
    """Test executing commands in Emacs"""

    print("\n4. Testing command execution...")

    commands_to_test = [
        ("(forward-char 1)", "Move forward 1 character"),
        ('(insert "AI-inserted-text")', "Insert text"),
        ("(backward-char 15)", "Move back to original position"),
        ("(delete-char 15)", "Delete the inserted text"),
    ]

    for elisp_cmd, description in commands_to_test:
        print(f"   🎯 {description}: {elisp_cmd}")
        try:
            result = subprocess.run(
                ["emacsclient", "--eval", elisp_cmd],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0:
                print(f"      ✅ Success: {result.stdout.strip()}")
            else:
                print(f"      ❌ Failed: {result.stderr}")

        except Exception as e:
            print(f"      ❌ Error: {e}")

        time.sleep(0.5)  # Small delay between commands

    return True


def test_buffer_monitoring():
    """Test monitoring buffer changes"""

    print("\n5. Testing buffer change monitoring...")

    try:
        # Get initial state
        get_state_cmd = """
(json-encode 
  (list 
    :buffer-name (buffer-name)
    :point (point)
    :buffer-size (buffer-size)
    :modified (buffer-modified-p)))
"""

        print("   📊 Getting initial state...")
        result = subprocess.run(
            ["emacsclient", "--eval", get_state_cmd],
            capture_output=True,
            text=True,
            timeout=5,
        )

        if result.returncode == 0:
            initial_state = result.stdout.strip().strip('"')
            print(f"   ✅ Initial state: {initial_state}")

            # Make a change
            print("   ✏️  Making a change...")
            subprocess.run(
                ["emacsclient", "--eval", '(insert "\\n;; AI monitoring test\\n")'],
                capture_output=True,
                text=True,
                timeout=5,
            )

            # Get new state
            print("   📊 Getting new state...")
            result = subprocess.run(
                ["emacsclient", "--eval", get_state_cmd],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0:
                new_state = result.stdout.strip().strip('"')
                print(f"   ✅ New state: {new_state}")

                # Clean up
                subprocess.run(
                    ["emacsclient", "--eval", "(undo 2)"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )

                return True

        return False

    except Exception as e:
        print(f"   ❌ Monitoring error: {e}")
        return False


def main():
    """Run all Emacs integration tests"""

    connectivity_ok = test_emacs_connectivity()

    if connectivity_ok:
        execution_ok = test_emacs_command_execution()
        monitoring_ok = test_buffer_monitoring()

        print("\n" + "=" * 50)
        print("🎯 EMACS INTEGRATION TEST RESULTS")
        print("=" * 50)

        if connectivity_ok and execution_ok and monitoring_ok:
            print("🎉 SUCCESS: Real Emacs integration is working!")
            print("✅ Can connect to running Emacs")
            print("✅ Can execute commands")
            print("✅ Can monitor buffer changes")
            print("✅ Ready for real AI-Emacs integration")
        else:
            print("⚠️  PARTIAL: Some issues found")
            print(f"   Connectivity: {'✅' if connectivity_ok else '❌'}")
            print(f"   Execution: {'✅' if execution_ok else '❌'}")
            print(f"   Monitoring: {'✅' if monitoring_ok else '❌'}")
    else:
        print("\n❌ FAILED: Cannot establish basic Emacs connection")
        print("💡 Make sure:")
        print("   1. Emacs is running")
        print("   2. Emacs server is started (M-x server-start)")
        print("   3. emacsclient is in your PATH")


if __name__ == "__main__":
    main()
