;;; redis-ai-core.el --- Core Redis communication functions for Redis AI Emacs mode

;;; Code:

(require 'json)

(defcustom redis-ai-host "localhost"
  "Redis server host"
  :type 'string
  :group 'redis-ai)

(defcustom redis-ai-port 6379
  "Redis server port"
  :type 'integer
  :group 'redis-ai)

(defvar redis-ai-connection nil
  "Redis connection status. (t if connected, nil otherwise)")

(defvar redis-ai-command-history '()
  "History of Redis AI commands.")

(defun redis-ai-filter (proc string)
  "Dummy filter function for compatibility. Redis communication is now direct."
  (message "redis-ai-filter called (dummy): %s" string))

(defun redis-ai-sentinel (proc event)
  "Dummy sentinel function for compatibility. Redis communication is now direct."
  (message "redis-ai-sentinel called (dummy): %s" event))

(defun redis-ai-create-consumer-group (stream-name group-name consumer-name)
  "Create a Redis consumer group for a stream if it doesn't exist."
  (let* ((command (format "XGROUP CREATE %s %s 0 MKSTREAM" stream-name group-name))
         (result (redis-ai-send-command command)))
    (if (string-match-p "OK" result)
        (message "Redis consumer group '%s' created for stream '%s'." group-name stream-name)
      (if (string-match-p "BUSYGROUP" result)
          (message "Redis consumer group '%s' already exists for stream '%s'." group-name stream-name)
        (message "Error creating Redis consumer group '%s' for stream '%s': %s" group-name stream-name result)))))

(defun redis-ai-connect ()
  "Connect to Redis server (now uses redis-cli directly)."
  (interactive)
  (message "Attempting to connect to Redis via redis-cli at %s:%d" redis-ai-host redis-ai-port)
  (let ((ping-result (string-trim (shell-command-to-string (format "redis-cli -h %s -p %d PING" redis-ai-host redis-ai-port)))))
    (if (string-match-p "PONG" ping-result)
        (progn
          (setq redis-ai-connection t) ;; Indicate a successful conceptual connection
          (message "✅ Connected to Redis AI system via redis-cli.")
          (redis-ai-create-consumer-group "ai:results" "ai_group" "ai_consumer") ;; Create consumer group
          (redis-ai-initialize-event-handlers) ;; These will be defined in redis-ai-events.el
          (redis-ai-start-monitoring)) ;; These will be defined in redis-ai-monitoring.el
      (message "❌ Could not connect to Redis AI system via redis-cli. Ping result: %s" ping-result))))

(defun redis-ai-disconnect ()
  "Disconnect from Redis server (now a conceptual disconnect)."
  (interactive)
  (setq redis-ai-connection nil)
  (message "Disconnected from Redis AI system (conceptual)."))

(defun redis-ai-send-command (command)
  "Send COMMAND to Redis server using redis-cli."
  (let* ((full-cli-command (format "redis-cli -h %s -p %d %s" redis-ai-host redis-ai-port command)))
    (message "DEBUG: Full redis-cli command: %S" full-cli-command) ;; Added debugging line
    (let ((raw-result (string-trim (shell-command-to-string full-cli-command))))
      (push command redis-ai-command-history)
      (if (or (string-prefix-p "ERR" raw-result)
              (string-prefix-p "(error)" raw-result))
          (progn
            (message "❌ Redis command error: %s" raw-result)
            (error "Redis command failed: %s" raw-result))
        (message "Redis command result: %s" raw-result)
        raw-result))))

(defun redis-ai-parse-xreadgroup-response (response-string)
  "Parses the raw string response from XREADGROUP into a structured Lisp list."
  (if (or (string-empty-p response-string) (string-match-p "(nil)" response-string))
      nil ;; No new messages
    (condition-case err
        (let* ((parsed-list (read (format "(%s)" response-string))) ;; Convert string to Lisp list
               (stream-data (car parsed-list)) ;; Get the stream data
               (messages (cadr stream-data)) ;; Get the messages for the stream
               (first-message (car messages)) ;; Get the first message
               (message-payload (cadr first-message)) ;; Get the payload of the first message
               (result-json-string (cadr (member "result" message-payload :test 'string=)))) ;; Extract the JSON string
          result-json-string)
      (error
       (message "❌ Error parsing XREADGROUP response: %s" (error-message-string err))
       (message "Problematic response string: %S" response-string)
       nil)))) ;; Return nil on parsing error

(provide 'redis-ai-core)
;;; redis-ai-core.el ends here