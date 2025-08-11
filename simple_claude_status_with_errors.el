;;; simple_claude_status_with_errors.el --- Claude status with error capture, no async required

;; -*- lexical-binding: t -*-

(defvar claude-status-error-buffer "*claude-status-errors*")
(defvar claude-status-log-buffer "*claude-status-log*") 
(defvar claude-status-timer nil)
(defvar claude-original-message-function nil)

(defun claude-status-log (level message)
  "Log message with timestamp"
  (with-current-buffer (get-buffer-create claude-status-log-buffer)
    (goto-char (point-max))
    (insert (format "[%s] %s: %s\n" 
                    (format-time-string "%H:%M:%S")
                    level
                    message))
    ;; Keep log manageable
    (when (> (buffer-size) 10000)
      (goto-char (point-min))
      (delete-region (point-min) (+ (point-min) 5000)))))

(defun claude-status-error-log (error-message)
  "Log errors to separate error buffer"
  (with-current-buffer (get-buffer-create claude-status-error-buffer)
    (goto-char (point-max))
    (insert (format "[%s] ERROR: %s\n" 
                    (format-time-string "%H:%M:%S")
                    error-message))
    ;; Keep error log manageable
    (when (> (buffer-size) 5000)
      (goto-char (point-min))
      (delete-region (point-min) (+ (point-min) 2500)))))

(defun claude-status-intercept-message (original-message &rest args)
  "Intercept message function to catch errors"
  (let ((message-text (apply 'format args)))
    ;; Log errors to our error buffer
    (when (or (string-match "ERROR" message-text)
              (string-match "error" message-text)
              (string-match "Error" message-text)
              (string-match "failed" message-text)
              (string-match "Failed" message-text))
      (claude-status-error-log message-text))
    
    ;; Call original message function
    (apply original-message args)))

(defun claude-status-setup-error-capture ()
  "Setup error capture from minibuffer"
  (unless claude-original-message-function
    (setq claude-original-message-function (symbol-function 'message))
    (fset 'message 
          (lambda (&rest args)
            (apply 'claude-status-intercept-message 
                   claude-original-message-function args))))
  (claude-status-log "SETUP" "Error capture enabled"))

(defun claude-status-restore-error-capture ()
  "Restore original message function"
  (when claude-original-message-function
    (fset 'message claude-original-message-function)
    (setq claude-original-message-function nil))
  (claude-status-log "SETUP" "Error capture disabled"))

(defun claude-status-check-processes ()
  "Check Claude processes with simple shell command"
  (condition-case err
      (let ((ps-output (shell-command-to-string "ps aux | grep -E 'claude|mcp' | grep -v grep")))
        (if (string-empty-p ps-output)
            (claude-status-log "INFO" "No Claude processes found")
          (let ((process-count (length (split-string ps-output "\n" t))))
            (claude-status-log "INFO" (format "Found %d Claude/MCP processes" process-count))
            ;; Check for high CPU usage
            (when (string-match-p " [1-9][0-9]\\." ps-output) ; 10%+ CPU
              (claude-status-log "BUSY" "High CPU Claude process detected")
              (claude-status-update-titlebar "🔴 CLAUDE BUSY")
              (return t)))))
    (error 
     (claude-status-log "ERROR" (format "Process check failed: %s" (error-message-string err)))))
  nil)

(defun claude-status-check-redis ()
  "Check Redis activity with simple command"
  (condition-case err
      (let ((redis-result (shell-command-to-string "redis-cli XREVRANGE emacs:commands + - COUNT 1 2>/dev/null")))
        (if (or (string-empty-p redis-result) (string-match-p "nil" redis-result))
            (claude-status-log "DEBUG" "No recent Redis activity")
          (claude-status-log "INFO" "Recent Redis activity detected")))
    (error
     (claude-status-log "DEBUG" "Redis check failed (redis not running?)"))))

(defun claude-status-update-titlebar (status)
  "Update titlebar with status"
  (condition-case err
      (progn
        (modify-frame-parameters nil `((title . ,(format "Emacs - %s" status))))
        (claude-status-log "INFO" (format "Titlebar: %s" status)))
    (error
     (claude-status-log "ERROR" (format "Titlebar update failed: %s" (error-message-string err))))))

(defun claude-status-server-tick ()
  "Main server tick - simplified version"
  (claude-status-log "DEBUG" "Server tick...")
  
  ;; Check processes and update status
  (let ((busy (claude-status-check-processes)))
    (unless busy
      (claude-status-update-titlebar "🟢 CLAUDE READY")))
  
  ;; Check Redis activity
  (claude-status-check-redis))

(defun claude-status-start-simple-server ()
  "Start simple Claude status server with error capture"
  (interactive)
  
  ;; Stop existing
  (claude-status-stop-simple-server)
  
  ;; Setup error capture
  (claude-status-setup-error-capture)
  
  ;; Create buffers
  (with-current-buffer (get-buffer-create claude-status-log-buffer)
    (erase-buffer)
    (insert "🚀 SIMPLE CLAUDE STATUS SERVER\n")
    (insert "==============================\n\n"))
  
  (with-current-buffer (get-buffer-create claude-status-error-buffer)
    (erase-buffer)
    (insert "🚨 MINIBUFFER ERROR CAPTURE\n")
    (insert "===========================\n\n"))
  
  ;; Start timer (every 5 seconds)
  (setq claude-status-timer 
        (run-with-timer 0 5 'claude-status-server-tick))
  
  (claude-status-log "STARTUP" "Simple Claude Status Server started")
  (message "🚀 Simple Claude Status Server started with error capture")
  
  ;; Show error buffer to demonstrate capture
  (pop-to-buffer claude-status-error-buffer))

(defun claude-status-stop-simple-server ()
  "Stop simple server and restore error capture"
  (interactive)
  
  (when claude-status-timer
    (cancel-timer claude-status-timer)
    (setq claude-status-timer nil))
  
  (claude-status-restore-error-capture)
  (claude-status-log "SHUTDOWN" "Simple Claude Status Server stopped")
  
  ;; Reset titlebar
  (modify-frame-parameters nil '((title . "Emacs")))
  
  (message "⏹️ Simple Claude Status Server stopped"))

(defun claude-status-show-errors ()
  "Show captured errors"
  (interactive)
  (pop-to-buffer claude-status-error-buffer))

(defun claude-status-test-error-capture ()
  "Generate test errors to verify capture works"
  (interactive)
  (message "Testing error capture...")
  (message "ERROR: This is a test error")
  (message "Something failed miserably")
  (message "Error processing command")
  (message "Command failed with code 1")
  (message "✅ Error capture test completed"))

;; Key bindings
(global-set-key (kbd "C-c s s") 'claude-status-start-simple-server)
(global-set-key (kbd "C-c s q") 'claude-status-stop-simple-server)
(global-set-key (kbd "C-c s e") 'claude-status-show-errors)
(global-set-key (kbd "C-c s t") 'claude-status-test-error-capture)

(provide 'simple-claude-status-with-errors)

;; Usage:
;; C-c s s  - Start server with error capture
;; C-c s q  - Stop server
;; C-c s e  - Show captured errors
;; C-c s t  - Test error capture with sample errors