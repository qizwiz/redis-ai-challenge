;; Fix Claude REPL buffer to display Redis responses
(require 'json)

;; Function to fetch and display Redis responses
(defun claude-repl-fetch-responses ()
  "Fetch responses from Redis claude:responses stream and display in REPL buffer"
  (interactive)
  (let* ((output (shell-command-to-string "redis-cli XRANGE claude:responses - +"))
         (lines (split-string output "\n" t))
         (responses nil))
    
    ;; Parse Redis stream output
    (let ((i 0))
      (while (< i (length lines))
        (let ((id (nth i lines)))
          (when (and (string-match "^[0-9]+-[0-9]+$" id)
                     (< (+ i 3) (length lines)))
            (let ((response-text (nth (+ i 2) lines))
                  (timestamp-text (nth (+ i 4) lines)))
              (when (and (string= (nth (+ i 1) lines) "response")
                         (string= (nth (+ i 3) lines) "timestamp"))
                (push (list id response-text timestamp-text) responses))))
          (setq i (+ i 6)))))
    
    ;; Display in Claude-REPL buffer
    (with-current-buffer (get-buffer-create "*Claude-REPL*")
      (goto-char (point-max))
      (dolist (resp (reverse responses))
        (let ((id (car resp))
              (text (cadr resp))
              (timestamp (caddr resp)))
          (insert (format "\n🤖 Claude [%s]: %s\n" 
                         (format-time-string "%H:%M:%S" 
                                           (seconds-to-time (string-to-number timestamp)))
                         text))))
      (goto-char (point-max)))
    
    (message "Fetched %d responses from Redis" (length responses))))

;; Set up automatic checking every 5 seconds
(defvar claude-repl-timer nil)

(defun claude-repl-start-auto-check ()
  "Start automatic checking for new responses"
  (interactive)
  (when claude-repl-timer
    (cancel-timer claude-repl-timer))
  (setq claude-repl-timer
        (run-with-timer 0 5 'claude-repl-fetch-responses))
  (message "Started automatic Claude response checking"))

(defun claude-repl-stop-auto-check ()
  "Stop automatic checking"
  (interactive)
  (when claude-repl-timer
    (cancel-timer claude-repl-timer)
    (setq claude-repl-timer nil))
  (message "Stopped automatic Claude response checking"))

;; Fetch responses immediately
(claude-repl-fetch-responses)
(claude-repl-start-auto-check)

(message "Claude REPL setup complete - responses will auto-update every 5 seconds")