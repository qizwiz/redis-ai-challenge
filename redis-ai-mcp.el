;;; redis-ai-mcp.el --- MCP Lisp Integration functions for Redis AI Emacs mode

;;; Code:

(require 'json)
(require 'redis-ai-core) ;; Ensure redis-ai-send-command is available

(defcustom redis-ai-mcp-server-port 8881
  "MCP Redis Lisp server port"
  :type 'integer
  :group 'redis-ai)

(defun redis-ai-send-ai-command (function-name args)
  "Send an AI command to the redis-ai-service via Redis Stream."
  (let* ((command-id (format "cmd-%s" (int-to-string (round (* (float-time) 1000))))) 
         (command-payload (json-encode (list (cons 'function function-name) (cons 'args args) (cons 'id command-id)))))
    ;; Corrected XADD format: XADD <stream-key> * <field> <value>
    (redis-ai-send-command (format "XADD ai:commands * payload %s" command-payload))
    (message "Sent AI command: %s with ID: %s" function-name command-id)
    command-id))

(defun redis-ai-get-ai-result (command-id &optional timeout)
  "Get the result for a specific AI command from the ai:results stream."
  (let ((start-time (float-time))
        (response nil)
        (parsed-response nil))
    (while (and (not parsed-response) (or (not timeout) (< (- (float-time) start-time) timeout)))
      (setq response (redis-ai-send-command (format "XREADGROUP GROUP ai_group ai_consumer COUNT 1 BLOCK 1000 STREAMS ai:results >")))
      (message "Raw Redis response from XREADGROUP: %S" response) ;; New debugging line
      (if (string-empty-p response) ;; Check if response is empty
          (setq response nil) ;; If empty, set to nil to continue loop
        (setq parsed-response (redis-ai-parse-xreadgroup-response response)) ;; Parse the response
        (message "Parsed Redis response: %S" parsed-response)
        (if parsed-response
            (condition-case err
                (json-read-from-string parsed-response)
              (error
               (message "❌ Error parsing AI result JSON: %s" (error-message-string err))
               (message "Problematic JSON string: %S" parsed-response)
               (setq parsed-response nil))))))
    parsed-response))

(defun redis-ai-classify-text (text)
  "Classify TEXT using the Python AI function via Redis Streams."
  (interactive "sText to classify: ")
  (let* ((command-id (redis-ai-send-ai-command "classify_text" (list text)))
         (result (redis-ai-get-ai-result command-id)))
    (message "Classification result: %S" result)
    result))

(defun redis-ai-demonstrate-homoiconicity ()
  "Run the Python demo for Redis homoiconicity via Redis Streams."
  (interactive)
  (let* ((command-id (redis-ai-send-ai-command "demonstrate_homoiconicity" nil))
         (result (redis-ai-get-ai-result command-id)))
    (message "Homoiconicity demo result: %S" result)
    result))

(defun redis-ai-demonstrate-ml-coordination ()
  "Run the Python demo for ML coordination via Redis Streams."
  (interactive)
  (let* ((command-id (redis-ai-send-ai-command "demonstrate_ml_coordination" nil))
         (result (redis-ai-get-ai-result command-id)))
    (message "ML coordination demo result: %S" result)
    result))

(defun redis-ai-demonstrate-intelligent-data-manipulation ()
  "Run the Python demo for intelligent data manipulation via Redis Streams."
  (interactive)
  (let* ((command-id (redis-ai-send-ai-command "demonstrate_intelligent_data_manipulation" nil))
         (result (redis-ai-get-ai-result command-id)))
    (message "Intelligent data manipulation demo result: %S" result)
    result))

(defun redis-ai-demonstrate-real-time-learning ()
  "Run the Python demo for real-time learning via Redis Streams."
  (interactive)
  (let* ((command-id (redis-ai-send-ai-command "demonstrate_real-time-learning" nil))
         (result (redis-ai-get-ai-result command-id)))
    (message "Real-time learning demo result: %S" result)
    result))

(defun redis-ai-execute-lisp (lisp-expr)
  "Execute LISP-EXPR using the MCP Redis Lisp server via Redis Streams."
  (interactive "sLisp expression: ")
  (let* ((json-expr (json-encode (read lisp-expr)))
         (command-id (redis-ai-send-ai-command "execute_lisp" (list json-expr)))
         (result (redis-ai-get-ai-result command-id)))
    (message "Executing Lisp result: %S" result)
    result))

(defun redis-ai-store-lisp-code (key lisp-code)
  "Store LISP-CODE under KEY in Redis for later execution via Redis Streams."
  (interactive "sKey: 
  sLisp code: ")
  (let* ((json-code (json-encode (read lisp-code)))
         (command-id (redis-ai-send-ai-command "store_lisp_code" (list key json-code)))
         (result (redis-ai-get-ai-result command-id)))
    (message "Stored Lisp code result: %S" result)
    result))

(defun redis-ai-execute-stored-lisp (key)
  "Execute Lisp code stored under KEY via Redis Streams."
  (interactive "sKey: ")
  (let* ((command-id (redis-ai-send-ai-command "execute_stored_lisp" (list key)))
         (result (redis-ai-get-ai-result command-id)))
    (message "Executing stored Lisp code result: %S" result)
    result))

(defun redis-ai-send-mcp-command (tool-name args)
  "Send MCP command to Redis Lisp server via Redis Streams."
  ;; This function now acts as a wrapper to send commands to the AI service
  (redis-ai-send-ai-command tool-name args))

(provide 'redis-ai-mcp)
;;; redis-ai-mcp.el ends here