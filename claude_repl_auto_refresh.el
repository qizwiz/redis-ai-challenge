;;; claude_repl_auto_refresh.el --- Auto-refresh Claude REPL with Redis responses -*- lexical-binding: t; -*-

(defvar claude-repl-auto-timer nil
  "Timer for auto-refreshing Claude REPL responses.")

(defun claude-repl-refresh-from-redis ()
  "Refresh Claude REPL buffer with latest responses from Redis."
  (interactive)
  (let* ((redis-output (shell-command-to-string "python3 -c \"
import redis
from datetime import datetime

r = redis.Redis(host='localhost', port=6379, decode_responses=True)
try:
    responses = r.xrange('claude:responses', '-', '+')
    for msg_id, fields in responses:
        response = fields.get('response', '')
        timestamp = float(fields.get('timestamp', 0))
        dt = datetime.fromtimestamp(timestamp)
        time_str = dt.strftime('%H:%M:%S')
        print(f'[{time_str}] {response}')
        print('---RESPONSE-SEPARATOR---')
except Exception as e:
    print(f'Error: {e}')
\""))
         (response-blocks (split-string redis-output "---RESPONSE-SEPARATOR---" t)))
    
    (with-current-buffer (get-buffer-create "*Claude-REPL*")
      (let ((inhibit-read-only t))
        (erase-buffer)
        (insert "=== Claude REPL - Live from Redis ===\n\n")
        
        (dolist (block response-blocks)
          (let ((trimmed (string-trim block)))
            (when (not (string-empty-p trimmed))
              (if (string-match "\\[\\([0-9:]+\\)\\] \\(.*\\)" trimmed)
                  (let ((time-str (match-string 1 trimmed))
                        (response-text (match-string 2 trimmed)))
                    (insert (format "🤖 Claude [%s]:\n%s\n\n" time-str response-text)))
                (insert (format "%s\n\n" trimmed))))))
        
        (goto-char (point-max))))
    
    (when (get-buffer-window "*Claude-REPL*")
      (with-selected-window (get-buffer-window "*Claude-REPL*")
        (goto-char (point-max))))
    
    (message "Claude REPL refreshed with %d responses" (length response-blocks))))

(defun claude-repl-start-auto-refresh ()
  "Start auto-refreshing Claude REPL every 3 seconds."
  (interactive)
  (claude-repl-stop-auto-refresh) ; Stop any existing timer
  (setq claude-repl-auto-timer
        (run-with-timer 0 3 'claude-repl-refresh-from-redis))
  (claude-repl-refresh-from-redis) ; Refresh immediately
  (switch-to-buffer "*Claude-REPL*")
  (message "Claude REPL auto-refresh started (every 3 seconds)"))

(defun claude-repl-stop-auto-refresh ()
  "Stop auto-refreshing Claude REPL."
  (interactive)
  (when claude-repl-auto-timer
    (cancel-timer claude-repl-auto-timer)
    (setq claude-repl-auto-timer nil))
  (message "Claude REPL auto-refresh stopped"))

;; Start auto-refresh when this file is loaded
(claude-repl-start-auto-refresh)