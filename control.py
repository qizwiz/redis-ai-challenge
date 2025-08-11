#!/usr/bin/env python3
"""A general-purpose script to execute Emacs Lisp code from the command line."""

import sys
import subprocess

def main():
    """Executes the main logic of the script."""
    if len(sys.argv) < 2:
        print('Usage: python control.py "(your-elisp-code)"')
        sys.exit(1)

    elisp_command = sys.argv[1]
    
    try:
        result = subprocess.run(
            ["emacsclient", "--eval", elisp_command],
            capture_output=True,
            text=True,
            timeout=10,
            check=True  # This will raise CalledProcessError for non-zero exit codes
        )
        print(f"✅ Success: {result.stdout.strip()}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed: {e.stderr.strip()}")
    except subprocess.TimeoutExpired:
        print("❌ Failed: Command timed out")
    except Exception as e:
        print(f"❌ Failed with unexpected error: {str(e)}")

if __name__ == "__main__":
    main()
