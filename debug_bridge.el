;;; debug_bridge.el --- Debug the Redis bridge process

(defun debug-redis-bridge ()
  "Debug what the Redis bridge is receiving"
  (interactive)
  
  ;; Check if process exists
  (if (and (boundp 'silent-redis-process) silent-redis-process)
      (let ((proc-buffer (process-buffer silent-redis-process)))
        (if (buffer-live-p proc-buffer)
            (progn
              (switch-to-buffer proc-buffer)
              (message "Bridge process buffer shown"))
          (message "Process buffer is dead")))
    (message "No Redis bridge process running")))

(defun test-redis-stream ()
  "Test Redis stream reading directly"
  (interactive)
  (let ((output (shell-command-to-string "redis-cli XREAD STREAMS emacs:commands 0-0")))
    (switch-to-buffer "*Redis Stream Test*")
    (erase-buffer)
    (insert "Redis XREAD output:\n")
    (insert "===================\n")
    (insert output)
    (message "Stream output shown in buffer")))

(provide 'debug-bridge)