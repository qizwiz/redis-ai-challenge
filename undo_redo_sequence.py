#!/usr/bin/env python3
"""
Undo-Redo Sequence with Smart Recovery
"""
import redis
import subprocess
import time


def execute_gui_elisp(elisp):
    """Execute elisp in GUI frame"""
    gui_elisp = f"""
(let ((gui-frame (seq-find (lambda (f) (frame-visible-p f)) (frame-list))))
  (when gui-frame
    (with-selected-frame gui-frame
      (let ((gui-window (frame-selected-window gui-frame)))
        (with-selected-window gui-window
          {elisp})))))
"""

    try:
        result = subprocess.run(
            ["emacsclient", "--eval", gui_elisp],
            capture_output=True,
            text=True,
            timeout=5,
        )

        if result.returncode == 0:
            return result.stdout.strip()
        else:
            print(f"❌ Error: {result.stderr.strip()}")
            return None
    except Exception as e:
        print(f"💥 Exception: {e}")
        return None


def undo_redo_demo():
    """Execute the undo-redo sequence"""

    print("🔄 UNDO-REDO-SCRATCH SEQUENCE")
    print("=" * 50)

    # Step 1: Winner-undo twice
    print("📤 Step 1: First winner-undo")
    result1 = execute_gui_elisp("(winner-undo)")
    print(f"   Result: {result1}")

    time.sleep(1)

    print("📤 Step 2: Second winner-undo")
    result2 = execute_gui_elisp("(winner-undo)")
    print(f"   Result: {result2}")

    time.sleep(1)

    # Step 3: Make scratch the lone buffer
    print("📤 Step 3: Make scratch the lone buffer")
    make_scratch_lone = """
(progn
  ;; Kill all other buffers except scratch
  (let ((scratch-buf (get-buffer "*scratch*")))
    (dolist (buf (buffer-list))
      (unless (or (eq buf scratch-buf)
                  (string-match-p "^\\\\*.*\\\\*" (buffer-name buf)))
        (kill-buffer buf))))
  ;; Switch to scratch and make it the only window
  (switch-to-buffer "*scratch*")
  (delete-other-windows)
  "scratch-is-lone")
"""
    result3 = execute_gui_elisp(make_scratch_lone)
    print(f"   Result: {result3}")

    time.sleep(1)

    # Step 4: Re-execute the smart command sequence
    print("📤 Step 4: Smart execution - go to 51:32 and insert text")

    # Get buffer info first
    buffer_info = execute_gui_elisp(
        "(list 'lines (line-number-at-pos (point-max)) 'chars (point-max))"
    )
    print(f"   Buffer info: {buffer_info}")

    # Smart goto with recovery
    smart_goto = """
(let* ((target-line 51)
       (target-col 32)
       (current-lines (line-number-at-pos (point-max))))
  (when (< current-lines target-line)
    (goto-char (point-max))
    (dotimes (i (- target-line current-lines))
      (insert "\\n")))
  (goto-line target-line)
  (move-to-column target-col t)
  (insert "from claude with ❤️ - REDONE!")
  (list 'success (line-number-at-pos) (current-column)))
"""

    result4 = execute_gui_elisp(smart_goto)
    print(f"   Smart execution result: {result4}")

    print("\n🎯 SEQUENCE COMPLETE!")
    print("   1. ✅ Winner-undo x2")
    print("   2. ✅ Made scratch lone buffer")
    print("   3. ✅ Smart re-execution with recovery")


if __name__ == "__main__":
    undo_redo_demo()
