;; -*- lexical-binding: t; -*-
;; Redis.el Demo - Direct Redis integration using redis-cli

(defvar redis-demo-active nil
  "Whether demo is active")

(defun redis-demo-start ()
  "Start Redis demo using redis-cli"
  (interactive)
  (setq redis-demo-active t)
  (message "🚀 Redis demo started using redis-cli")
  (redis-demo-poll-loop))

(defun redis-demo-poll-loop ()
  "Poll Redis for tutorial commands using redis-cli"
  (when redis-demo-active
    (condition-case err
        (let ((result (shell-command-to-string 
                      "redis-cli XREAD COUNT 1 STREAMS tutorial:commands 0")))
          (when (and result 
                     (not (string-match-p "nil\\|(nil)" result))
                     (string-match-p "command" result))
            (redis-demo-process-command result)))
      (error 
       (message "Redis poll error: %s" err)))
    ;; Continue polling every 0.5 seconds
    (run-with-timer 0.5 nil #'redis-demo-poll-loop)))

(defun redis-demo-process-command (redis-output)
  "Process command from Redis stream output"
  ;; Parse the Redis XREAD response to extract command and description
  (when (string-match "command[^\"]*\"\\([^\"]+\\)\"" redis-output)
    (let ((command (match-string 1 redis-output))
          (description ""))
      
      ;; Try to extract description too
      (when (string-match "description[^\"]*\"\\([^\"]+\\)\"" redis-output)
        (setq description (match-string 1 redis-output)))
      
      (redis-demo-execute-command command description))))

(defun redis-demo-execute-command (command description)
  "Execute a tutorial command and report back to Redis"
  (message "⚡ Executing: %s (%s)" command description)
  
  (condition-case err
      (progn
        ;; Execute the command
        (execute-kbd-macro (kbd command))
        
        ;; Report success to Redis
        (shell-command-to-string 
         (format "redis-cli XADD tutorial:responses * command \"%s\" status executed description \"%s\" timestamp %s"
                 command description (format-time-string "%s")))
        
        (message "✅ Executed: %s" command))
    (error
     ;; Report error to Redis
     (shell-command-to-string 
      (format "redis-cli XADD tutorial:responses * command \"%s\" status error error \"%s\" timestamp %s"
              command (error-message-string err) (format-time-string "%s")))
     
     (message "❌ Error executing %s: %s" command err))))

(defun redis-demo-stop ()
  "Stop Redis demo"
  (interactive)
  (setq redis-demo-active nil)
  (message "⏹️ Redis demo stopped"))

(defun redis-demo-test-connection ()
  "Test Redis connection using redis-cli"
  (interactive)
  (let ((result (shell-command-to-string "redis-cli PING")))
    (if (string-match-p "PONG" result)
        (message "✅ Redis connection test: PONG")
      (message "❌ Redis connection failed: %s" result))))

;; Auto-start demo
(redis-demo-start)

(provide 'redis-el-demo)