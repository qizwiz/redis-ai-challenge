;;; test_error_capture.el --- Test minibuffer error capture without async

;; -*- lexical-binding: t -*-

(defvar test-error-log-buffer "*test-error-log*")
(defvar test-original-message-function nil)

(defun test-error-log (error-message)
  "Log errors to test buffer"
  (with-current-buffer (get-buffer-create test-error-log-buffer)
    (goto-char (point-max))
    (insert (format "[%s] ERROR: %s\n" 
                    (format-time-string "%H:%M:%S")
                    error-message))))

(defun test-intercept-message (original-message &rest args)
  "Intercept message function to catch errors"
  (let ((message-text (apply 'format args)))
    ;; Log errors to our error buffer
    (when (or (string-match "ERROR" message-text)
              (string-match "error" message-text)
              (string-match "Error" message-text))
      (test-error-log message-text))
    
    ;; Call original message function
    (apply original-message args)))

(defun test-setup-error-capture ()
  "Setup error capture from minibuffer"
  (unless test-original-message-function
    (setq test-original-message-function (symbol-function 'message))
    (fset 'message 
          (lambda (&rest args)
            (apply 'test-intercept-message 
                   test-original-message-function args))))
  (message "✅ Error capture enabled"))

(defun test-restore-error-capture ()
  "Restore original message function"
  (when test-original-message-function
    (fset 'message test-original-message-function)
    (setq test-original-message-function nil))
  (message "✅ Error capture disabled"))

(defun test-generate-errors ()
  "Generate some test errors to verify capture works"
  (message "This is a normal message")
  (message "ERROR: This is a test error")
  (message "Something went wrong - error occurred")
  (message "Error in processing")
  (message "Another normal message"))

(defun test-run-error-capture-demo ()
  "Run a complete demo of error capture"
  (interactive)
  
  ;; Create error log buffer
  (with-current-buffer (get-buffer-create test-error-log-buffer)
    (erase-buffer)
    (insert "🚨 TEST ERROR CAPTURE LOG\n")
    (insert "==========================\n\n"))
  
  ;; Setup error capture
  (test-setup-error-capture)
  
  ;; Generate test messages including errors
  (test-generate-errors)
  
  ;; Show results
  (pop-to-buffer test-error-log-buffer)
  
  ;; Restore original message function
  (test-restore-error-capture)
  
  ;; Report results
  (with-current-buffer test-error-log-buffer
    (goto-char (point-max))
    (insert "\n✅ Error capture test completed\n"))
  
  (message "🎯 Error capture test completed - check *test-error-log* buffer"))

(provide 'test-error-capture)

;; Usage: (test-run-error-capture-demo)