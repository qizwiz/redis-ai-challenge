;;; real_redis_parser.el --- Actually working Redis stream parser

;; -*- lexical-binding: t -*-

(defun redis-parse-xread-response (output)
  "Parse actual Redis XREAD response format
  
  Redis XREAD returns:
  stream-name
  message-id
  field1
  value1
  field2
  value2
  ..."
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

(defun redis-send-stream-message (stream-name fields)
  "Send message to Redis stream with proper error handling
  
  Returns the message ID on success, nil on failure"
  (let* ((field-args (mapconcat 
                      (lambda (kv) 
                        (format "%s %s" 
                                (shell-quote-argument (format "%s" (car kv)))
                                (shell-quote-argument (format "%s" (cdr kv)))))
                      fields " "))
         (cmd (format "redis-cli XADD %s '*' %s" 
                     (shell-quote-argument stream-name)
                     field-args)))
    
    (condition-case err
        (let ((result (shell-command-to-string cmd)))
          (setq result (string-trim result))
          (if (string-match-p "^[0-9]+-[0-9]+$" result)
              result ; Return message ID
            (progn
              (message "Redis XADD failed: %s" result)
              nil)))
      (error
       (message "Redis command error: %s" (error-message-string err))
       nil))))

(defun redis-read-stream-messages (stream-name last-id &optional count)
  "Read messages from Redis stream after last-id
  
  Returns list of parsed messages or nil on error"
  (let* ((count-arg (if count (format "COUNT %d" count) ""))
         (cmd (format "redis-cli XREAD %s STREAMS %s %s"
                     count-arg
                     (shell-quote-argument stream-name)
                     (shell-quote-argument (or last-id "0")))))
    
    (condition-case err
        (let ((output (shell-command-to-string cmd)))
          (redis-parse-xread-response output))
      (error
       (message "Redis XREAD error: %s" (error-message-string err))
       nil))))

(defun redis-test-parser ()
  "Test the Redis parser with real data"
  (interactive)
  
  ;; Send a test message
  (let ((msg-id (redis-send-stream-message "test:parser" 
                                          '((type . "test")
                                            (data . "hello world")
                                            (timestamp . 12345)))))
    (if msg-id
        (progn
          (message "✅ Sent message: %s" msg-id)
          
          ;; Read it back
          (let ((messages (redis-read-stream-messages "test:parser" "0" 10)))
            (if messages
                (progn
                  (message "✅ Received %d messages" (length messages))
                  (dolist (msg messages)
                    (let ((fields (plist-get msg :fields)))
                      (message "Message ID: %s, Type: %s, Data: %s"
                              (plist-get msg :id)
                              (alist-get "type" fields nil nil #'string=)
                              (alist-get "data" fields nil nil #'string=))))
                  t) ; Success
              (message "❌ Failed to read messages")
              nil)))
      (message "❌ Failed to send message")
      nil)))

(provide 'real-redis-parser)