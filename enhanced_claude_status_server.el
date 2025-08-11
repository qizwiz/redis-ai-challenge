;;; enhanced_claude_status_server.el --- Enhanced server with minibuffer error capture

(require 'async)

(defvar claude-status-server-buffer "*claude-status-server*")
(defvar claude-status-log-buffer "*claude-status-log*")
(defvar claude-status-error-buffer "*claude-status-errors*")
(defvar claude-status-process nil)
(defvar claude-status-timer nil)
(defvar claude-status-verbose t)
(defvar claude-status-original-message-function nil)

(defun claude-status-log (level message)
  "Log message to status log buffer with timestamp"
  (when claude-status-verbose
    (with-current-buffer (get-buffer-create claude-status-log-buffer)
      (goto-char (point-max))
      (insert (format "[%s] %s: %s\n" 
                      (format-time-string "%H:%M:%S")
                      level
                      message))
      ;; Keep log size manageable
      (when (> (buffer-size) 20000)
        (goto-char (point-min))
        (delete-region (point-min) (+ (point-min) 10000))))))

(defun claude-status-error-log (error-message)
  "Log errors to separate error buffer"
  (with-current-buffer (get-buffer-create claude-status-error-buffer)
    (goto-char (point-max))
    (insert (format "[%s] ERROR: %s\n" 
                    (format-time-string "%H:%M:%S")
                    error-message))
    ;; Keep error log manageable
    (when (> (buffer-size) 10000)
      (goto-char (point-min))
      (delete-region (point-min) (+ (point-min) 5000)))))

(defun claude-status-intercept-message (original-message &rest args)
  "Intercept message function to catch errors"
  (let ((message-text (apply 'format args)))
    ;; Log errors to our error buffer
    (when (or (string-match "ERROR" message-text)
              (string-match "error" message-text)
              (string-match "Error" message-text))
      (claude-status-error-log message-text))
    
    ;; Call original message function
    (apply original-message args)))

(defun claude-status-setup-error-capture ()
  "Setup error capture from minibuffer"
  (unless claude-status-original-message-function
    (setq claude-status-original-message-function (symbol-function 'message))
    (fset 'message 
          (lambda (&rest args)
            (apply 'claude-status-intercept-message 
                   claude-status-original-message-function args))))
  (claude-status-log "SETUP" "Error capture enabled"))

(defun claude-status-restore-error-capture ()
  "Restore original message function"
  (when claude-status-original-message-function
    (fset 'message claude-status-original-message-function)
    (setq claude-status-original-message-function nil))
  (claude-status-log "SETUP" "Error capture disabled"))

(defun claude-status-get-cpu-usage ()
  "Get Claude process CPU usage asynchronously with better error handling"
  (claude-status-log "DEBUG" "Checking Claude CPU usage...")
  
  (async-start
   `(lambda ()
      (condition-case err
          (let ((result '()))
            (with-temp-buffer
              (let ((exit-code (call-process "ps" nil t nil "aux")))
                (if (= exit-code 0)
                    (progn
                      (goto-char (point-min))
                      (while (re-search-forward ".*claude.*" nil t)
                        (let* ((line (match-string 0))
                               (parts (split-string line))
                               (cpu (when (>= (length parts) 3)
                                      (condition-case nil
                                          (string-to-number (nth 2 parts))
                                        (error 0))))
                               (pid (when (>= (length parts) 2)
                                     (nth 1 parts))))
                          (when (and cpu pid (> cpu 0.5))
                            (push (list :pid pid :cpu cpu 
                                       :cmd (string-join (nthcdr 10 parts) " ")) result)))))
                  (list :error (format "ps command failed with exit code %d" exit-code)))))
            result)
        (error (list :error (format "Exception in CPU check: %s" err)))))
   
   (lambda (result)
     (if (plist-get result :error)
         (claude-status-log "ERROR" (format "CPU check failed: %s" (plist-get result :error)))
       (progn
         (claude-status-log "INFO" (format "Found %d active Claude processes" (length result)))
         (dolist (proc result)
           (claude-status-log "DEBUG" 
                             (format "PID %s: %.1f%% CPU - %s" 
                                    (plist-get proc :pid)
                                    (plist-get proc :cpu)
                                    (substring (or (plist-get proc :cmd) "unknown") 0 
                                              (min 50 (length (or (plist-get proc :cmd) "unknown")))))))
         (claude-status-update-titlebar-from-data result))))))

(defun claude-status-check-redis-activity ()
  "Check Redis activity asynchronously with better error handling"
  (claude-status-log "DEBUG" "Checking Redis activity...")
  
  (async-start
   `(lambda ()
      (condition-case err
          (with-temp-buffer
            (let ((exit-code (call-process "redis-cli" nil t nil "XREVRANGE" "emacs:commands" "+" "-" "COUNT" "1")))
              (if (= exit-code 0)
                  (let ((output (buffer-string)))
                    (if (and output (> (length output) 5) (not (string-match "nil" output)))
                        (when (string-match "\\([0-9]+\\)-[0-9]+" output)
                          (let ((timestamp-ms (string-to-number (match-string 1 output))))
                            (/ timestamp-ms 1000)))
                      nil))
                (list :error (format "redis-cli failed with exit code %d" exit-code)))))
        (error (list :error (format "Exception in Redis check: %s" err)))))
   
   (lambda (result)
     (cond
      ((plist-get result :error)
       (claude-status-log "ERROR" (format "Redis check failed: %s" (plist-get result :error))))
      ((numberp result)
       (let ((age (- (float-time) result)))
         (claude-status-log "INFO" (format "Redis activity %.1f seconds ago" age))))
      (t
       (claude-status-log "DEBUG" "No recent Redis activity"))))))

(defun claude-status-update-titlebar-from-data (active-processes)
  "Update titlebar based on process data with error handling"
  (condition-case err
      (let* ((high-cpu-procs (seq-filter (lambda (p) (> (plist-get p :cpu) 5.0)) active-processes))
             (status (cond
                      ((> (length high-cpu-procs) 0) "🔴 CLAUDE BUSY")
                      ((> (length active-processes) 0) "🟡 CLAUDE IDLE") 
                      (t "🟢 CLAUDE READY"))))
        
        (claude-status-log "INFO" (format "Status: %s (%d processes, %d high-CPU)" 
                                  status 
                                  (length active-processes)
                                  (length high-cpu-procs)))
        
        ;; Update titlebar
        (modify-frame-parameters nil `((title . ,(format "Emacs - %s" status))))
        (claude-status-log "DEBUG" "Titlebar updated successfully"))
    (error 
     (claude-status-log "ERROR" (format "Titlebar update failed: %s" (error-message-string err))))))

(defun claude-status-server-tick ()
  "Main server tick with comprehensive error handling"
  (condition-case err
      (progn
        (claude-status-log "DEBUG" "Server tick starting...")
        (claude-status-get-cpu-usage)
        (claude-status-check-redis-activity))
    (error
     (claude-status-log "ERROR" (format "Server tick failed: %s" (error-message-string err))))))

(defun claude-status-start-enhanced-server ()
  "Start the enhanced Claude status server with error capture"
  (interactive)
  
  ;; Stop existing server
  (claude-status-stop-enhanced-server)
  
  ;; Setup error capture
  (claude-status-setup-error-capture)
  
  ;; Create buffers
  (with-current-buffer (get-buffer-create claude-status-log-buffer)
    (erase-buffer)
    (insert "🚀 ENHANCED CLAUDE STATUS SERVER LOG\n")
    (insert "====================================\n\n"))
  
  (with-current-buffer (get-buffer-create claude-status-error-buffer)
    (erase-buffer)
    (insert "🚨 CLAUDE STATUS ERROR LOG\n")
    (insert "==========================\n\n"))
  
  (with-current-buffer (get-buffer-create claude-status-server-buffer)
    (erase-buffer)
    (insert "🚀 ENHANCED CLAUDE STATUS SERVER\n")
    (insert "================================\n\n")
    (insert "Server Status: RUNNING\n")
    (insert "Update Interval: 5 seconds\n")
    (insert "Verbose Logging: ON\n")
    (insert "Error Capture: ENABLED\n")
    (insert (format "Started: %s\n\n" (current-time-string)))
    (insert "Buffers:\n")
    (insert "- *claude-status-log* - Detailed logs\n")
    (insert "- *claude-status-errors* - Error capture\n")
    (insert "- *claude-status-server* - Server status\n"))
  
  ;; Start timer
  (setq claude-status-timer 
        (run-with-timer 0 5 'claude-status-server-tick))
  
  (claude-status-log "STARTUP" "Enhanced Claude Status Server started")
  (claude-status-log "INFO" "Error capture enabled")
  
  (message "🚀 Enhanced Claude Status Server started")
  (pop-to-buffer claude-status-server-buffer))

(defun claude-status-stop-enhanced-server ()
  "Stop the enhanced server and restore error capture"
  (interactive)
  
  (when claude-status-timer
    (cancel-timer claude-status-timer)
    (setq claude-status-timer nil))
  
  (claude-status-restore-error-capture)
  (claude-status-log "SHUTDOWN" "Enhanced Claude Status Server stopped")
  
  ;; Reset titlebar
  (modify-frame-parameters nil '((title . "Emacs")))
  
  (message "⏹️ Enhanced Claude Status Server stopped"))

(defun claude-status-show-errors ()
  "Show the error capture buffer"
  (interactive)
  (pop-to-buffer claude-status-error-buffer))

(provide 'enhanced-claude-status-server)

;; Usage:
;; (claude-status-start-enhanced-server) - Start with error capture
;; (claude-status-stop-enhanced-server)  - Stop and restore
;; (claude-status-show-errors)           - Show captured errors