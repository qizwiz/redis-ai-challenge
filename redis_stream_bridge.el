;;; redis_stream_bridge.el --- Working Redis Stream Bridge

(defvar redis-stream-consumer-process nil "Redis stream consumer process")
(defvar redis-stream-running nil "Stream consumer status")

(defun redis-stream-bridge-start ()
  "Start the Redis stream bridge that actually works"
  (interactive)
  
  ;; Kill any existing process
  (when redis-stream-consumer-process
    (delete-process redis-stream-consumer-process))
  
  ;; Start persistent Redis stream consumer
  (setq redis-stream-consumer-process
        (start-process "redis-consumer" "*redis-stream*"
                      "redis-cli" "XREAD" "BLOCK" "0" "STREAMS" "emacs:commands" "$"))
  
  ;; Set up process filter to handle commands
  (set-process-filter redis-stream-consumer-process 'redis-stream-process-filter)
  
  ;; Report success with telemetry
  (shell-command "redis-cli SET bridge:status 'ACTIVE'")
  (shell-command (format "redis-cli SET bridge:pid '%d'" (process-id redis-stream-consumer-process)))
  (setq redis-stream-running t)
  
  (message "Redis stream bridge started - commands will now execute!"))

(defun redis-stream-process-filter (process output)
  "Process filter to handle Redis stream commands"
  (when (string-match "elisp.*\\([^}]+\\)" output)
    (let ((elisp-code (match-string 1 output)))
      ;; Clean up the command
      (setq elisp-code (replace-regexp-in-string "\\\\\"" "\"" elisp-code))
      (setq elisp-code (replace-regexp-in-string "^\\\\" "" elisp-code))
      
      ;; Execute with telemetry
      (condition-case err
          (progn
            (eval (read elisp-code))
            (shell-command (format "redis-cli LPUSH telemetry:executed '%s'" elisp-code))
            (shell-command "redis-cli INCR telemetry:success-count"))
        (error 
         (shell-command (format "redis-cli LPUSH telemetry:errors '%s'" (error-message-string err)))))))
  
  ;; Restart the consumer for next command
  (when redis-stream-running
    (run-with-timer 0.1 nil 'redis-stream-restart-consumer)))

(defun redis-stream-restart-consumer ()
  "Restart the Redis consumer for continuous listening"
  (when redis-stream-running
    (setq redis-stream-consumer-process
          (start-process "redis-consumer" "*redis-stream*"
                        "redis-cli" "XREAD" "BLOCK" "0" "STREAMS" "emacs:commands" "$"))
    (set-process-filter redis-stream-consumer-process 'redis-stream-process-filter)))

(defun redis-stream-bridge-stop ()
  "Stop the Redis stream bridge"
  (interactive)
  (setq redis-stream-running nil)
  (when redis-stream-consumer-process
    (delete-process redis-stream-consumer-process))
  (shell-command "redis-cli SET bridge:status 'STOPPED'")
  (message "Redis stream bridge stopped"))

(provide 'redis-stream-bridge)