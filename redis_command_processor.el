;; -*- lexical-binding: t; -*-
;; Redis Command Processor - Execute commands from Redis streams

(defvar redis-command-processor-active nil
  "Whether command processing is active")

(defun redis-start-command-processing ()
  "Start processing commands from Redis streams"
  (interactive)
  (setq redis-command-processor-active t)
  (message "🎯 Redis command processor started")
  (redis-command-poll-loop))

(defun redis-command-poll-loop ()
  "Poll Redis for commands to execute"
  (when redis-command-processor-active
    (condition-case err
        (let ((result (shell-command-to-string 
                      "redis-cli XREAD COUNT 1 STREAMS emacs:commands $")))
          (when (and result 
                     (not (string-match-p "nil\\|(nil)" result))
                     (string-match-p "command" result))
            (redis-process-command result)))
      (error 
       (message "Redis command poll error: %s" err)))
    ;; Poll every 0.5 seconds
    (run-with-timer 0.5 nil #'redis-command-poll-loop)))

(defun redis-process-command (redis-result)
  "Process a command from Redis"
  (let ((command-data (redis-parse-command redis-result)))
    (when command-data
      (let ((action (plist-get command-data :action))
            (command (plist-get command-data :command))
            (description (plist-get command-data :description)))
        
        (message "📥 Redis command: %s (%s)" command description)
        
        (condition-case err
            (progn
              ;; Execute the keyboard command
              (execute-kbd-macro (kbd command))
              
              ;; Log success back to Redis
              (shell-command-to-string 
               (format "redis-cli XADD emacs:responses '*' action '%s' command '%s' status executed" 
                       action command))
              
              (message "✅ Executed: %s" command))
          (error 
           ;; Log error back to Redis
           (shell-command-to-string 
            (format "redis-cli XADD emacs:responses '*' action '%s' command '%s' status error message '%s'" 
                    action command (error-message-string err)))
           (message "❌ Command failed: %s" (error-message-string err))))))))

(defun redis-parse-command (redis-result)
  "Parse command data from Redis XREAD result"
  (when (string-match "action.*\\([^[:space:]]+\\)" redis-result)
    (let ((action (match-string 1 redis-result)))
      (when (string-match "command.*\\([^[:space:]]+\\)" redis-result)
        (let ((command (match-string 1 redis-result)))
          (when (string-match "description.*\\([^\"]*\\)" redis-result)
            (let ((description (match-string 1 redis-result)))
              (list :action action :command command :description description))))))))

(defun redis-stop-command-processing ()
  "Stop command processing"
  (interactive)
  (setq redis-command-processor-active nil)
  (message "⏹️ Redis command processor stopped"))

;; Start processing automatically
(redis-start-command-processing)

(provide 'redis-command-processor)