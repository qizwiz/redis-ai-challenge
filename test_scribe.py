import unittest
import subprocess
import os

class TestScribe(unittest.TestCase):

    def _get_emacs_buffer_content(self, buffer_name):
        """Helper function to read the content of an Emacs buffer."""
        lisp = f'(with-current-buffer "{buffer_name}" (buffer-string))'
        # The emacsclient command needs to be properly escaped for the shell
        command = f'emacsclient -e \'{lisp}\''
        
        try:
            result = subprocess.run(
                ["osascript", "-e", f'tell application \"Emacs\" to do shell script \"{command}\"'],
                capture_output=True, text=True, check=True
            )
            # emacsclient output includes quotes, so we strip them
            return result.stdout.strip().strip('"')
        except subprocess.CalledProcessError as e:
            self.fail(f"Failed to get Emacs buffer content. STDERR: {e.stderr}")

    def test_scribe_writes_every_character(self):
        """
        Tests that scribe.py writes the exact message, character for character,
        into the designated Emacs buffer.
        """
        # 1. Define a complex test message
        test_message = "Hello, World! This is a test with symbols: !@#$%^&*()_+-=[]{};':\",./<>? and newlines.\n...and even 'single quotes' and \\backslashes\\."
        scribe_script_path = os.path.join(os.path.dirname(__file__), "scribe.py")
        buffer_name = "*gemini-scribe-buffer*"

        # 2. Call scribe.py to write the message
        try:
            subprocess.run(["python3", scribe_script_path, test_message], check=True)
        except subprocess.CalledProcessError as e:
            self.fail(f"scribe.py failed to execute. STDERR: {e.stderr}")

        # 3. Read the content directly from the Emacs buffer
        actual_content = self._get_emacs_buffer_content(buffer_name)
        
        # 4. Assert that the content is an exact match
        self.assertEqual(test_message, actual_content, "The content in the Emacs buffer does not match the message sent by the scribe.")

if __name__ == "__main__":
    unittest.main()