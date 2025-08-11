;; -*- lexical-binding: t; -*-
;; Redis Command Executor - The missing piece that actually executes Redis commands in Emacs

(defvar redis-executor-timer nil
  "Timer for polling Redis commands")

(defvar redis-executor-last-id "0"
  "Last processed Redis stream ID")

(defvar redis-executor-error-count 0
  "Count of consecutive errors for exponential backoff")

(defvar redis-executor-max-stream-length 1000
  "Maximum length of Redis stream before cleanup")

(defvar redis-executor-heartbeat-timer nil
  "Timer for sending heartbeat signals")

(defvar redis-executor-auto-restart t
  "Whether to automatically restart on errors")

(defvar redis-executor-session-id nil
  "Unique session identifier for this Emacs instance")

(defvar redis-executor-vision-timer nil
  "Timer for continuous state streaming")

(defvar redis-executor-last-state nil
  "Last captured state to detect changes")

(defvar redis-executor-vision-enabled t
  "Whether persistent vision is enabled")

(defvar redis-executor-vision-interval 0.1
  "Interval in seconds for vision updates (100ms default)")

(defun redis-executor-start ()
  "Start the Redis command executor with continuous operation features"
  (interactive)
  ;; Stop any existing timers
  (redis-executor-stop)
  
  ;; Generate unique session ID
  (setq redis-executor-session-id (format "emacs_%d_%d" (emacs-pid) (floor (time-to-seconds))))
  
  ;; Reset error count
  (setq redis-executor-error-count 0)
  
  ;; Start main polling timer
  (setq redis-executor-timer 
        (run-with-timer 0 0.5 'redis-executor-poll-and-execute))
  
  ;; Start heartbeat timer
  (setq redis-executor-heartbeat-timer
        (run-with-timer 10 30 'redis-executor-send-heartbeat))
  
  ;; Start persistent vision
  (redis-executor-start-persistent-vision)
  
  ;; Install real-time hooks
  (redis-executor-install-vision-hooks)
  
  ;; Cleanup old streams
  (redis-executor-cleanup-streams)
  
  ;; Register this instance
  (redis-executor-register-instance)
  
  (message "🚀 Redis Command Executor STARTED - continuous operation mode enabled")
  (message "   Session ID: %s" redis-executor-session-id))

(defun redis-executor-stop ()
  "Stop the Redis command executor"
  (interactive)
  (when redis-executor-timer
    (cancel-timer redis-executor-timer)
    (setq redis-executor-timer nil))
  (when redis-executor-heartbeat-timer
    (cancel-timer redis-executor-heartbeat-timer)
    (setq redis-executor-heartbeat-timer nil))
  ;; Stop persistent vision
  (redis-executor-stop-persistent-vision)
  ;; Remove vision hooks
  (redis-executor-remove-vision-hooks)
  ;; Unregister this instance
  (when redis-executor-session-id
    (redis-executor-unregister-instance))
  (message "⏹️ Redis Command Executor STOPPED"))

(defun redis-executor-poll-and-execute ()
  "Poll Redis for new commands and execute them with auto-recovery"
  (condition-case err
      (let ((result (shell-command-to-string 
                     (format "redis-cli XREAD STREAMS emacs:commands %s" 
                             redis-executor-last-id))))
        (when (and result (not (string-empty-p result)))
          (redis-executor-process-commands result))
        ;; Reset error count on successful poll
        (setq redis-executor-error-count 0))
    (error 
     (progn
       (setq redis-executor-error-count (1+ redis-executor-error-count))
       (let ((backoff-delay (min 60 (* 2 redis-executor-error-count))))
         (message "Redis executor error #%d: %s (retrying in %ds)" 
                  redis-executor-error-count 
                  (error-message-string err)
                  backoff-delay)
         ;; Auto-restart with exponential backoff if enabled
         (when redis-executor-auto-restart
           (cancel-timer redis-executor-timer)
           (setq redis-executor-timer 
                 (run-with-timer backoff-delay 0.5 'redis-executor-poll-and-execute))))))))

(defun redis-executor-process-commands (redis-output)
  "Process Redis command output and execute commands with enhanced parsing"
  (let ((lines (split-string redis-output "\n" t)))
    (let ((i 0))
      (while (< i (length lines))
        (let ((line (nth i lines)))
          ;; Look for stream IDs (format: 1234567890-0)
          (when (string-match "^[0-9]+-[0-9]+$" line)
            (let ((stream-id line)
                  (fields-hash (make-hash-table :test 'equal)))
              
              ;; Parse the key-value pairs after the stream ID
              (setq i (1+ i))
              (while (and (< i (length lines))
                         (not (string-match "^[0-9]+-[0-9]+$" (nth i lines)))
                         (not (string-match "^emacs:" (nth i lines))))
                (let ((key (nth i lines)))
                  (setq i (1+ i))
                  (when (< i (length lines))
                    (let ((value (nth i lines)))
                      (puthash key value fields-hash)
                      (setq i (1+ i))))))
              
              ;; Execute based on the parsed fields
              (redis-executor-execute-from-fields fields-hash stream-id)
              
              ;; Update last processed ID
              (setq redis-executor-last-id stream-id)
              (setq i (1- i)))) ;; Decrement i to handle the next line correctly
          (setq i (1+ i)))))))

(defun redis-executor-string-to-number (s)
  "Convert string to number if possible, otherwise return string."
  (if (string-match-p "^[0-9]+$" s)
      (string-to-number s)
    s))

(defun redis-executor-execute-from-fields (fields-hash stream-id)
  "Execute command based on parsed Redis stream fields"
  (let ((elisp-code (gethash "elisp" fields-hash))
        (command-name (gethash "command" fields-hash))
        (function-name (car (hash-table-keys fields-hash))))
    
    (cond
     ;; Handle elisp expressions directly
     (elisp-code
      (redis-executor-execute-elisp elisp-code stream-id))
     
     ;; Handle explicit command field
     (command-name
      (redis-executor-execute-function-call command-name nil stream-id))
     
     ;; Handle direct function calls (backward compatibility)
     ((and function-name (not (equal function-name "elisp")) (not (equal function-name "command")))
      (let ((args (gethash function-name fields-hash)))
        (redis-executor-execute-function-call function-name (if args (split-string args) nil) stream-id)))
     
     ;; Unknown format
     (t
      (redis-executor-send-status "error" "unknown" stream-id "Unknown command format")))))

(defun redis-executor-execute-elisp (elisp-code stream-id)
  "Execute raw elisp code safely"
  (condition-case err
      (let ((result (eval (read elisp-code))))
        (redis-executor-send-status "success" "elisp-eval" stream-id 
                                   (format "Executed: %s → %s" elisp-code result))
        ;; Send current state back to Redis for feedback
        (redis-executor-report-current-state))
    (error
     (redis-executor-send-status "error" "elisp-eval" stream-id 
                                (format "Error executing %s: %s" elisp-code (error-message-string err))))))

(defun redis-executor-execute-function-call (function-name args stream-id)
  "Execute a function call with arguments"
  (let ((func (intern function-name)))
    (condition-case err
        (if (fboundp func)
            (progn
              (if args
                  (apply func (mapcar #'redis-executor-string-to-number args))
                (funcall func))
              (redis-executor-send-status "success" function-name stream-id 
                                         (format "Executed: (%s %s)" function-name (mapconcat #'prin1-to-string args " ")))
              ;; Send current state back to Redis for feedback
              (redis-executor-report-current-state))
          (redis-executor-send-status "error" function-name stream-id 
                                     (format "Unknown function: %s" function-name)))
      (error
       (redis-executor-send-status "error" function-name stream-id 
                                  (format "Error: %s" (error-message-string err)))))))

(defun redis-executor-execute-command (command-list stream-id)
  "Execute a single Redis command list"
  (let* ((command-name (car command-list))
         (args (mapcar #'redis-executor-string-to-number (cdr command-list)))
         (func (intern command-name)))
    (message "🎯 EXECUTING: (%s %s) (ID: %s)" command-name (mapconcat #'prin1-to-string args " ") stream-id)
    (message "  - Function: %s, Arguments: %s, fboundp: %s" func args (fboundp func))
    
    (condition-case err
        (if (fboundp func)
            (progn
              (apply func args)
              (redis-executor-send-status "success" command-name stream-id 
                                         (format "Executed: (%s %s)" command-name (mapconcat #'prin1-to-string args " "))))
          (let ((key-sequence (read-kbd-macro command-name)))
            (if (and key-sequence (> (length key-sequence) 0))
                (progn
                  (execute-kbd-macro key-sequence)
                  (redis-executor-send-status "success" command-name stream-id 
                                             (format "Executed key sequence: %s" command-name)))
              (redis-executor-send-status "error" command-name stream-id 
                                         (format "Unknown function or key sequence: %s" command-name)))))
      (error
       (redis-executor-send-status "error" command-name stream-id 
                                  (format "Error: %s" (error-message-string err)))))))

(defun redis-executor-report-state ()
  "Report the current state of Emacs to Redis"
  (interactive)
  (let* ((buffer-content (buffer-string))
         (cursor-position (point))
         (state-json (json-encode `(:content ,buffer-content :position ,cursor-position))))
    (shell-command (format "redis-cli SET emacs:state %s" (shell-quote-argument state-json)))))

(defun redis-executor-report-current-state ()
  "Report comprehensive current Emacs state to Redis for AI feedback"
  (condition-case nil
      (let* ((current-buffer (buffer-name))
             (cursor-pos (point))
             (buffer-content (buffer-substring-no-properties (point-min) (point-max)))
             (window-config (mapcar (lambda (w) (buffer-name (window-buffer w))) (window-list)))
             (state-data (format "buffer=%s point=%d windows=%s content_length=%d timestamp=%s"
                                current-buffer 
                                cursor-pos
                                (mapconcat 'identity window-config ",")
                                (length buffer-content)
                                (current-time-string))))
        ;; Send to state stream for AI to read
        (shell-command (format "redis-cli XADD emacs:state '*' %s" state-data))
        ;; Also update the simple state key
        (shell-command (format "redis-cli SET emacs:current %s" (shell-quote-argument current-buffer))))
    (error nil)))


(defun redis-executor-send-status (status action stream-id details)
  "Send execution status back to Redis"
  (let ((status-data (format "action=%s status=%s stream_id=%s details=%s timestamp=%s" 
                            action status stream-id details (current-time-string))))
    (shell-command (format "redis-cli XADD emacs:status '*' %s" status-data))
    (message "📊 STATUS: %s - %s" status details)))

(defun redis-executor-test ()
  "Test the Redis executor with comprehensive test sequence"
  (interactive)
  (message "🧪 Testing Redis Executor...")
  
  ;; Clear old test commands
  (shell-command "redis-cli DEL emacs:test_responses")
  
  ;; Test 1: Simple elisp evaluation
  (shell-command "redis-cli XADD emacs:commands '*' elisp '(message \"✅ REDIS EXECUTOR TEST WORKING!\")'")
  
  ;; Test 2: Buffer creation  
  (shell-command "redis-cli XADD emacs:commands '*' elisp '(progn (switch-to-buffer \"*REDIS-TEST*\") (insert \"Redis executor is WORKING!\\n\"))'")
  
  ;; Test 3: Function call format
  (shell-command "redis-cli XADD emacs:commands '*' message '🎯 Function call format works!'")
  
  (message "✅ Test commands sent - watch for results in 2 seconds...")
  
  ;; Check results after delay
  (run-with-timer 3 nil 
                  (lambda ()
                    (message "🔍 Checking test results...")
                    (shell-command-to-string "redis-cli XREVRANGE emacs:responses + - COUNT 5"))))

(defun redis-executor-show-recent-commands ()
  "Show recent Redis commands for debugging"
  (interactive)
  (let ((result (shell-command-to-string "redis-cli XREVRANGE emacs:commands + - COUNT 5")))
    (with-current-buffer (get-buffer-create "*Redis Commands*")
      (erase-buffer)
      (insert "Recent Redis Commands:
")
      (insert "========================

")
      (insert result)
      (display-buffer (current-buffer)))))

(defun redis-executor-show-status ()
  "Show recent execution status"
  (interactive)
  (let ((result (shell-command-to-string "redis-cli XREVRANGE emacs:status + - COUNT 10")))
    (with-current-buffer (get-buffer-create "*Redis Status*")
      (erase-buffer)
      (insert "Redis Execution Status:
")
      (insert "=======================

")
      (insert result)
      (display-buffer (current-buffer)))))

;; === CONTINUOUS OPERATION FEATURES ===

(defun redis-executor-send-heartbeat ()
  "Send heartbeat signal to Redis to indicate this instance is alive"
  (when redis-executor-session-id
    (condition-case nil
        (shell-command 
         (format "redis-cli HSET emacs:instances %s '{\"last_heartbeat\":\"%s\",\"buffer\":\"%s\",\"point\":%d}'"
                 redis-executor-session-id
                 (current-time-string)
                 (buffer-name)
                 (point)))
      (error nil))))

(defun redis-executor-register-instance ()
  "Register this Emacs instance with Redis"
  (when redis-executor-session-id
    (condition-case nil
        (shell-command 
         (format "redis-cli HSET emacs:instances %s '{\"started\":\"%s\",\"pid\":%d,\"version\":\"%s\"}'"
                 redis-executor-session-id
                 (current-time-string)
                 (emacs-pid)
                 emacs-version))
      (error nil))))

(defun redis-executor-unregister-instance ()
  "Unregister this Emacs instance from Redis"
  (when redis-executor-session-id
    (condition-case nil
        (shell-command 
         (format "redis-cli HDEL emacs:instances %s" redis-executor-session-id))
      (error nil))))

(defun redis-executor-cleanup-streams ()
  "Clean up old Redis streams to prevent infinite growth"
  (condition-case nil
      (progn
        ;; Keep only last 1000 commands
        (shell-command 
         (format "redis-cli XTRIM emacs:commands MAXLEN ~ %d" redis-executor-max-stream-length))
        ;; Keep only last 500 status messages
        (shell-command "redis-cli XTRIM emacs:status MAXLEN ~ 500")
        (message "🧹 Redis streams cleaned up"))
    (error nil)))

(defun redis-executor-health-check ()
  "Perform comprehensive health check"
  (interactive)
  (let ((redis-ok (condition-case nil
                      (string= "PONG" (string-trim (shell-command-to-string "redis-cli ping")))
                    (error nil)))
        (timer-ok (and redis-executor-timer (not (timer--canceled redis-executor-timer))))
        (heartbeat-ok (and redis-executor-heartbeat-timer (not (timer--canceled redis-executor-heartbeat-timer)))))
    
    (message "🏥 Redis Executor Health Check:")
    (message "   Redis connection: %s" (if redis-ok "✅ OK" "❌ FAILED"))
    (message "   Main timer: %s" (if timer-ok "✅ RUNNING" "❌ STOPPED"))
    (message "   Heartbeat timer: %s" (if heartbeat-ok "✅ RUNNING" "❌ STOPPED"))
    (message "   Error count: %d" redis-executor-error-count)
    (message "   Session ID: %s" (or redis-executor-session-id "NONE"))
    
    ;; Auto-restart if needed
    (when (and redis-executor-auto-restart (not (and redis-ok timer-ok heartbeat-ok)))
      (message "🔄 Auto-restarting Redis executor...")
      (redis-executor-start))))

(defun redis-executor-show-instances ()
  "Show all registered Emacs instances"
  (interactive)
  (let ((result (shell-command-to-string "redis-cli HGETALL emacs:instances")))
    (with-current-buffer (get-buffer-create "*Redis Instances*")
      (erase-buffer)
      (insert "Active Emacs Instances:
")
      (insert "========================

")
      (insert result)
      (display-buffer (current-buffer)))))

(defun redis-executor-force-restart ()
  "Force restart the Redis executor with full cleanup"
  (interactive)
  (message "🔄 Force restarting Redis executor...")
  (redis-executor-stop)
  (sleep-for 1)
  (redis-executor-start))

(defun redis-executor-get-visual-state ()
  "Get comprehensive visual state that an AI can use to 'see' Emacs"
  (interactive)
  (let* ((all-buffers (mapcar 'buffer-name (buffer-list)))
         (visible-buffers (mapcar (lambda (w) (buffer-name (window-buffer w))) (window-list)))
         (current-buf (buffer-name))
         (cursor-pos (point))
         (buffer-size (buffer-size))
         (window-count (length (window-list)))
         (current-line (line-number-at-pos))
         (buffer-content (if (< buffer-size 1000) 
                             (buffer-string) 
                             (concat (buffer-substring 1 500) "\n...[TRUNCATED]...\n" 
                                    (buffer-substring (max 1 (- buffer-size 500)) buffer-size))))
         (state-report (format "EMACS VISUAL STATE:\nCurrent Buffer: %s\nCursor Position: %d (line %d)\nWindow Count: %d\nVisible Buffers: [%s]\nAll Buffers: [%s]\nBuffer Size: %d chars\n--- BUFFER CONTENT ---\n%s\n--- END CONTENT ---"
                              current-buf cursor-pos current-line window-count
                              (mapconcat 'identity visible-buffers ", ")
                              (mapconcat 'identity (seq-take all-buffers 10) ", ")
                              buffer-size
                              buffer-content)))
    ;; Store in Redis for AI to read
    (shell-command (format "redis-cli SET emacs:visual_state %s" (shell-quote-argument state-report)))
    (message "📸 Visual state captured to Redis")
    state-report))

;; === PERSISTENT VISION SYSTEM ===

(defun redis-executor-start-persistent-vision ()
  "Start the persistent vision system for real-time state streaming"
  (when redis-executor-vision-enabled
    (when redis-executor-vision-timer
      (cancel-timer redis-executor-vision-timer))
    
    ;; Initialize last state
    (setq redis-executor-last-state (redis-executor-capture-full-state))
    
    ;; Start continuous vision timer (100ms default)
    (setq redis-executor-vision-timer
          (run-with-timer 0 redis-executor-vision-interval 'redis-executor-continuous-vision))
    
    (message "👁️ Persistent vision STARTED - streaming every %sms" 
             (round (* redis-executor-vision-interval 1000)))))

(defun redis-executor-stop-persistent-vision ()
  "Stop the persistent vision system"
  (when redis-executor-vision-timer
    (cancel-timer redis-executor-vision-timer)
    (setq redis-executor-vision-timer nil)
    (message "👁️ Persistent vision STOPPED")))

(defun redis-executor-continuous-vision ()
  "Continuously capture and stream Emacs state changes"
  (when redis-executor-vision-enabled
    (condition-case err
        (let ((current-state (redis-executor-capture-full-state)))
          ;; Only stream if state has changed
          (unless (equal current-state redis-executor-last-state)
            (redis-executor-stream-state-change current-state redis-executor-last-state)
            (setq redis-executor-last-state current-state)))
      (error 
       (message "Vision error: %s" (error-message-string err))))))

(defun redis-executor-capture-full-state ()
  "Capture complete Emacs state for change detection"
  (let ((current-buffer (buffer-name))
        (cursor-pos (point))
        (cursor-line (line-number-at-pos))
        (cursor-col (current-column))
        (buffer-size (buffer-size))
        (window-count (length (window-list)))
        (visible-buffers (mapcar (lambda (w) (buffer-name (window-buffer w))) (window-list)))
        (frame-count (length (frame-list)))
        (buffer-modified (buffer-modified-p))
        (major-mode-name (symbol-name major-mode))
        (region-active (use-region-p))
        (region-start (when (use-region-p) (region-beginning)))
        (region-end (when (use-region-p) (region-end)))
        (buffer-content-hash (secure-hash 'md5 (buffer-string))))
    
    (list :buffer current-buffer
          :cursor cursor-pos
          :line cursor-line
          :column cursor-col
          :size buffer-size
          :windows window-count
          :visible-buffers visible-buffers
          :frames frame-count
          :modified buffer-modified
          :mode major-mode-name
          :region-active region-active
          :region-start region-start
          :region-end region-end
          :content-hash buffer-content-hash
          :timestamp (float-time))))

(defun redis-executor-stream-state-change (current-state last-state)
  "Stream state changes to Redis for real-time AI vision"
  (condition-case nil
      (let ((changes (redis-executor-detect-changes current-state last-state))
            (timestamp (format "%.3f" (float-time))))
        
        ;; Stream the change event
        (shell-command 
         (format "redis-cli XADD emacs:vision '*' session '%s' timestamp '%s' changes '%s' state '%s'"
                 redis-executor-session-id
                 timestamp
                 (json-encode changes)
                 (json-encode current-state)))
        
        ;; Update the current state key for immediate access
        (shell-command 
         (format "redis-cli SET emacs:live_state '%s'" 
                 (json-encode current-state)))
        
        ;; Log significant changes
        (when (plist-get changes :buffer-changed)
          (message "👁️ Buffer changed: %s → %s" 
                   (plist-get last-state :buffer)
                   (plist-get current-state :buffer)))
        
        (when (plist-get changes :major-movement)
          (message "👁️ Major cursor movement: line %d → %d" 
                   (plist-get last-state :line)
                   (plist-get current-state :line))))
    (error nil)))

(defun redis-executor-detect-changes (current last)
  "Detect what changed between states"
  (let ((changes '()))
    
    ;; Buffer change
    (unless (equal (plist-get current :buffer) (plist-get last :buffer))
      (setq changes (plist-put changes :buffer-changed t))
      (setq changes (plist-put changes :old-buffer (plist-get last :buffer)))
      (setq changes (plist-put changes :new-buffer (plist-get current :buffer))))
    
    ;; Cursor movement
    (let ((cursor-delta (abs (- (plist-get current :cursor) (plist-get last :cursor))))
          (line-delta (abs (- (plist-get current :line) (plist-get last :line)))))
      (when (> cursor-delta 0)
        (setq changes (plist-put changes :cursor-moved t))
        (setq changes (plist-put changes :cursor-delta cursor-delta)))
      (when (> line-delta 5)
        (setq changes (plist-put changes :major-movement t))
        (setq changes (plist-put changes :line-delta line-delta))))
    
    ;; Buffer size change (editing)
    (let ((size-delta (- (plist-get current :size) (plist-get last :size))))
      (when (/= size-delta 0)
        (setq changes (plist-put changes :content-changed t))
        (setq changes (plist-put changes :size-delta size-delta))))
    
    ;; Window configuration change
    (unless (equal (plist-get current :visible-buffers) (plist-get last :visible-buffers))
      (setq changes (plist-put changes :windows-changed t))
      (setq changes (plist-put changes :old-windows (plist-get last :visible-buffers)))
      (setq changes (plist-put changes :new-windows (plist-get current :visible-buffers))))
    
    ;; Mode change
    (unless (equal (plist-get current :mode) (plist-get last :mode))
      (setq changes (plist-put changes :mode-changed t))
      (setq changes (plist-put changes :old-mode (plist-get last :mode)))
      (setq changes (plist-put changes :new-mode (plist-get current :mode))))
    
    ;; Region selection
    (unless (equal (plist-get current :region-active) (plist-get last :region-active))
      (setq changes (plist-put changes :selection-changed t))
      (setq changes (plist-put changes :region-active (plist-get current :region-active))))
    
    changes))

(defun redis-executor-install-vision-hooks ()
  "Install hooks for immediate state change detection"
  (add-hook 'post-command-hook 'redis-executor-immediate-cursor-update)
  (add-hook 'window-configuration-change-hook 'redis-executor-immediate-window-update)
  (add-hook 'buffer-list-update-hook 'redis-executor-immediate-buffer-update)
  (message "🔗 Vision hooks installed"))

(defun redis-executor-remove-vision-hooks ()
  "Remove vision hooks"
  (remove-hook 'post-command-hook 'redis-executor-immediate-cursor-update)
  (remove-hook 'window-configuration-change-hook 'redis-executor-immediate-window-update)
  (remove-hook 'buffer-list-update-hook 'redis-executor-immediate-buffer-update)
  (message "🔗 Vision hooks removed"))

(defun redis-executor-immediate-cursor-update ()
  "Immediate cursor position update hook"
  (when (and redis-executor-vision-enabled redis-executor-session-id)
    (condition-case nil
        (shell-command 
         (format "redis-cli SET emacs:cursor '%s:%d:%d'" 
                 (buffer-name) (point) (line-number-at-pos)))
      (error nil))))

(defun redis-executor-immediate-window-update ()
  "Immediate window configuration update hook"
  (when (and redis-executor-vision-enabled redis-executor-session-id)
    (condition-case nil
        (let ((windows (mapcar (lambda (w) (buffer-name (window-buffer w))) (window-list))))
          (shell-command 
           (format "redis-cli SET emacs:windows '%s'" 
                   (json-encode windows))))
      (error nil))))

(defun redis-executor-immediate-buffer-update ()
  "Immediate buffer list update hook"
  (when (and redis-executor-vision-enabled redis-executor-session-id)
    (condition-case nil
        (shell-command 
         (format "redis-cli SET emacs:current_buffer '%s'" (buffer-name)))
      (error nil))))

;; Vision control functions
(defun redis-executor-toggle-vision ()
  "Toggle persistent vision on/off"
  (interactive)
  (setq redis-executor-vision-enabled (not redis-executor-vision-enabled))
  (if redis-executor-vision-enabled
      (progn
        (redis-executor-start-persistent-vision)
        (redis-executor-install-vision-hooks)
        (message "👁️ Persistent vision ENABLED"))
    (progn
      (redis-executor-stop-persistent-vision)
      (redis-executor-remove-vision-hooks)
      (message "👁️ Persistent vision DISABLED"))))

(defun redis-executor-vision-status ()
  "Show persistent vision status"
  (interactive)
  (message "👁️ Vision: %s | Timer: %s | Hooks: %s | Interval: %sms"
           (if redis-executor-vision-enabled "ON" "OFF")
           (if redis-executor-vision-timer "RUNNING" "STOPPED")
           (if (memq 'redis-executor-immediate-cursor-update post-command-hook) "INSTALLED" "NOT-INSTALLED")
           (round (* redis-executor-vision-interval 1000))))

;; Auto-start on load if desired
(defvar redis-executor-auto-start-on-load nil
  "Whether to automatically start the executor when this file is loaded")

(when redis-executor-auto-start-on-load
  (add-hook 'emacs-startup-hook 'redis-executor-start))

(provide 'redis-command-executor)

;;; redis_command_executor.el ends here
