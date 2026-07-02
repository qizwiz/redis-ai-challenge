import unittest
import subprocess
import redis
import time
import os
import json

# Absolute path to the directory containing the scripts
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
NEUROCOMMANDER_PATH = os.path.join(SCRIPT_DIR, "neurocommander.sh")
LISP_INTERPRETER_PATH = os.path.join(SCRIPT_DIR, "redis_lisp_interpreter.py")

class TestNeuroCommanderSystem(unittest.TestCase):
    redis_client = None

    @classmethod
    def setUpClass(cls):
        """Set up a Redis client and flush the database before any tests run."""
        cls.redis_client = redis.Redis(decode_responses=True)
        cls.redis_client.flushall()
        # Ensure neurocommander is executable
        if not os.access(NEUROCOMMANDER_PATH, os.X_OK):
            subprocess.run(["chmod", "+x", NEUROCOMMANDER_PATH], check=True)

    def test_01_neurocommander_update(self):
        """Test the 'neurocommander.sh update' command."""
        result = subprocess.run([NEUROCOMMANDER_PATH, "update"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, "neurocommander update failed")
        app_count = self.redis_client.hget("neuro:windows:current", "app_count")
        self.assertIsNotNone(app_count, "app_count not set in Redis")
        self.assertGreater(int(app_count), 0, "app_count should be greater than 0")

    def test_02_neurocommander_get_frontmost(self):
        """Test the 'neurocommander.sh get frontmost_app_name' command."""
        result = subprocess.run([NEUROCOMMANDER_PATH, "get", "frontmost_app_name"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        frontmost_app = result.stdout.strip()
        self.assertGreater(len(frontmost_app), 0, "frontmost_app_name should not be empty")

    def test_03_neurocommander_deepscan(self):
        """Test the 'neurocommander.sh deepscan' command."""
        # First get the frontmost app
        frontmost_app_result = subprocess.run([NEUROCOMMANDER_PATH, "get", "frontmost_app_name"], capture_output=True, text=True)
        frontmost_app = frontmost_app_result.stdout.strip()
        self.assertGreater(len(frontmost_app), 0, "Could not get frontmost app for deepscan test")

        # Now deepscan it
        result = subprocess.run([NEUROCOMMANDER_PATH, "deepscan", frontmost_app], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, "deepscan command failed")
        self.assertGreater(len(result.stdout.strip()), 0, "deepscan should produce output")
        # Check if output is valid JSON
        try:
            json.loads(result.stdout)
        except json.JSONDecodeError:
            self.fail("deepscan output is not valid JSON")

    def test_04_lisp_interpreter(self):
        """Test the full cycle of the Lisp interpreter."""
        lisp_code = """
        (defun test-redis-write ()
          (let ((redis-cli "redis-cli"))
            (uiop:run-program (list redis-cli "SET" "lisp_test_key" "success"))))
        (test-redis-write)
        """
        lisp_file_path = os.path.join(SCRIPT_DIR, "test_lisp_temp.lisp")
        with open(lisp_file_path, "w") as f:
            f.write(lisp_code)

        # 1. Load Lisp code into Redis
        load_result = subprocess.run(["python3", LISP_INTERPRETER_PATH, "load_lisp_to_redis", "lisp:test:function", lisp_file_path], capture_output=True, text=True)
        self.assertEqual(load_result.returncode, 0, f"Failed to load Lisp to Redis: {load_result.stderr}")

        # 2. Run Lisp code from Redis
        run_result = subprocess.run(["python3", LISP_INTERPRETER_PATH, "run_lisp_from_redis", "lisp:test:function"], capture_output=True, text=True)
        self.assertEqual(run_result.returncode, 0, f"Failed to run Lisp from Redis: {run_result.stderr}")

        # 3. Verify the side effect in Redis
        value = self.redis_client.get("lisp_test_key")
        self.assertEqual(value, "success", "Lisp code did not produce the expected side effect in Redis")

        # Clean up
        os.remove(lisp_file_path)
        self.redis_client.delete("lisp:test:function", "lisp_test_key")


if __name__ == "__main__":
    unittest.main()
