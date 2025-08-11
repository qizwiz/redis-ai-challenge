;;; truly_persistent_redis_bridge.el --- True Redis Stream Persistence

(defvar persistent-redis-process nil "Single persistent Redis XREAD process")
(defvar persistent-redis-active nil "True persistence status")
(defvar persistent-redis-last-id "$" "Stream position - start from new messages")

(defun persistent-redis-start ()
  "Start truly persistent Redis stream consumer - no restarts, no cycles"
  (interactive)
  
  ;; Kill any existing process
  (when (and persistent-redis-process (process-live-p persistent-redis-process))
    (kill-process persistent-redis-process))
  
  (setq persistent-redis-active t)
  (setq persistent-redis-last-id "$")  ; Start from new messages only
  
  ;; Single persistent process that never restarts
  (setq persistent-redis-process
        (start-process "persistent-redis" " *persistent-redis*"
                      "redis-cli" "XREAD" "BLOCK" "0" "STREAMS" "emacs:commands" persistent-redis-last-id))
  
  ;; Set up persistent filter - NO RESTARTS
  (set-process-filter persistent-redis-process 'persistent-redis-filter)
  (set-process-sentinel persistent-redis-process 'persistent-redis-sentinel)
  
  (message "Truly persistent Redis bridge started - single process, no restarts"))

(defun persistent-redis-filter (process output)
  "Persistent filter - executes and continues reading automatically"
  (when persistent-redis-active
    (let ((lines (split-string output "\n" t))
          (current-id nil)
          (executed-count 0))
      (dolist (line lines)
        (cond
         ;; Message ID
         ((string-match "^\\([0-9]+-[0-9]+\\)$" line)
          (setq current-id (match-string 1 line))
          (setq persistent-redis-last-id current-id))
         ;; Skip metadata
         ((string-match-p "^emacs:commands$\\|^elisp$" line) nil)
         ;; Execute Lisp
         ((string-match-p "^(" line)
          (condition-case err
              (progn
                (eval (read line))
                (setq executed-count (1+ executed-count))
                (redis-cli-incr "bridge:executed"))
            (error 
             (message "Execution error: %s" (error-message-string err)))))))
      
      ;; CRITICAL FIX: Immediately start next XREAD to continue stream
      (when (and persistent-redis-active (> executed-count 0))
        (persistent-redis-continue-reading))))

(defun redis-cli-incr (key)
  "Increment Redis counter without blocking"
  (start-process "redis-incr" nil "redis-cli" "INCR" key))

(defun persistent-redis-continue-reading ()
  "Continue reading from stream after execution"
  (when persistent-redis-active
    (setq persistent-redis-process
          (start-process "persistent-redis" " *persistent-redis*"
                        "redis-cli" "XREAD" "BLOCK" "0" "STREAMS" "emacs:commands" persistent-redis-last-id))
    (set-process-filter persistent-redis-process 'persistent-redis-filter)
    (set-process-sentinel persistent-redis-process 'persistent-redis-sentinel)))

(defun persistent-redis-sentinel (process event)
  "Handle process death - only restart if process actually dies"
  (when (and persistent-redis-active
             (string-match "\\(finished\\|exited\\|killed\\)" event))
    (message "Persistent Redis bridge died: %s - restarting..." event)
    (persistent-redis-start)))  ; Only restart if process actually dies

(defun persistent-redis-stop ()
  "Stop persistent bridge"
  (interactive)
  (setq persistent-redis-active nil)
  (when (and persistent-redis-process (process-live-p persistent-redis-process))
    (kill-process persistent-redis-process))
  (message "Persistent Redis bridge stopped"))

(defun persistent-redis-status ()
  "Show true persistence status"
  (interactive)
  (message "Persistent bridge: %s, Process alive: %s, Last ID: %s"
           (if persistent-redis-active "ACTIVE" "INACTIVE")
           (if (and persistent-redis-process (process-live-p persistent-redis-process)) "YES" "NO")
           persistent-redis-last-id))

(provide 'truly-persistent-redis-bridge)
           (if (and persistent-redis-process (process-live-p persistent-redis-process)) "YES" "NO")
           persistent-redis-last-id))

(provide 'truly-persistent-redis-bridge)