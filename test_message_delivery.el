;;; test_message_delivery.el --- Test message delivery without dependencies

;; -*- lexical-binding: t -*-

;; Mock the Redis functions for testing
(defun redis-send-stream-message (stream fields)
  "Mock Redis send - just return success"
  (message "📤 Mock Redis: %s <- %s" stream fields)
  "mock-id-123")

(defun redis-read-stream-messages (stream last-id count)
  "Mock Redis read - return test message"
  (when (string= stream "actor:test-receiver:inbox")
    (list (list :id "1754177000000-0"
                :stream stream
                :fields '(("id" . "test-msg-1")
                         ("type" . "ping")
                         ("data" . "{\"message\":\"Hello\",\"test-id\":1}")
                         ("sender" . "test-sender")
                         ("timestamp" . "1754177000"))))))

;; Load the actual message delivery system
(load-file "real_message_delivery.el")

;; Test it
(defun run-message-test ()
  "Run a simple message test"
  (message "🧪 Testing message delivery...")
  
  ;; Register handlers
  (message-delivery-register-handler "test-receiver" "ping"
                                    (lambda (data sender)
                                      (message "✅ Received ping: %s from %s" data sender)))
  
  ;; Start inbox
  (message-delivery-start-actor-inbox "test-receiver")
  
  ;; Send message
  (message-delivery-send "test-receiver" "ping" '((test . "data")) "test-sender")
  
  ;; Wait and stop
  (run-with-timer 3 nil 
                 (lambda ()
                   (message-delivery-stop-all)
                   (message "✅ Test completed"))))

(run-message-test)