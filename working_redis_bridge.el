;; -*- lexical-binding: t; -*-
;; Working Redis Bridge - Actually works

(defvar redis-bridge-process nil)
(defvar redis-bridge-active nil)

(defun redis-bridge-start ()
  "Start Redis bridge"
  (interactive)
  (when redis-bridge-process
    (delete-process redis-bridge-process))
  
  (setq redis-bridge-active t)
  (redis-bridge-poll)
  (message "🚀 Redis bridge started"))

(defun redis-bridge-poll ()
  "Poll Redis for commands"
  (when redis-bridge-active
    (let ((result (shell-command-to-string "redis-cli XREAD COUNT 1 STREAMS emacs:commands 0")))
      (when (and result (not (string-match-p "nil\\|(nil)" result)) (string-match-p "command" result))
        (redis-bridge-process-command result)))
    (run-with-timer 1.0 nil #'redis-bridge-poll)))

(defun redis-bridge-process-command (output)
  "Process command from Redis"
  (when (string-match "command[^\"]*\"\\([^\"]+\\)" output)
    (let ((cmd (match-string 1 output)))
      (message "⚡ Executing: %s" cmd)
      (condition-case err
          (progn
            (execute-kbd-macro (kbd cmd))
            (shell-command-to-string 
             (format "redis-cli XADD emacs:responses * command \"%s\" status executed timestamp %s"
                     cmd (format-time-string "%s")))
            (message "✅ Executed: %s" cmd))
        (error
         (message "❌ Error: %s" err)
         (shell-command-to-string 
          (format "redis-cli XADD emacs:responses * command \"%s\" status error error \"%s\""
                  cmd (error-message-string err))))))))

(defun redis-bridge-stop ()
  "Stop Redis bridge"
  (interactive)
  (setq redis-bridge-active nil)
  (message "⏹️ Redis bridge stopped"))

;; Start automatically
(redis-bridge-start)

(provide 'working-redis-bridge)