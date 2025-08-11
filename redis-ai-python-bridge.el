;;; redis-ai-python-bridge.el --- Bridge to Python AI functions for Redis AI Emacs mode

;;; Code:

(require 'json)

(defvar redis-ai-python-cli-path "/Users/jonathanhill/src/redis-ai-challenge/redis_ai_cli.py"
  "Path to the redis_ai_cli.py script.")

(defun redis-ai-call-python-cli (command &rest args)
  "Call the Python CLI script with COMMAND and ARGS, returning parsed JSON output."
  (let* ((command-list (cons redis-ai-python-cli-path (cons command args)))
         (full-command (string-join (cons "python3" command-list) " "))
         (raw-output nil))

    (message "Python CLI command: %S" full-command)

    (setq raw-output (shell-command-to-string full-command))

    (message "Python CLI raw output: %S" raw-output)

    (let* ((trimmed-output (string-trim raw-output))
           (sanitized-output (replace-regexp-in-string "[\x00-\x08\x0B\x0C\x0E-\x1F]" "" trimmed-output)))
      (message "Python CLI trimmed output: %S" trimmed-output)
      (message "Python CLI sanitized output: %S" sanitized-output)

      (with-temp-file "/tmp/redis-ai-raw-output.txt"
        (insert raw-output))
      (with-temp-file "/tmp/redis-ai-trimmed-output.txt"
        (insert trimmed-output))
      (with-temp-file "/tmp/redis-ai-sanitized-output.txt"
        (insert sanitized-output))

      (condition-case err
          (json-read-from-string sanitized-output)
        (error
         (message "❌ Error parsing Python CLI output: %s" (error-message-string err))
         (message "Raw output was: %S" raw-output)
         (message "Trimmed output was: %S" trimmed-output)
         (message "Sanitized output was: %S" sanitized-output)
         (error "Python CLI output parsing failed"))))))

(defun redis-ai-classify-text (text)
  "Classify TEXT using the Python AI function."
  (interactive "sText to classify: ")
  (let ((result (redis-ai-call-python-cli "classify_text" text)))
    (message "Classification result: %S" result)
    result))

(defun redis-ai-demonstrate-homoiconicity ()
  "Run the Python demo for Redis homoiconicity."
  (interactive)
  (let ((result (redis-ai-call-python-cli "demonstrate_homoiconicity")))
    (message "Homoiconicity demo result: %S" result)
    result))

(defun redis-ai-demonstrate-ml-coordination ()
  "Run the Python demo for ML coordination."
  (interactive)
  (let ((result (redis-ai-call-python-cli "demonstrate_ml_coordination")))
    (message "ML coordination demo result: %S" result)
    result))

(defun redis-ai-demonstrate-intelligent-data-manipulation ()
  "Run the Python demo for intelligent data manipulation."
  (interactive)
  (let ((result (redis-ai-call-python-cli "demonstrate_intelligent_data_manipulation")))
    (message "Intelligent data manipulation demo result: %S" result)
    result))

(defun redis-ai-demonstrate-real-time-learning ()
  "Run the Python demo for real-time learning."
  (interactive)
  (let ((result (redis-ai-call-python-cli "demonstrate_real-time-learning")))
    (message "Real-time learning demo result: %S" result)
    result))

(provide 'redis-ai-python-bridge)
;;; redis-ai-python-bridge.el ends here