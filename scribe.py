import sys
import subprocess

def scribe(message: str):
    """
    Writes a message to a dedicated Emacs buffer.

    Args:
        message: The string to write.
    """
    # Escape single quotes and backslashes for AppleScript
    message = message.replace("\\", "\\\\").replace("'", "'\\''")

    lisp_command = f"""
    (let ((buf (get-buffer-create "*gemini-scribe-buffer*"))) 
      (with-current-buffer buf
        (goto-char (point-max))
        (insert "{message}")
        (display-buffer buf)))
    """
    
    # Using a here-document to pass the lisp command safely
    osascript_command = [
        "osascript",
        "-l", "AppleScript",
        "-e", f'tell application "Emacs" to do shell script "emacsclient -e \\'{lisp_command}\\''"'
    ]

    try:
        subprocess.run(osascript_command, check=True, capture_output=True, text=True)
        print(f"Successfully wrote to *gemini-scribe-buffer* in Emacs.")
    except subprocess.CalledProcessError as e:
        print(f"Error executing scribe command:", file=sys.stderr)
        print(f"  STDOUT: {e.stdout}", file=sys.stderr)
        print(f"  STDERR: {e.stderr}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        scribe(" ".join(sys.argv[1:]))
    else:
        print("Usage: python3 scribe.py <message>", file=sys.stderr)
        sys.exit(1)

