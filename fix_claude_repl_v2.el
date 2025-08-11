;;; fix_claude_repl_v2.el --- Fix Claude REPL buffer -*- lexical-binding: t; -*-

;; Function to fetch and display Redis responses
(defun claude-repl-fetch-responses ()
  "Fetch responses from Redis claude:responses stream and display in REPL buffer"
  (interactive)
  (let* ((output (shell-command-to-string "redis-cli XRANGE claude:responses - +"))
         (lines (split-string output "\n"))
         (responses nil)
         (current-id nil)
         (current-response nil)
         (current-timestamp nil)
         (in-response nil))
    
    ;; Parse Redis stream output line by line
    (dolist (line lines)
      (cond
       ;; Check if this is a message ID line
       ((string-match "^[0-9]+-[0-9]+$" line)
        ;; Save previous response if we have one
        (when (and current-id current-response current-timestamp)
          (push (list current-id current-response current-timestamp) responses))
        ;; Start new response
        (setq current-id line
              current-response nil
              current-timestamp nil
              in-response nil))
       
       ;; Check for field names
       ((string= line "response")
        (setq in-response t))
       ((string= line "timestamp")
        (setq in-response nil))
       ((string= line "from")
        (setq in-response nil))
       ((string= line "message_id")
        (setq in-response nil))
       
       ;; Collect response content or timestamp
       ((and current-id (not (string= line "")))
        (cond
         (in-response
          (if current-response
              (setq current-response (concat current-response "\n" line))
            (setq current-response line)))
         ((and (not in-response) (not current-timestamp) (string-match "^[0-9]+\\." line))
          (setq current-timestamp line))))))
    
    ;; Save the last response
    (when (and current-id current-response current-timestamp)
      (push (list current-id current-response current-timestamp) responses))
    
    ;; Display in Claude-REPL buffer
    (when responses
      (with-current-buffer (get-buffer-create "*Claude-REPL*")
        (let ((inhibit-read-only t))
          (goto-char (point-max))
          (dolist (resp (reverse responses))
            (let ((id (car resp))
                  (text (cadr resp))
                  (timestamp (caddr resp)))
              (insert (format "\n🤖 Claude [%s]: %s\n\n" 
                             (format-time-string "%H:%M:%S" 
                                               (seconds-to-time (string-to-number timestamp)))
                             text))))
          (goto-char (point-max)))
        (when (get-buffer-window "*Claude-REPL*")
          (with-selected-window (get-buffer-window "*Claude-REPL*")
            (goto-char (point-max))))))
    
    (message "Fetched %d responses from Redis" (length responses))))

;; Set up automatic checking every 5 seconds
(defvar claude-repl-timer nil)

(defun claude-repl-start-auto-check ()
  "Start automatic checking for new responses"
  (interactive)
  (when claude-repl-timer
    (cancel-timer claude-repl-timer))
  (setq claude-repl-timer
        (run-with-timer 0 2 'claude-repl-fetch-responses))
  (message "Started automatic Claude response checking every 2 seconds"))

(defun claude-repl-stop-auto-check ()
  "Stop automatic checking"
  (interactive)
  (when claude-repl-timer
    (cancel-timer claude-repl-timer)
    (setq claude-repl-timer nil))
  (message "Stopped automatic Claude response checking"))

;; Clear the buffer first
(with-current-buffer (get-buffer-create "*Claude-REPL*")
  (let ((inhibit-read-only t))
    (erase-buffer)
    (insert "=== Claude REPL - Responses from Redis ===\n")))

;; Fetch responses immediately
(claude-repl-fetch-responses)
(claude-repl-start-auto-check)

;; Switch to the buffer to show it
(switch-to-buffer "*Claude-REPL*")

(message "Claude REPL setup complete - responses will auto-update every 2 seconds")