;; Enhanced Redis Command Executor - Full bidirectional communication
;; Handles commands AND sends responses for dream interface

(defvar redis-executor-timer nil "Timer for polling Redis commands")
(defvar redis-executor-last-id "0" "Last processed Redis stream ID")

(defun redis-executor-send-response (command-id result)
  "Send response back to Redis responses stream"
  (let ((response-cmd (format "redis-cli XADD emacs:responses '*' command_id '%s' result '%s' timestamp '%s'"
                             command-id result (format-time-string "%H:%M:%S"))))
    (shell-command response-cmd)
    (message "📤 Response sent: %s" result)))

(defun redis-executor-handle-action (action text stream-id)
  "Handle Redis action with proper response"
  (let ((result 
         (condition-case err
             (cond
              ((string= action "delete-other-windows")
               (delete-other-windows)
               "✨ Focused on this window - perfect for deep work!")
              
              ((string= action "split-window-right") 
               (split-window-right)
               "🪟 Created a new window to the right - ready for multitasking!")
              
              ((string= action "other-window")
               (other-window 1)
               "↗️ Moved to the other window - seamless navigation!")
               
              ((string= action "switch-to-buffer")
               (if text
                   (progn
                     (switch-to-buffer text)
                     (format "📂 Now viewing %s - your workspace is ready!" text))
                 "❌ Which buffer would you like to see?"))
                 
              ((string= action "insert-text")
               (if text
                   (progn
                     (insert text)
                     (format "✍️ Added your text: '%s...' - looking good!" (substring text 0 (min 30 (length text)))))
                 "❌ What would you like me to write?"))
                 
              ((string= action "autonomous-insert")
               (if text
                   (let ((target-buffer (get-buffer "*AI-Workspace*")))
                     (if target-buffer
                         (with-current-buffer target-buffer
                           (goto-char (point-max))
                           (insert text)
                           (format "🤖 I've added some insights: %s" (substring text 0 (min 30 (length text)))))
                       "❌ Let me create the AI workspace first"))
                 "❌ No insights to share right now"))
                 
              ((string= action "goto-char")
               (if (string= text "point-max")
                   (progn
                     (goto-char (point-max))
                     "🎯 Jumped to the end - ready for new content!")
                 "🎯 Moved to new position - where shall we go next?"))
                 
              ((string= action "elisp-eval")
               (if text
                   (condition-case err
                       (progn
                         (eval (read text))
                         (format "⚡ Executed: %s - magic happening!" (substring text 0 (min 40 (length text)))))
                     (error (format "🛠️ Oops! Error: %s - let me help fix that" (error-message-string err))))
                 "❓ What code would you like me to run?"))
                 
              (t (format "🤔 I'm not sure about '%s' - can you explain what you'd like me to do?" action)))
           (error (format "❌ Error: %s" (error-message-string err))))))
    
    (redis-executor-send-response stream-id result)
    (message "🎯 Executed: %s -> %s" action result)))

(defun redis-executor-poll-and-execute ()
  "Poll Redis for new commands and execute them with responses"
  (condition-case err
      (let ((result (shell-command-to-string 
                     (format "redis-cli XREAD STREAMS emacs:commands %s" 
                             redis-executor-last-id))))
        (when (and result (not (string-empty-p result)))
          (redis-executor-process-commands result)))
    (error 
     (message "Redis executor error: %s" (error-message-string err)))))

(defun redis-executor-process-commands (redis-output)
  "Process Redis command output and execute commands with responses"
  (let ((lines (split-string redis-output "\\n" t)))
    (let ((i 0))
      (while (< i (length lines))
        (let ((line (nth i lines)))
          ;; Look for stream IDs (format: 1234567890-0)
          (when (string-match "^[0-9]+-[0-9]+$" line)
            (let ((stream-id line)
                  (action nil)
                  (text nil)
                  (target nil))
              
              ;; Parse the key-value pairs after the stream ID
              (setq i (1+ i))
              (while (and (< i (length lines))
                         (not (string-match "^[0-9]+-[0-9]+$" (nth i lines)))
                         (not (string-match "^emacs:" (nth i lines))))
                (let ((key (nth i lines)))
                  (when (< (1+ i) (length lines))
                    (let ((value (nth (1+ i) lines)))
                      (cond
                       ((string= key "action") (setq action value))
                       ((string= key "text") (setq text value))
                       ((string= key "target") (setq target value)))
                      (setq i (+ i 2))))
                  (unless (< (1+ i) (length lines))
                    (setq i (1+ i)))))
              
              ;; Use target as text if no text specified (for buffer switching)
              (when (and target (not text))
                (setq text target))
              
              ;; Execute the command with response
              (when action
                (redis-executor-handle-action action text stream-id))
              
              ;; Update last processed ID
              (setq redis-executor-last-id stream-id)))
          (setq i (1+ i)))))))

(defun enhanced-redis-executor-start ()
  "Start the enhanced Redis command executor with bidirectional communication"
  (interactive)
  (when redis-executor-timer
    (cancel-timer redis-executor-timer))
  
  (setq redis-executor-timer 
        (run-with-timer 0 0.5 'redis-executor-poll-and-execute))
  
  (message "🚀 Enhanced Redis Executor STARTED - bidirectional communication active"))

(defun enhanced-redis-executor-stop ()
  "Stop the enhanced Redis command executor"
  (interactive)
  (when redis-executor-timer
    (cancel-timer redis-executor-timer)
    (setq redis-executor-timer nil))
  (message "⏹️ Enhanced Redis Executor STOPPED"))

(provide 'enhanced-redis-executor)