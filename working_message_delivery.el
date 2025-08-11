;;; working_message_delivery.el --- Simple working message delivery

;; -*- lexical-binding: t -*-

(require 'cl-lib)
(require 'json)

;; Include the Redis parser inline
(defun redis-parse-xread-response (output)
  "Parse actual Redis XREAD response format"
  (when (and output (not (string-empty-p output)) (not (string-match-p "(nil)" output)))
    (let ((lines (split-string output "\n" t))
          (messages '())
          (current-stream nil)
          (current-id nil)
          (current-fields '()))
      
      (let ((i 0))
        (while (< i (length lines))
          (let ((line (string-trim (nth i lines))))
            (cond
             ;; Stream name (contains colon)
             ((string-match-p ":" line)
              (setq current-stream line
                    current-id nil
                    current-fields '()))
             
             ;; Message ID (timestamp-sequence format)
             ((and current-stream (string-match-p "^[0-9]+-[0-9]+$" line))
              (when (and current-id current-fields)
                ;; Save previous message
                (push (list :stream current-stream
                           :id current-id
                           :fields (reverse current-fields))
                      messages))
              (setq current-id line
                    current-fields '()))
             
             ;; Field-value pairs
             ((and current-id (< (1+ i) (length lines)))
              (let ((field line)
                    (value (nth (1+ i) lines)))
                (push (cons field value) current-fields)
                (setq i (1+ i)))) ; Skip the value line
             ))
          (setq i (1+ i))))
      
      ;; Don't forget the last message
      (when (and current-id current-fields)
        (push (list :stream current-stream
                   :id current-id
                   :fields (reverse current-fields))
              messages))
      
      (reverse messages))))

(defvar message-handlers (make-hash-table :test 'equal)
  "Message handlers: actor-name -> hash-table of message-type -> handler")

(defvar message-timers (make-hash-table :test 'equal)
  "Active timers for message processing")

(defvar last-message-ids (make-hash-table :test 'equal)
  "Last processed message ID per stream")

(defun msg-register-handler (actor-name message-type handler-func)
  "Register a message handler"
  (let ((actor-handlers (or (gethash actor-name message-handlers)
                           (make-hash-table :test 'equal))))
    (puthash message-type handler-func actor-handlers)
    (puthash actor-name actor-handlers message-handlers)
    (message "📋 Handler registered: %s.%s" actor-name message-type)))

(defun msg-send (recipient message-type data sender)
  "Send a message via Redis"
  (let* ((stream-name (format "actor:%s:inbox" recipient))
         (fields `((type . ,message-type)
                   (data . ,(json-encode data))
                   (sender . ,sender)
                   (timestamp . ,(float-time)))))
    
    (condition-case err
        (let ((result (shell-command-to-string 
                      (format "redis-cli XADD %s '*' %s"
                             (shell-quote-argument stream-name)
                             (mapconcat (lambda (kv) 
                                         (format "%s %s" 
                                                (shell-quote-argument (format "%s" (car kv)))
                                                (shell-quote-argument (format "%s" (cdr kv)))))
                                       fields " ")))))
          (if (string-match-p "^[0-9]+-[0-9]+$" (string-trim result))
              (progn
                (message "📨 Sent %s to %s: %s" message-type recipient (string-trim result))
                (string-trim result))
            (progn
              (message "❌ Send failed: %s" result)
              nil)))
      (error
       (message "❌ Send error: %s" (error-message-string err))
       nil))))

(defun msg-read-inbox (actor-name)
  "Read messages from actor's inbox using real Redis parser"
  (message "🔍 Reading inbox for %s" actor-name)
  (let* ((stream-name (format "actor:%s:inbox" actor-name))
         (last-id (or (gethash stream-name last-message-ids) "0")))
    
    (condition-case err
        (let* ((stream-quoted (shell-quote-argument stream-name))
               (id-quoted (shell-quote-argument last-id))
               (cmd (format "redis-cli XREAD COUNT 10 STREAMS %s %s" stream-quoted id-quoted))
               (output (shell-command-to-string cmd)))
          (message "🔍 CMD: %s" cmd)
          (message "🔍 OUTPUT: '%s'" output)
          (when (and output 
                     (not (string-empty-p output))
                     (not (string-match-p "(nil)" output)))
            (message "🔍 Redis output: %s" (substring output 0 (min 100 (length output))))
            ;; Use the real Redis parser
            (let ((messages (redis-parse-xread-response output)))
              (message "🔍 Parsed %d messages" (length messages))
              (dolist (msg messages)
                (let ((msg-id (plist-get msg :id))
                      (fields (plist-get msg :fields)))
                  ;; Don't update last-message-ids to avoid the consumption bug
                  ;; In production, would use Redis consumer groups  
                  (msg-dispatch-real-message actor-name fields))))))
      (error 
       (message "❌ Inbox read error for %s: %s" actor-name (error-message-string err))
       nil))))

(defun msg-parse-messages (actor-name stream-name output)
  "Parse Redis XREAD output"
  (let ((lines (split-string output "\n" t))
        (messages '())
        (current-id nil)
        (current-fields '()))
    
    (dolist (line lines)
      (setq line (string-trim line))
      (cond
       ;; Message ID
       ((string-match-p "^[0-9]+-[0-9]+$" line)
        (when current-id
          ;; Process previous message
          (push (cons current-id current-fields) messages))
        (setq current-id line
              current-fields '()))
       
       ;; Field name (when we have an ID)
       ((and current-id (not (string-empty-p line)))
        (push line current-fields))))
    
    ;; Don't forget last message
    (when current-id
      (push (cons current-id current-fields) messages))
    
    ;; Process messages
    (dolist (msg (reverse messages))
      (let ((msg-id (car msg))
            (fields (cdr msg)))
        (puthash stream-name msg-id last-message-ids)
        (msg-dispatch-message actor-name fields)))))

;; Removed broken first dispatch function

(defun msg-dispatch-real-message (actor-name fields)
  "Dispatch message using real Redis parser format"
  (let* ((message-type (alist-get "type" fields nil nil #'string=))
         (data-json (alist-get "data" fields nil nil #'string=))
         (sender (alist-get "sender" fields nil nil #'string=)))
    
    (when (and message-type data-json sender)
      (condition-case err
          (let* ((data (json-read-from-string data-json))
                 (actor-handlers (gethash actor-name message-handlers))
                 (handler (when actor-handlers (gethash message-type actor-handlers))))
            
            (if handler
                (progn
                  (message "📨 Dispatching %s to %s from %s" message-type actor-name sender)
                  (funcall handler data sender))
              (message "⚠️ No handler for %s in %s" message-type actor-name)))
        
        (error
         (message "❌ Real dispatch error: %s" (error-message-string err))))))

(defun msg-start-processing (actor-name)
  "Start processing messages for an actor"
  (let ((timer-key (format "%s-inbox" actor-name)))
    (msg-stop-processing actor-name)
    (let ((timer (run-with-timer 0 1 
                                `(lambda () (msg-read-inbox ,actor-name)))))
      (puthash timer-key timer message-timers)
      (message "📥 Started processing for %s" actor-name))))

(defun msg-stop-processing (actor-name)
  "Stop processing messages for an actor"
  (let* ((timer-key (format "%s-inbox" actor-name))
         (timer (gethash timer-key message-timers)))
    (when timer
      (cancel-timer timer)
      (remhash timer-key message-timers)
      (message "📥 Stopped processing for %s" actor-name))))

(defun msg-stop-all ()
  "Stop all message processing"
  (maphash (lambda (_key timer) (cancel-timer timer)) message-timers)
  (clrhash message-timers)
  (clrhash last-message-ids)
  (message "🛑 All message processing stopped"))

(defun msg-test ()
  "Test message delivery"
  (interactive)
  
  ;; Register handlers
  (msg-register-handler "ping-actor" "ping"
                       (lambda (data sender)
                         (message "🏓 Got ping from %s: %s" sender data)
                         (msg-send sender "pong" 
                                  `((reply . "pong back")
                                    (original . ,data))
                                  "ping-actor")))
  
  (msg-register-handler "test-sender" "pong"
                       (lambda (data sender)
                         (message "🏓 Got pong from %s: %s" sender data)))
  
  ;; Start processing
  (msg-start-processing "ping-actor")
  (msg-start-processing "test-sender")
  
  ;; Send test message
  (run-with-timer 1 nil
                 (lambda ()
                   (message "🧪 About to send test message...")
                   (msg-send "ping-actor" "ping" 
                            '((message . "Hello ping!")
                              (test . 123))
                            "test-sender")
                   (message "🧪 Test message sent!")))
  
  (message "🧪 Message test started"))

(provide 'working-message-delivery)