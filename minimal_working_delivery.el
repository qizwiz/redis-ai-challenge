;;; minimal_working_delivery.el --- ACTUALLY working message delivery

;; -*- lexical-binding: t -*-

(require 'cl-lib)
(require 'json)

;; Simple Redis parser (copied from working version)
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

(defvar msg-handlers (make-hash-table :test 'equal)
  "Message handlers")

(defvar msg-timers (make-hash-table :test 'equal)
  "Processing timers")

(defvar msg-last-ids (make-hash-table :test 'equal)
  "Last processed message ID per stream")

(defun msg-register-handler (actor-name message-type handler-func)
  "Register handler"
  (let ((actor-handlers (or (gethash actor-name msg-handlers)
                           (make-hash-table :test 'equal))))
    (puthash message-type handler-func actor-handlers)
    (puthash actor-name actor-handlers msg-handlers)
    (message "📋 Handler: %s.%s" actor-name message-type)))

(defun msg-send (recipient message-type data sender)
  "Send message"
  (let* ((stream-name (format "actor:%s:inbox" recipient))
         (fields `((type . ,message-type)
                   (data . ,(json-encode data))
                   (sender . ,sender)
                   (timestamp . ,(float-time))))
         (cmd (format "redis-cli XADD %s '*' %s"
                     (shell-quote-argument stream-name)
                     (mapconcat (lambda (kv) 
                                 (format "%s %s" 
                                        (shell-quote-argument (format "%s" (car kv)))
                                        (shell-quote-argument (format "%s" (cdr kv)))))
                               fields " "))))
    
    (let ((result (shell-command-to-string cmd)))
      (if (string-match-p "^[0-9]+-[0-9]+$" (string-trim result))
          (progn
            (message "📨 Sent %s to %s: %s" message-type recipient (string-trim result))
            (string-trim result))
        (message "❌ Send failed: %s" result)))))

(defun msg-process-inbox (actor-name)
  "Process messages for actor"
  (let* ((stream-name (format "actor:%s:inbox" actor-name))
         (last-id (or (gethash stream-name msg-last-ids) "0"))
         (cmd (format "redis-cli XREAD COUNT 10 STREAMS %s %s"
                     (shell-quote-argument stream-name)
                     (shell-quote-argument last-id)))
         (output (shell-command-to-string cmd)))
    
    (when (and output 
               (not (string-empty-p output))
               (not (string-match-p "(nil)" output)))
      
      (let ((messages (redis-parse-xread-response output)))
        (dolist (msg messages)
          (let* ((msg-id (plist-get msg :id))
                 (fields (plist-get msg :fields))
                 (message-type (alist-get "type" fields nil nil #'string=))
                 (data-json (alist-get "data" fields nil nil #'string=))
                 (sender (alist-get "sender" fields nil nil #'string=)))
            
            ;; Update last processed ID BEFORE processing to prevent reprocessing
            (puthash stream-name msg-id msg-last-ids)
            
            (when (and message-type data-json sender)
              (condition-case err
                  (let* ((data (json-read-from-string data-json))
                         (actor-handlers (gethash actor-name msg-handlers))
                         (handler (when actor-handlers (gethash message-type actor-handlers))))
                    
                    (if handler
                        (progn
                          (message "📨 %s -> %s: %s [%s]" sender actor-name message-type msg-id)
                          (funcall handler data sender))
                      (message "⚠️ No handler: %s.%s" actor-name message-type)))
                
                (error
                 (message "❌ Dispatch error: %s" (error-message-string err)))))))))))

(defun msg-start-processing (actor-name)
  "Start processing"
  (let ((timer-key actor-name))
    (msg-stop-processing actor-name)
    (let ((timer (run-with-timer 0 1 
                                `(lambda () (msg-process-inbox ,actor-name)))))
      (puthash timer-key timer msg-timers)
      (message "📥 Started: %s" actor-name))))

(defun msg-stop-processing (actor-name)
  "Stop processing"
  (let ((timer (gethash actor-name msg-timers)))
    (when timer
      (cancel-timer timer)
      (remhash actor-name msg-timers))))

(defun msg-stop-all ()
  "Stop all"
  (maphash (lambda (_key timer) (cancel-timer timer)) msg-timers)
  (clrhash msg-timers)
  (clrhash msg-last-ids)
  (message "🛑 All stopped"))

(defun msg-test ()
  "Test the system"
  (interactive)
  
  ;; Register handlers
  (msg-register-handler "ping-actor" "ping"
                       (lambda (data sender)
                         (message "🏓 PING from %s: %s" sender data)
                         (msg-send sender "pong" 
                                  `((reply . "pong back")
                                    (original . ,data))
                                  "ping-actor")))
  
  (msg-register-handler "test-sender" "pong"
                       (lambda (data sender)
                         (message "🏓 PONG from %s: %s" sender data)))
  
  ;; Start processing
  (msg-start-processing "ping-actor")
  (msg-start-processing "test-sender")
  
  ;; Send test message after 1 second
  (run-with-timer 1 nil
                 (lambda ()
                   (message "🧪 Sending test message...")
                   (msg-send "ping-actor" "ping" 
                            '((message . "Hello ping!")
                              (test . 123))
                            "test-sender")))
  
  (message "🧪 Test started"))

(provide 'minimal-working-delivery)