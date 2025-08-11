;;; truly_persistent_redis_bridge_fixed.el --- Fixed True Persistence

(defvar persistent-redis-process nil "Single persistent Redis XREAD process")
(defvar persistent-redis-active nil "True persistence status")
(defvar persistent-redis-last-id "$" "Stream position")

(defun persistent-redis-start ()
  "Start truly persistent Redis stream - auto-continues after execution"
  (interactive)
  
  ;; Clean start
  (persistent-redis-stop)
  (setq persistent-redis-active t)
  (setq persistent-redis-last-id "$")
  
  ;; Start initial read
  (persistent-redis-continue-reading)
  (message "Fixed persistent Redis bridge started - auto-continuing"))

(defun persistent-redis-continue-reading ()
  "Continue reading stream - called after each execution batch"
  (when persistent-redis-active
    (setq persistent-redis-process
          (start-process "persistent-redis" " *persistent-redis*"
                        "redis-cli" "-p" "6380" "XREAD" "BLOCK" "0" "STREAMS" "emacs:commands" persistent-redis-last-id))
    (set-process-filter persistent-redis-process 'persistent-redis-filter)
    (set-process-sentinel persistent-redis-process 'persistent-redis-sentinel)))

(defun persistent-redis-filter (process output)
  "Execute commands and auto-continue reading"
  (when persistent-redis-active
    (let ((lines (split-string output "\n" t))
          (current-id nil)
          (executed 0))
      (dolist (line lines)
        (cond
         ;; Track message ID
         ((string-match "^\\([0-9]+-[0-9]+\\)$" line)
          (setq current-id (match-string 1 line))
          (setq persistent-redis-last-id current-id))
         ;; Skip metadata
         ((string-match-p "^emacs:commands$\\|^elisp$" line) nil)
         ;; Execute MCP Lisp
         ((string-match-p "^(" line)
          (condition-case err
              (progn
                (eval (read line))
                (setq executed (1+ executed))
                (start-process "incr" nil "redis-cli" "INCR" "bridge:executed"))
            (error 
             (message "MCP Lisp error: %s" (error-message-string err)))))))
      
      ;; Auto-continue reading after execution
      (when (and persistent-redis-active (> executed 0))
        (run-with-timer 0.1 nil 'persistent-redis-continue-reading)))))

(defun persistent-redis-sentinel (process event)
  "Handle process completion - continue reading"
  (when (and persistent-redis-active
             (string-match "\\(finished\\|exited\\)" event))
    ;; Process finished normally after reading - continue
    (run-with-timer 0.1 nil 'persistent-redis-continue-reading)))

(defun persistent-redis-stop ()
  "Stop bridge"
  (interactive)
  (setq persistent-redis-active nil)
  (when (and persistent-redis-process (process-live-p persistent-redis-process))
    (kill-process persistent-redis-process))
  (message "Persistent bridge stopped"))

(provide 'truly-persistent-redis-bridge-fixed)