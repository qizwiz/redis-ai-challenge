;;; claude_status_server.el --- Server-first Claude status monitoring using async buffers

(require 'async)

(defvar claude-status-server-buffer "*claude-status-server*")
(defvar claude-status-log-buffer "*claude-status-log*")
(defvar claude-status-process nil)
(defvar claude-status-timer nil)
(defvar claude-status-verbose t)

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
      (when (> (buffer-size) 10000)
        (goto-char (point-min))
        (delete-region (point-min) (+ (point-min) 5000))))))

(defun claude-status-get-cpu-usage ()
  "Get Claude process CPU usage asynchronously"
  (claude-status-log "DEBUG" "Checking Claude CPU usage...")
  
  (async-start
   `(lambda ()
      (require 'json)
      (let ((result '()))
        (with-temp-buffer
          (call-process "ps" nil t nil "aux")
          (goto-char (point-min))
          (while (re-search-forward ".*claude.*" nil t)
            (let* ((line (match-string 0))
                   (parts (split-string line))
                   (cpu (when (>= (length parts) 3)
                          (string-to-number (nth 2 parts))))
                   (pid (when (>= (length parts) 2)
                         (nth 1 parts))))
              (when (and cpu pid (> cpu 0.5))
                (push (list :pid pid :cpu cpu :cmd (string-join (nthcdr 10 parts) " ")) result)))))
        result))
   
   (lambda (processes)
     (claude-status-log "INFO" (format "Found %d active Claude processes" (length processes)))
     (dolist (proc processes)
       (claude-status-log "DEBUG" 
                         (format "PID %s: %.1f%% CPU - %s" 
                                (plist-get proc :pid)
                                (plist-get proc :cpu)
                                (substring (plist-get proc :cmd) 0 (min 50 (length (plist-get proc :cmd)))))))
     (claude-status-update-titlebar-from-data processes))))

(defun claude-status-check-redis-activity ()
  "Check Redis activity asynchronously"
  (claude-status-log "DEBUG" "Checking Redis activity...")
  
  (async-start
   `(lambda ()
      (with-temp-buffer
        (let ((result (call-process "redis-cli" nil t nil "XREVRANGE" "emacs:commands" "+" "-" "COUNT" "1")))
          (if (= result 0)
              (let ((output (buffer-string)))
                (when (and output (> (length output) 5) (not (string-match "nil" output)))
                  (when (string-match "\\([0-9]+\\)-[0-9]+" output)
                    (let ((timestamp-ms (string-to-number (match-string 1 output))))
                      (/ timestamp-ms 1000)))))
            nil))))
   
   (lambda (redis-timestamp)
     (if redis-timestamp
         (let ((age (- (float-time) redis-timestamp)))
           (claude-status-log "INFO" (format "Redis activity %.1f seconds ago" age))
           (when (< age 10)
             (claude-status-log "DEBUG" "Recent Redis activity detected")))
       (claude-status-log "DEBUG" "No recent Redis activity")))))

(defun claude-status-update-titlebar-from-data (active-processes)
  "Update titlebar based on process data"
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
    (condition-case err
        (progn
          (modify-frame-parameters nil `((title . ,(format "Emacs - %s" status))))
          (claude-status-log "DEBUG" "Titlebar updated successfully"))
      (error 
       (claude-status-log "ERROR" (format "Titlebar update failed: %s" (error-message-string err)))))))

(defun claude-status-server-tick ()
  "Main server tick - check all status sources"
  (claude-status-log "DEBUG" "Server tick starting...")
  (claude-status-get-cpu-usage)
  (claude-status-check-redis-activity))

(defun claude-status-start-server ()
  "Start the Claude status server"
  (interactive)
  
  ;; Stop existing server
  (claude-status-stop-server)
  
  ;; Create log buffer
  (with-current-buffer (get-buffer-create claude-status-log-buffer)
    (erase-buffer)
    (insert "🚀 CLAUDE STATUS SERVER LOG\n")
    (insert "===========================\n\n"))
  
  ;; Create server buffer  
  (with-current-buffer (get-buffer-create claude-status-server-buffer)
    (erase-buffer)
    (insert "🚀 CLAUDE STATUS SERVER\n")
    (insert "======================\n\n")
    (insert "Server Status: RUNNING\n")
    (insert "Update Interval: 5 seconds\n")
    (insert "Verbose Logging: ON\n")
    (insert (format "Started: %s\n\n" (current-time-string)))
    (insert "Monitoring:\n")
    (insert "- Claude process CPU usage\n")
    (insert "- Redis command activity\n") 
    (insert "- Emacs titlebar updates\n\n")
    (insert "Logs available in: *claude-status-log*\n"))
  
  ;; Start timer
  (setq claude-status-timer 
        (run-with-timer 0 5 'claude-status-server-tick))
  
  (claude-status-log "STARTUP" "Claude Status Server started")
  (claude-status-log "INFO" "Update interval: 5 seconds")
  (claude-status-log "INFO" "Verbose logging enabled")
  
  (message "🚀 Claude Status Server started (check *claude-status-log* for details)")
  
  ;; Show server buffer
  (pop-to-buffer claude-status-server-buffer))

(defun claude-status-stop-server ()
  "Stop the Claude status server"
  (interactive)
  
  (when claude-status-timer
    (cancel-timer claude-status-timer)
    (setq claude-status-timer nil))
  
  (claude-status-log "SHUTDOWN" "Claude Status Server stopped")
  
  ;; Reset titlebar
  (modify-frame-parameters nil '((title . "Emacs")))
  
  (message "⏹️ Claude Status Server stopped"))

(defun claude-status-toggle-verbose ()
  "Toggle verbose logging"
  (interactive)
  (setq claude-status-verbose (not claude-status-verbose))
  (claude-status-log "CONFIG" (format "Verbose logging: %s" 
                                     (if claude-status-verbose "ON" "OFF")))
  (message "Verbose logging: %s" (if claude-status-verbose "ON" "OFF")))

(defun claude-status-show-log ()
  "Show the status log buffer"
  (interactive)
  (pop-to-buffer claude-status-log-buffer))

(defun claude-status-clear-log ()
  "Clear the status log"
  (interactive)
  (with-current-buffer claude-status-log-buffer
    (erase-buffer)
    (insert "🧹 LOG CLEARED\n")
    (insert "==============\n\n"))
  (claude-status-log "ADMIN" "Log cleared"))

;; Key bindings
(global-set-key (kbd "C-c c s") 'claude-status-start-server)
(global-set-key (kbd "C-c c q") 'claude-status-stop-server)
(global-set-key (kbd "C-c c l") 'claude-status-show-log)
(global-set-key (kbd "C-c c v") 'claude-status-toggle-verbose)
(global-set-key (kbd "C-c c c") 'claude-status-clear-log)

(provide 'claude-status-server)

;; Usage:
;; C-c c s  - Start server
;; C-c c q  - Stop server  
;; C-c c l  - Show log
;; C-c c v  - Toggle verbose logging
;; C-c c c  - Clear log