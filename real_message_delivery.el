;;; real_message_delivery.el --- Actually working message delivery system

;; -*- lexical-binding: t -*-

;; Dependencies loaded externally
(require 'cl-lib)

(defvar message-delivery-timers (make-hash-table :test 'equal)
  "Active message delivery timers for each actor")

(defvar message-acknowledgments (make-hash-table :test 'equal)
  "Pending message acknowledgments: message-id -> (timestamp . callback)")

(defvar message-handlers (make-hash-table :test 'equal)
  "Message handlers for each actor: actor-name -> (message-type -> handler-func)")

(defvar last-message-ids (make-hash-table :test 'equal)
  "Last processed message ID for each actor stream")

(cl-defstruct message-envelope
  id
  type
  data
  sender
  recipient
  timestamp
  retry-count
  max-retries
  ack-timeout)

(defun message-delivery-register-handler (actor-name message-type handler-func)
  "Register a message handler for an actor"
  (let ((actor-handlers (or (gethash actor-name message-handlers)
                           (make-hash-table :test 'equal))))
    (puthash message-type handler-func actor-handlers)
    (puthash actor-name actor-handlers message-handlers)
    (message "📋 Handler registered: %s -> %s" actor-name message-type)))

(defun message-delivery-send (recipient message-type data &optional sender)
  "Send a message with delivery confirmation and retry logic
  
  Returns message-id on success, nil on failure"
  (let* ((sender (or sender "unknown"))
         (message-id (format "%s-%d" recipient (floor (* (float-time) 1000))))
         (envelope (make-message-envelope
                   :id message-id
                   :type message-type
                   :data data
                   :sender sender
                   :recipient recipient
                   :timestamp (float-time)
                   :retry-count 0
                   :max-retries 3
                   :ack-timeout 5.0)))
    
    (if (message-delivery-attempt-send envelope)
        (progn
          ;; Set up acknowledgment timeout
          (puthash message-id 
                   (cons (float-time) 
                         (lambda () (message-delivery-handle-ack-timeout envelope)))
                   message-acknowledgments)
          
          (run-with-timer (message-envelope-ack-timeout envelope) nil
                         `(lambda () (message-delivery-check-ack ,message-id)))
          
          (message "📨 Message sent: %s -> %s (%s)" sender recipient message-id)
          message-id)
      
      (message "❌ Failed to send message: %s -> %s" sender recipient)
      nil)))

(defun message-delivery-attempt-send (envelope)
  "Attempt to send a message envelope to Redis
  
  Returns t on success, nil on failure"
  (let* ((recipient (message-envelope-recipient envelope))
         (stream-name (format "actor:%s:inbox" recipient))
         (fields `((id . ,(message-envelope-id envelope))
                   (type . ,(message-envelope-type envelope))
                   (data . ,(json-encode (message-envelope-data envelope)))
                   (sender . ,(message-envelope-sender envelope))
                   (timestamp . ,(message-envelope-timestamp envelope))
                   (retry-count . ,(message-envelope-retry-count envelope)))))
    
    (when (redis-send-stream-message stream-name fields)
      ;; Message sent successfully
      t)))

(defun message-delivery-check-ack (message-id)
  "Check if acknowledgment was received, retry if not"
  (let ((ack-info (gethash message-id message-acknowledgments)))
    (when ack-info
      ;; Still waiting for ack - handle timeout
      (funcall (cdr ack-info))
      (remhash message-id message-acknowledgments))))

(defun message-delivery-handle-ack-timeout (envelope)
  "Handle acknowledgment timeout - retry or give up"
  (let ((retry-count (message-envelope-retry-count envelope))
        (max-retries (message-envelope-max-retries envelope)))
    
    (if (< retry-count max-retries)
        (progn
          (setf (message-envelope-retry-count envelope) (1+ retry-count))
          (message "🔄 Retrying message delivery: %s (attempt %d/%d)"
                   (message-envelope-id envelope)
                   (1+ retry-count)
                   max-retries)
          
          ;; Retry with exponential backoff
          (let ((backoff-delay (* (1+ retry-count) 2)))
            (run-with-timer backoff-delay nil
                           `(lambda ()
                              (when (message-delivery-attempt-send ,envelope)
                                (run-with-timer ,(message-envelope-ack-timeout envelope) nil
                                               `(lambda () 
                                                  (message-delivery-check-ack 
                                                   ,(message-envelope-id envelope)))))))))
      
      ;; Max retries exceeded
      (message "❌ Message delivery failed permanently: %s -> %s" 
               (message-envelope-sender envelope)
               (message-envelope-recipient envelope))
      
      ;; Notify sender of failure if possible
      (message-delivery-send (message-envelope-sender envelope)
                            "delivery-failed"
                            `((failed-message-id . ,(message-envelope-id envelope))
                              (reason . "max-retries-exceeded"))
                            "message-delivery-system"))))

(defun message-delivery-send-ack (message-id sender)
  "Send acknowledgment for received message"
  (redis-send-stream-message "message-delivery:acks"
                            `((message-id . ,message-id)
                              (ack-timestamp . ,(float-time))
                              (ack-sender . ,sender)))
  
  ;; Remove from pending acks
  (remhash message-id message-acknowledgments)
  (message "✅ Ack sent for message: %s" message-id))

(defun message-delivery-start-actor-inbox (actor-name)
  "Start processing inbox for an actor"
  (let ((timer-name (format "%s-inbox" actor-name)))
    
    ;; Stop existing timer
    (message-delivery-stop-actor-inbox actor-name)
    
    ;; Start new timer
    (let ((timer (run-with-timer 0 1 
                                `(lambda () 
                                   (message-delivery-process-inbox ,actor-name)))))
      (puthash timer-name timer message-delivery-timers)
      (message "📥 Started inbox processing for: %s" actor-name))))

(defun message-delivery-stop-actor-inbox (actor-name)
  "Stop inbox processing for an actor"
  (let* ((timer-name (format "%s-inbox" actor-name))
         (timer (gethash timer-name message-delivery-timers)))
    (when timer
      (cancel-timer timer)
      (remhash timer-name message-delivery-timers)
      (message "📥 Stopped inbox processing for: %s" actor-name))))

(defun message-delivery-process-inbox (actor-name)
  "Process pending messages in actor's inbox"
  (condition-case err
      (let* ((stream-name (format "actor:%s:inbox" actor-name))
             (last-id (or (gethash stream-name last-message-ids) "0"))
             (messages (redis-read-stream-messages stream-name last-id 10)))
        
        (when messages
          (dolist (msg messages)
            (let* ((msg-id (plist-get msg :id))
                   (fields (plist-get msg :fields))
                   (message-type (alist-get "type" fields nil nil #'string=))
                   (data-json (alist-get "data" fields nil nil #'string=))
                   (sender (alist-get "sender" fields nil nil #'string=))
                   (msg-internal-id (alist-get "id" fields nil nil #'string=)))
              
              ;; Update last processed ID
              (puthash stream-name msg-id last-message-ids)
              
              ;; Parse message data
              (condition-case parse-err
                  (let ((data (json-read-from-string data-json)))
                    
                    ;; Send acknowledgment
                    (message-delivery-send-ack msg-internal-id actor-name)
                    
                    ;; Dispatch to handler
                    (message-delivery-dispatch-message actor-name message-type data sender))
                
                (error 
                 (message "❌ Failed to parse message data: %s" 
                         (error-message-string parse-err)))))))
    
    (error
     ;; Don't spam errors if Redis is down
     nil)))

(defun message-delivery-dispatch-message (actor-name message-type data sender)
  "Dispatch message to appropriate handler"
  (let* ((actor-handlers (gethash actor-name message-handlers))
         (handler (when actor-handlers (gethash message-type actor-handlers))))
    
    (if handler
        (condition-case handler-err
            (progn
              (message "📨 Dispatching %s to %s from %s" message-type actor-name sender)
              (funcall handler data sender))
          
          (error
           (message "❌ Handler error in %s: %s" 
                   actor-name (error-message-string handler-err))
           
           ;; Send error response to sender
           (message-delivery-send sender
                                 "handler-error"
                                 `((error . ,(error-message-string handler-err))
                                   (failed-message-type . ,message-type))
                                 actor-name)))
      
      (message "⚠️ No handler for message type %s in actor %s" message-type actor-name))))

(defun message-delivery-test-system ()
  "Test the real message delivery system with acknowledgments"
  (interactive)
  
  ;; Register test handlers
  (message-delivery-register-handler "test-receiver" "ping"
                                    (lambda (data sender)
                                      (message "🏓 PING received from %s: %s" sender data)
                                      (message-delivery-send sender "pong" 
                                                            `((response . "pong back")
                                                              (original-data . ,data))
                                                            "test-receiver")))
  
  (message-delivery-register-handler "test-sender" "pong"
                                    (lambda (data sender)
                                      (message "🏓 PONG received from %s: %s" sender data)))
  
  (message-delivery-register-handler "test-sender" "delivery-failed"
                                    (lambda (data sender)
                                      (message "💀 Delivery failed: %s" data)))
  
  ;; Start inbox processing
  (message-delivery-start-actor-inbox "test-receiver")
  (message-delivery-start-actor-inbox "test-sender")
  
  ;; Send test messages
  (message "🧪 Starting message delivery test...")
  
  (run-with-timer 1 nil
                 (lambda ()
                   (message-delivery-send "test-receiver" "ping" 
                                         '((message . "Hello from sender")
                                           (test-id . 1))
                                         "test-sender")))
  
  (run-with-timer 3 nil
                 (lambda ()
                   (message-delivery-send "nonexistent-actor" "test"
                                         '((this . "should fail"))
                                         "test-sender")))
  
  (message "🧪 Test messages scheduled - check logs for results"))

(defun message-delivery-stop-all ()
  "Stop all message delivery processing"
  (interactive)
  
  (maphash (lambda (timer-name timer)
             (cancel-timer timer))
           message-delivery-timers)
  
  (clrhash message-delivery-timers)
  (clrhash message-acknowledgments)
  (clrhash last-message-ids)
  
  (message "🛑 All message delivery stopped"))

(provide 'real-message-delivery)