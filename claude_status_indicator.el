;;; claude_status_indicator.el --- Real utility: Show Claude availability in titlebar

(defvar claude-status-timer nil "Timer for checking Claude status")
(defvar claude-last-activity 0 "Timestamp of last Claude activity")
(defvar claude-status-indicator "🟢" "Current status indicator")

(defun claude-update-titlebar ()
  "Update the titlebar with Claude status"
  (let* ((current-time (float-time))
         (time-since-activity (- current-time claude-last-activity))
         (status-text (cond
                       ((< time-since-activity 5) "🔴 CLAUDE BUSY")
                       ((< time-since-activity 30) "🟡 CLAUDE FINISHING")
                       (t "🟢 CLAUDE READY"))))
    
    ;; Update the frame title
    (modify-frame-parameters nil `((title . ,(format "Emacs - %s" status-text))))
    
    ;; Also update mode line for visibility
    (setq claude-status-indicator status-text)
    (force-mode-line-update t)))

(defun claude-mark-activity ()
  "Mark that Claude is currently active"
  (setq claude-last-activity (float-time))
  (claude-update-titlebar))

(defun claude-check-process-activity ()
  "Check if Claude processes are running"
  (condition-case err
      (let ((claude-processes (shell-command-to-string "ps aux | grep -E 'claude|mcp' | grep -v grep | wc -l")))
        (when (and claude-processes (> (string-to-number claude-processes) 0))
          (claude-mark-activity)))
    (error nil)))

(defun claude-monitor-redis-activity ()
  "Monitor Redis for Claude command activity"
  (condition-case err
      (let ((recent-commands (shell-command-to-string "redis-cli XREVRANGE emacs:commands + - COUNT 1")))
        (when (and recent-commands 
                   (not (string-empty-p recent-commands))
                   (not (string-match-p "nil" recent-commands)))
          ;; Parse timestamp from Redis ID (format: timestamp-sequence)
          (when (string-match "\\([0-9]+\\)-[0-9]+" recent-commands)
            (let ((redis-timestamp (/ (string-to-number (match-string 1 recent-commands)) 1000)))
              (when (> redis-timestamp (- (float-time) 10)) ; Activity in last 10 seconds
                (claude-mark-activity))))))
    (error nil)))

(defun claude-status-tick ()
  "Update Claude status - called by timer"
  (claude-check-process-activity)
  (claude-monitor-redis-activity)
  (claude-update-titlebar))

(defun claude-status-start ()
  "Start monitoring Claude status"
  (interactive)
  (when claude-status-timer
    (cancel-timer claude-status-timer))
  
  (setq claude-status-timer 
        (run-with-timer 0 2 'claude-status-tick))
  
  ;; Initial update
  (claude-update-titlebar)
  (message "🔍 Claude status monitoring started"))

(defun claude-status-stop ()
  "Stop monitoring Claude status"
  (interactive)
  (when claude-status-timer
    (cancel-timer claude-status-timer)
    (setq claude-status-timer nil))
  
  ;; Reset titlebar
  (modify-frame-parameters nil '((title . "Emacs")))
  (setq claude-status-indicator "")
  (force-mode-line-update t)
  (message "⏹️ Claude status monitoring stopped"))

;; Add to mode line for additional visibility
(defvar claude-status-mode-line
  '(:eval (when claude-status-indicator
            (concat " " claude-status-indicator))))

;; Add to global mode line
(unless (member claude-status-mode-line global-mode-string)
  (setq global-mode-string 
        (append global-mode-string (list claude-status-mode-line))))

;; Auto-start when loading
(claude-status-start)

(provide 'claude-status-indicator)

;; Usage:
;; - Loads automatically and starts monitoring
;; - Titlebar shows: "Emacs - 🟢 CLAUDE READY" or "Emacs - 🔴 CLAUDE BUSY"
;; - Mode line also shows status indicator
;; - Updates every 2 seconds based on process activity and Redis commands
;; - Call (claude-status-stop) to disable