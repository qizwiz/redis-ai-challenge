;;; facade_redis_executor.el --- Redis executor that maintains facade state

(require 'json)

(defvar redis-executor-timer nil "Timer for polling Redis commands")
(defvar redis-executor-last-id "0" "Last processed Redis stream ID")

(defun update-emacs-facade (updates)
  "Update the Emacs facade in Redis with current state"
  (let ((facade-data (json-encode updates)))
    (shell-command
     (format "redis-cli HSET emacs:facade_updates %s \'%s\'"
             (format-time-string "%s")
             facade-data))))

(defun get-current-emacs-state ()
  "Get comprehensive current Emacs state that is safe for JSON serialization."
  (list
   (cons 'timestamp (float-time))
   (cons 'windows 
         (list (cons 'count (length (window-list)))
               (cons 'layout (if (> (length (window-list)) 1) "split" "single"))
               (cons 'current_window (format "%s" (selected-window)))))
   (cons 'buffers 
         (list (cons 'current (buffer-name))
               (cons 'list (mapcar 'buffer-name (buffer-list)))
               (cons 'current_buffer_size (buffer-size))))
   (cons 'cursor 
         (list (cons 'buffer (buffer-name))
               (cons 'position (point))
               (cons 'line (line-number-at-pos))
               (cons 'column (current-column))))
   (cons 'modes 
         (list (cons 'major_mode (symbol-name major-mode))
               (cons 'minor_modes (mapcar 'symbol-name minor-mode-list))))
   (cons 'last_update (float-time))))

(defun facade-send-response (command-id result action)
  "Send response and update facade"
  (let ((response-cmd (format "redis-cli XADD emacs:responses '*' command_id '%s' result '%s' action '%s' timestamp '%s'" 
                             command-id result action (format-time-string "%H:%M:%S"))))
    (shell-command response-cmd)
    
    ;; Update facade with current state
    (let ((current-state (get-current-emacs-state)))
      (update-emacs-facade current-state))
    
    (message "📤 Response sent: %s | Facade updated" result)))

(defun facade-handle-action (action text stream-id)
  "Handle Redis action with facade updates"
  (let ((result 
         (condition-case err
             (cond
              ((string= action "split-window-right")
               (split-window-right)
               "🪟 Created new window - now split horizontally!")
              
              ((string= action "delete-other-windows")
               (delete-other-windows)
               "✨ Focused on single window - perfect for concentration!")
              
              ((string= action "other-window")
               (other-window 1)
               "↗️ Switched to other window!")
               
              ((string= action "switch-to-buffer")
               (if text
                   (progn
                     (switch-to-buffer text)
                     (format "📂 Switched to %s - workspace ready!" text))
                 "❌ Which buffer would you like to see?"))
                 
              ((string= action "insert-text")
               (if text
                   (progn
                     (unless (buffer-writable-p)
                       (with-current-buffer (current-buffer) (set-buffer-modified-p nil) (toggle-read-only)))
                     (insert text)
                     (format "✍️ Added: '%s' - content updated!" (substring text 0 (min 30 (length text)))))
                 "❌ What would you like me to write?"))
                 
              ((string= action "goto-char")
               (if (string= text "point-max")
                   (progn
                     (goto-char (point-max))
                     "🎯 Moved to end of buffer!")
                 "🎯 Position updated!"))
                 
              ((string= action "elisp-eval")
               (if text
                   (condition-case err
                       (progn
                         (eval (read text))
                         (format "⚡ Executed: %s - magic!" (substring text 0 (min 40 (length text)))))
                     (error (format "🛠️ Error: %s" (error-message-string err))))
                 "❓ What code would you like me to run?"))
                 
              (t (format "🤔 Unknown action: %s - please explain!" action)))
           (error (format "❌ Error: %s" (error-message-string err))))))
    
    ;; Send response with facade update
    (facade-send-response stream-id result action)
    (message "🎯 Executed: %s -> %s | State synchronized" action result)))

(defun facade-poll-and-execute ()
  "Poll Redis for commands and maintain facade state"
  (condition-case err
      (let ((result (shell-command-to-string 
                     (format "redis-cli XREAD STREAMS emacs:commands %s" 
                             redis-executor-last-id))))
        (when (and result (not (string-empty-p result)))
          (facade-process-commands result)))
    (error 
     (message "Redis facade executor error: %s" (error-message-string err)))))

(defun facade-process-commands (redis-output)
  "Process Redis commands and update facade"
  (let ((lines (split-string redis-output "\n" t)))
    (let ((i 0)) 
      (while (< i (length lines))
        (let ((line (nth i lines)))
          ;; Look for stream IDs
          (when (string-match "^[0-9]+-[0-9]+$" line)
            (let ((stream-id line)
                  (action nil)
                  (text nil)) 
              
              ;; Parse key-value pairs
              (setq i (1+ i))
              (while (and (< i (length lines))
                         (not (string-match "^[0-9]+-[0-9]+$" (nth i lines)))
                         (not (string-match "^emacs:" (nth i lines))))
                (let ((key (nth i lines)))
                  (when (< (1+ i) (length lines))
                    (let ((value (nth (1+ i) lines)))
                      (cond
                       ((string= key "action") (setq action value))
                       ((string= key "text") (setq text value)))
                      (setq i (+ i 2)))
                    (unless (< (1+ i) (length lines))
                      (setq i (1+ i))))))
              
              ;; Execute with facade updates
              (when action
                (facade-handle-action action text stream-id))
              
              ;; Update last processed ID
              (setq redis-executor-last-id stream-id)))
          (setq i (1+ i)))))))

(defun facade-redis-executor-start ()
  "Start facade-aware Redis executor"
  (interactive)
  (when redis-executor-timer
    (cancel-timer redis-executor-timer))
  
  ;; Initialize facade with current state
  (let ((initial-state (get-current-emacs-state)))
    (update-emacs-facade initial-state))
  
  (setq redis-executor-timer 
        (run-with-timer 0 0.5 'facade-poll-and-execute))
  
  (message "🚀 FACADE Redis Executor STARTED - state synchronization active!"))

(defun facade-redis-executor-stop ()
  "Stop facade-aware Redis executor"
  (interactive)
  (when redis-executor-timer
    (cancel-timer redis-executor-timer)
    (setq redis-executor-timer nil))
  (message "⏹️ Facade Redis Executor STOPPED"))

(defun get-facade-state ()
  "Get current facade state from Redis"
  (interactive)
  (let ((state-json (shell-command-to-string "redis-cli GET emacs:facade")))
    (when (and state-json (not (string-empty-p state-json)))
      (message "🎯 Facade State: %s" state-json))))

(provide 'facade-redis-executor)
