#!/usr/bin/env python3
"""
Emacs Bridge - A unified, robust way to communicate with Emacs.
"""

import subprocess


class EmacsBridge:
    """A robust bridge to Emacs, using direct command injection.

    This class provides a single, reliable method for communicating with Emacs.
    It uses the `emacsclient --eval` method to directly inject Elisp commands
    and retrieve the results directly from stdout.
    """

    def __init__(self):
        pass

    def execute_command(self, command, description=""):
        """Send a command to Emacs and return the result.

        Args:
            command (str): The Emacs Lisp command to execute.
            description (str): A description of the command.

        Returns:
            str: The result of the command, or an error message.
        """
        print(f"📤 Sending to Emacs: {command} ({description})")

        try:
            result = subprocess.run(
                ["emacsclient", "-s", "redis-tutorial", "--eval", command],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                return f"Error: {result.stderr.strip()}"

        except Exception as e:
            return f"💥 Error executing command: {e}"
