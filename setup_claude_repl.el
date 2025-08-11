;;; setup_claude_repl.el --- Setup Claude REPL with Redis integration -*- lexical-binding: t; -*-

;;; Commentary:
;; This script fixes the *Claude-REPL* buffer to display responses from Redis
;; and sets up automatic checking for new responses.

;;; Code:

(defvar claude-repl-timer nil
  "Timer for checking Redis responses.")

(defvar claude-repl-last-processed-id "0-0"
  "Last processed message ID to avoid duplicates.")

(defun claude-repl-display-responses ()
  "Fetch and display new responses from Redis claude:responses stream."
  (interactive)
  (condition-case err
      (let* ((cmd (format "python3 -c \"
import redis
from datetime import datetime
import sys

r = redis.Redis(host='localhost', port=6379, decode_responses=True)
try:
    # Get all responses after the last processed ID
    responses = r.xrange('claude:responses', '%s', '+')
    if not responses:
        sys.exit(0)
    
    for msg_id, fields in responses:
        if msg_id != '%s':  # Skip the last processed ID itself
            response = fields.get('response', '')
            timestamp = float(fields.get('timestamp', 0))
            dt = datetime.fromtimestamp(timestamp)
            time_str = dt.strftime('%%H:%%M:%%S')
            print(f'ID:{msg_id}')
            print(f'TIME:{time_str}')
            print(f'RESPONSE:{response}')
            print('---END-RESPONSE---')
except Exception as e:
    print(f'ERROR:{e}', file=sys.stderr)
\"" claude-repl-last-processed-id claude-repl-last-processed-id))
             (output (shell-command-to-string cmd))
             (blocks (split-string output "---END-RESPONSE---" t))
             (new-responses 0))
        
        (when (and output (not (string-empty-p (string-trim output))))
          (with-current-buffer (get-buffer-create "*Claude-REPL*")
            (let ((inhibit-read-only t))
              ;; Ensure buffer exists and has header if empty
              (when (= (point-max) 1)
                (insert "=== Claude REPL - Live Responses from Redis ===\n\n"))
              
              (goto-char (point-max))
              
              (dolist (block blocks)
                (let ((lines (split-string (string-trim block) "\n")))
                  (when (>= (length lines) 3)
                    (let ((id-line (nth 0 lines))
                          (time-line (nth 1 lines))
                          (response-lines (nthcdr 2 lines)))
                      (when (and (string-prefix-p "ID:" id-line)
                                 (string-prefix-p "TIME:" time-line)
                                 (string-prefix-p "RESPONSE:" (nth 0 response-lines)))
                        (let ((msg-id (substring id-line 3))
                              (time-str (substring time-line 5))
                              (response-text (mapconcat 'identity 
                                                      (cons (substring (nth 0 response-lines) 9)
                                                            (cdr response-lines))
                                                      "\n")))
                          (insert (format "🤖 Claude [%s]: %s\n\n" time-str response-text))
                          (setq claude-repl-last-processed-id msg-id)
                          (setq new-responses (1+ new-responses))))))))
              
              (goto-char (point-max))))
          
          ;; Show the buffer if it has a window
          (when (and (> new-responses 0) (get-buffer-window "*Claude-REPL*"))
            (with-selected-window (get-buffer-window "*Claude-REPL*")
              (goto-char (point-max))))
          
          (when (> new-responses 0)
            (message "Added %d new Claude responses" new-responses))))
    
    (error (message "Error fetching Claude responses: %s" (error-message-string err)))))

(defun claude-repl-start ()
  "Start the Claude REPL system with auto-refresh."
  (interactive)
  ;; Stop any existing timer
  (when claude-repl-timer
    (cancel-timer claude-repl-timer))
  
  ;; Create and show the buffer
  (with-current-buffer (get-buffer-create "*Claude-REPL*")
    (let ((inhibit-read-only t))
      (erase-buffer)
      (insert "=== Claude REPL - Live Responses from Redis ===\n\n")
      (insert "Checking for responses...\n\n")))
  
  ;; Switch to the buffer
  (switch-to-buffer "*Claude-REPL*")
  
  ;; Reset last processed ID to get all responses
  (setq claude-repl-last-processed-id "0-0")
  
  ;; Fetch responses immediately
  (claude-repl-display-responses)
  
  ;; Set up timer to check every 2 seconds
  (setq claude-repl-timer
        (run-with-timer 0 2 'claude-repl-display-responses))
  
  (message "Claude REPL started - monitoring Redis responses every 2 seconds"))

(defun claude-repl-stop ()
  "Stop the Claude REPL auto-refresh."
  (interactive)
  (when claude-repl-timer
    (cancel-timer claude-repl-timer)
    (setq claude-repl-timer nil))
  (message "Claude REPL auto-refresh stopped"))

;; Start the system immediately
(claude-repl-start)

(provide 'setup-claude-repl)
;;; setup_claude_repl.el ends here