(defun my-test-filter (proc string)
  (message "My test filter: %s" string))

(defun my-test-sentinel (proc event)
  (message "My test sentinel: %s" event))

(setq my-test-connection
      (make-network-process
       :name "my-test-redis"
       :host "localhost"
       :port 6379
       :filter 'my-test-filter
       :sentinel 'my-test-sentinel))

(message "Minimal network process created.")