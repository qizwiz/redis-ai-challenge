;;; silent_redis_bridge.el --- Truly Reactive Redis Bridge (No Timers, No Spam)

(defvar silent-redis-process nil "Silent Redis XREAD process")
(defvar silent-redis-active nil "Bridge active status")
(defvar silent-redis-last-id "$" "Last processed message ID")

(defun silent-redis-start ()
  "Start truly reactive Redis bridge - no timers, no message spam"
  (interactive)
  
  ;; Stop any existing bridge
  (silent-redis-stop)
  
  ;; Start continuous XREAD process (blocks until data available)
  ;; Start with "0-0" for initial read, then use last ID for subsequent reads
  (setq silent-redis-last-id "0-0")
  (setq silent-redis-process
        (start-process "silent-redis" " *silent-redis*"  ; space = hidden buffer
                      "redis-cli" "XREAD" "BLOCK" "0" "STREAMS" "emacs:commands" silent-redis-last-id))
  
  ;; Set up silent process filter
  (set-process-filter silent-redis-process 'silent-redis-filter)
  (set-process-sentinel silent-redis-process 'silent-redis-sentinel)
  
  (setq silent-redis-active t)
  
  ;; Silent telemetry (no minibuffer spam)
  (call-process "redis-cli" nil nil nil "SET" "bridge:status" "SILENT_ACTIVE")
  
  ;; Only show this once
  (message "Silent Redis bridge started (no more messages)"))

(defun silent-redis-filter (process output)
  "Silent process filter - executes commands without spam"
  (when silent-redis-active
    ;; Parse multi-line Redis XREAD output
    (let ((lines (split-string output "\n" t))
          (current-id nil))
      (dolist (line lines)
        (cond
         ;; Message ID line (format: 1754765323414-0)
         ((string-match-p "^[0-9]+-[0-9]+$" line)
          (setq current-id line))
         ;; Skip stream name and field name
         ((string-match-p "^emacs:commands$\\|^elisp$" line)
          nil)  ; Do nothing
         ;; Elisp expression line
         ((string-match-p "^(" line)
          ;; Execute the elisp command silently
          (condition-case nil
              (eval (read line))
            (error nil))  ; Ignore errors silently
          
          ;; Update last processed ID
          (when current-id
            (setq silent-redis-last-id current-id))
          
          ;; Silent telemetry
          (call-process "redis-cli" nil nil nil "INCR" "bridge:executed")))))
    
    ;; Restart listener with updated last ID
    (when silent-redis-active
      (silent-redis-restart))))

(defun silent-redis-sentinel (process event)
  "Handle process events silently"
  (when (and silent-redis-active 
             (string-match "\\(finished\\|exited\\)" event))
    ;; Process died, restart it (no timer, immediate)
    (silent-redis-restart)))

(defun silent-redis-restart ()
  "Restart Redis listener immediately"
  (when silent-redis-active
    (setq silent-redis-process
          (start-process "silent-redis" " *silent-redis*"
                        "redis-cli" "XREAD" "BLOCK" "0" "STREAMS" "emacs:commands" silent-redis-last-id))
    (set-process-filter silent-redis-process 'silent-redis-filter)
    (set-process-sentinel silent-redis-process 'silent-redis-sentinel)))

(defun silent-redis-stop ()
  "Stop the silent Redis bridge"
  (interactive)
  (setq silent-redis-active nil)
  (when silent-redis-process
    (delete-process silent-redis-process)
    (setq silent-redis-process nil))
  
  ;; Silent telemetry
  (call-process "redis-cli" nil nil nil "SET" "bridge:status" "STOPPED")
  
  (message "Silent Redis bridge stopped"))

(defun silent-redis-status ()
  "Check bridge status"
  (interactive)
  (if silent-redis-active
      (message "Silent Redis bridge: ACTIVE")
    (message "Silent Redis bridge: STOPPED")))

(provide 'silent-redis-bridge)

;;; Usage:
;;; (load-file "silent_redis_bridge.el")
;;; (silent-redis-start)
;;; 
;;; Your MCP Lisp commands will now execute silently in the background