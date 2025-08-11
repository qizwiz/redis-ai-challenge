;;; working_facade_executor.el --- Simple facade executor that actually works

(defvar facade-executor-timer nil "Timer for polling Redis commands")
(defvar facade-executor-last-id "$" "Last processed Redis stream ID")

(defun facade-update-state ()
  "Update facade with current real Emacs state"
  (let* ((window-count (length (window-list)))
         (current-buf (buffer-name))
         (buf-contents (buffer-string))
         (state-data (format "{\"windows\":{\"count\":%d,\"layout\":\"%s\"},\"buffers\":{\"current\":\"%s\",\"contents\":{\"%s\":\"%s\"}},\"timestamp\":%f}"
                           window-count
                           (if (> window-count 1) "split" "single")
                           current-buf
                           current-buf
                           (replace-regexp-in-string "\"" "\\\\\"" buf-contents)
                           (float-time))))
    (shell-command (format "redis-cli SET emacs:facade '%s'" state-data))
    (message "🎯 Facade updated: %d windows, buffer %s" window-count current-buf)))

(defun facade-execute-action (action text stream-id)
  "Execute action and update facade"
  (let ((result
         (condition-case err
             (cond
              ((string= action "split-window-right")
               (split-window-right)
               "🪟 Split window right - now multitasking!")
              
              ((string= action "delete-other-windows")
               (delete-other-windows)
               "✨ Focused on single window!")
              
              ((string= action "switch-to-buffer")
               (when text
                 (switch-to-buffer text)
                 (format "📂 Switched to %s!" text)))
              
              ((string= action "insert-text")
               (when text
                 (insert text)
                 (format "✍️ Inserted: %s" (substring text 0 (min 20 (length text))))))
              
              ((string= action "goto-char")
               (when (string= text "point-max")
                 (goto-char (point-max))
                 "🎯 Moved to end!"))
              
              (t (format "❓ Unknown: %s" action)))
           (error (format "❌ Error: %s" (error-message-string err))))))
    
    ;; Update facade with current state
    (facade-update-state)
    
    ;; Send response
    (when result
      (shell-command (format "redis-cli XADD emacs:responses '*' command_id '%s' result '%s' timestamp '%s'"
                           stream-id result (format-time-string "%H:%M:%S"))))
    
    (message "✅ Executed %s: %s" action result)))

(defun facade-poll-commands ()
  "Poll for Redis commands"
  (condition-case err
      (let ((result (shell-command-to-string 
                     (format "redis-cli XREAD STREAMS emacs:commands %s COUNT 1" 
                             facade-executor-last-id))))
        (when (and result (not (string-empty-p result)) (not (string-match-p "nil" result)))
          (facade-process-result result)))
    (error 
     (message "Facade executor error: %s" (error-message-string err)))))

(defun facade-process-result (redis-output)
  "Process Redis command output"
  (let ((lines (split-string redis-output "\n" t)))
    (when (>= (length lines) 4)
      (let ((stream-id (nth 1 lines))
            (action nil)
            (text nil))
        
        ;; Parse action and text
        (let ((i 2))
          (while (< i (length lines))
            (when (string= (nth i lines) "action")
              (setq action (nth (1+ i) lines)))
            (when (string= (nth i lines) "text")
              (setq text (nth (1+ i) lines)))
            (setq i (+ i 2))))
        
        ;; Execute if we have an action
        (when (and stream-id action)
          (facade-execute-action action text stream-id)
          (setq facade-executor-last-id stream-id))))))

(defun start-working-facade-executor ()
  "Start the working facade executor"
  (interactive)
  (when facade-executor-timer
    (cancel-timer facade-executor-timer))
  
  ;; Initialize facade with current state
  (facade-update-state)
  
  ;; Start polling
  (setq facade-executor-timer 
        (run-with-timer 0 0.5 'facade-poll-commands))
  
  (message "🚀 WORKING Facade Executor STARTED!"))

(defun stop-working-facade-executor ()
  "Stop the working facade executor"
  (interactive)
  (when facade-executor-timer
    (cancel-timer facade-executor-timer)
    (setq facade-executor-timer nil))
  (message "⏹️ Working Facade Executor STOPPED"))

(provide 'working-facade-executor)