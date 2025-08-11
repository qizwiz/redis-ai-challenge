;; -*- lexical-binding: t; -*-
;; Direct State Writer - Run this in your GUI Emacs to write real state

(defun write-real-state-now ()
  "Write actual current state directly to Redis"
  (interactive)
  (let* ((buf (buffer-name))
         (pt (point))
         (ln (line-number-at-pos))
         (col (current-column))
         (ts (format-time-string "%s")))
    
    ;; Write to Redis
    (shell-command-to-string 
     (format "redis-cli SET emacs:real-current '%s'" buf))
    
    (shell-command-to-string
     (format "redis-cli HSET emacs:real-state buffer '%s' point %d line %d column %d timestamp %s"
             buf pt ln col ts))
    
    (message "📡 Real state written: %s at line %d" buf ln)))

;; Auto-write every 2 seconds
(run-with-timer 0 2 'write-real-state-now)

(provide 'direct-state-writer)