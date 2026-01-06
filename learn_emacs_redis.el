;;; learn_emacs_redis.el --- Learn Emacs Through Redis -*- lexical-binding: t; -*-

;; This file teaches me (Claude) how to use Emacs by:
;; 1. Executing Emacs commands
;; 2. Recording results to Redis
;; 3. Learning from the feedback loop

;;; Code:

(require 'json)

(defvar learn-redis-channel "emacs:learning"
  "Redis channel for learning interactions.")

(defun learn-redis-exec (redis-command)
  "Execute REDIS-COMMAND and return result."
  (string-trim
   (shell-command-to-string
    (format "redis-cli %s" redis-command))))

(defun learn-log-to-redis (lesson data)
  "Log LESSON with DATA to Redis."
  (let* ((json-str (json-encode data))
         ;; Properly escape for redis-cli
         (escaped-json (replace-regexp-in-string "\"" "\\\\\"" json-str))
         (timestamp (format-time-string "%s")))
    (learn-redis-exec
     (format "XADD %s '*' lesson \"%s\" data \"%s\" timestamp %s"
             learn-redis-channel
             lesson
             escaped-json
             timestamp))))

(defun learn-basic-commands ()
  "Learn basic Emacs commands by executing and logging them."
  (let ((lessons '()))

    ;; Lesson 1: Buffer creation
    (with-temp-buffer
      (insert "Hello, Redis!")
      (let ((result (list 'lesson "buffer-creation"
                          'action "Created temp buffer and inserted text"
                          'buffer-content (buffer-string)
                          'point (point))))
        (learn-log-to-redis "buffer-creation" result)
        (push result lessons)))

    ;; Lesson 2: Point movement
    (with-temp-buffer
      (insert "Line 1\nLine 2\nLine 3")
      (goto-char (point-min))
      (let ((start-point (point)))
        (forward-line 1)
        (let ((result (list 'lesson "point-movement"
                            'action "goto-char then forward-line"
                            'start-point start-point
                            'end-point (point)
                            'line-number (line-number-at-pos))))
          (learn-log-to-redis "point-movement" result)
          (push result lessons))))

    ;; Lesson 3: Text manipulation
    (with-temp-buffer
      (insert "Original text")
      (goto-char (point-min))
      (delete-char 8)
      (insert "Modified")
      (let ((result (list 'lesson "text-manipulation"
                          'action "delete-char and insert"
                          'result (buffer-string))))
        (learn-log-to-redis "text-manipulation" result)
        (push result lessons)))

    ;; Lesson 4: Search and replace
    (with-temp-buffer
      (insert "foo bar foo baz")
      (goto-char (point-min))
      (while (search-forward "foo" nil t)
        (replace-match "qux"))
      (let ((result (list 'lesson "search-replace"
                          'action "search-forward and replace-match"
                          'result (buffer-string))))
        (learn-log-to-redis "search-replace" result)
        (push result lessons)))

    ;; Lesson 5: Region operations
    (with-temp-buffer
      (insert "Region text here")
      (goto-char (point-min))
      (forward-word 1)
      (let ((start (point)))
        (forward-word 1)
        (let ((result (list 'lesson "region-operations"
                            'action "marked region between two words"
                            'region-start start
                            'region-end (point)
                            'region-text (buffer-substring start (point)))))
          (learn-log-to-redis "region-operations" result)
          (push result lessons))))

    (message "✅ Logged %d basic command lessons to Redis" (length lessons))
    lessons))

(defun learn-file-operations ()
  "Learn file operations through Redis logging."
  (let ((test-file "/tmp/emacs_learn_test.txt")
        (lessons '()))

    ;; Lesson: File writing
    (with-temp-buffer
      (insert "Test content for learning")
      (write-file test-file)
      (let ((result (list 'lesson "file-write"
                          'action "write-file"
                          'file test-file
                          'success (file-exists-p test-file))))
        (learn-log-to-redis "file-write" result)
        (push result lessons)))

    ;; Lesson: File reading
    (with-temp-buffer
      (insert-file-contents test-file)
      (let ((result (list 'lesson "file-read"
                          'action "insert-file-contents"
                          'file test-file
                          'content (buffer-string))))
        (learn-log-to-redis "file-read" result)
        (push result lessons)))

    ;; Cleanup
    (delete-file test-file)

    (message "✅ Logged %d file operation lessons to Redis" (length lessons))
    lessons))

(defun learn-mode-operations ()
  "Learn about major and minor modes."
  (let ((lessons '()))

    ;; Lesson: Detecting major mode
    (with-temp-buffer
      (emacs-lisp-mode)
      (let ((result (list 'lesson "major-mode"
                          'action "emacs-lisp-mode"
                          'mode (symbol-name major-mode))))
        (learn-log-to-redis "major-mode" result)
        (push result lessons)))

    ;; Lesson: Syntax parsing
    (with-temp-buffer
      (emacs-lisp-mode)
      (insert "(defun foo () \"docstring\" 42)")
      (goto-char (point-min))
      (forward-char 1)
      (let ((result (list 'lesson "syntax-parsing"
                          'action "syntax-ppss at different positions"
                          'in-string (nth 3 (syntax-ppss))
                          'paren-depth (nth 0 (syntax-ppss)))))
        (learn-log-to-redis "syntax-parsing" result)
        (push result lessons)))

    (message "✅ Logged %d mode lessons to Redis" (length lessons))
    lessons))

(defun learn-interactive-commands ()
  "Learn how interactive commands work."
  (let ((lessons '()))

    (let ((result (list 'lesson "interactive-function"
                        'concept "Functions with (interactive) can be called via M-x"
                        'example "(defun my-cmd () (interactive) (message \"Hello\"))")))
      (learn-log-to-redis "interactive-function" result)
      (push result lessons))

    (let ((result (list 'lesson "interactive-args"
                        'concept "(interactive \"sPrompt: \") gets string input"
                        'example "(defun greet (name) (interactive \"sName: \") (message \"Hi %s\" name))")))
      (learn-log-to-redis "interactive-args" result)
      (push result lessons))

    (message "✅ Logged %d interactive command lessons to Redis" (length lessons))
    lessons))

(defun learn-redis-operations ()
  "Learn Redis operations from within Emacs."
  (let ((lessons '()))

    ;; Test Redis connectivity
    (let* ((ping-result (learn-redis-exec "PING"))
           (result (list 'lesson "redis-ping"
                         'action "Test Redis connection"
                         'command "redis-cli PING"
                         'response ping-result
                         'connected (string= ping-result "PONG"))))
      (learn-log-to-redis "redis-ping" result)
      (push result lessons))

    ;; Set and get a key
    (learn-redis-exec "SET emacs:test:key 'Hello from Emacs'")
    (let* ((get-result (learn-redis-exec "GET emacs:test:key"))
           (result (list 'lesson "redis-set-get"
                         'action "SET then GET"
                         'key "emacs:test:key"
                         'value get-result)))
      (learn-log-to-redis "redis-set-get" result)
      (push result lessons))

    ;; List current streams
    (let* ((keys-result (learn-redis-exec "KEYS *:*"))
           (result (list 'lesson "redis-keys"
                         'action "List all keys with pattern"
                         'pattern "*:*"
                         'found (split-string keys-result "\n" t))))
      (learn-log-to-redis "redis-keys" result)
      (push result lessons))

    (message "✅ Logged %d Redis operation lessons" (length lessons))
    lessons))

(defun learn-all-emacs-basics ()
  "Execute all learning functions and report to Redis."
  (interactive)
  (message "🎓 Starting Emacs learning session via Redis...")

  (let ((total-lessons 0)
        (start-time (current-time)))

    (setq total-lessons (+ total-lessons (length (learn-basic-commands))))
    (setq total-lessons (+ total-lessons (length (learn-file-operations))))
    (setq total-lessons (+ total-lessons (length (learn-mode-operations))))
    (setq total-lessons (+ total-lessons (length (learn-interactive-commands))))
    (setq total-lessons (+ total-lessons (length (learn-redis-operations))))

    (let ((elapsed (float-time (time-subtract (current-time) start-time))))
      (message "")
      (message "🎓 Learning complete!")
      (message "   - %d total lessons logged to Redis" total-lessons)
      (message "   - Completed in %.2f seconds" elapsed)
      (message "   - Stream: %s" learn-redis-channel)
      (message "")
      (message "📊 View lessons with:")
      (message "   redis-cli XREAD COUNT 100 STREAMS %s 0" learn-redis-channel)

      ;; Log summary
      (learn-log-to-redis "session-complete"
                          (list 'total-lessons total-lessons
                                'elapsed-seconds elapsed
                                'timestamp (format-time-string "%Y-%m-%d %H:%M:%S")
                                'status "complete")))))

(defun learn-query-redis-lessons ()
  "Query and display lessons from Redis."
  (interactive)
  (let* ((result (learn-redis-exec (format "XREAD COUNT 100 STREAMS %s 0" learn-redis-channel)))
         (lines (split-string result "\n" t)))
    (message "📚 Lessons stored in Redis:")
    (message "%s" result)
    (message "")
    (message "Total entries: %d" (length lines))))

;; Run the learning session when loaded in batch mode
(when noninteractive
  (learn-all-emacs-basics))

(provide 'learn-emacs-redis)
;;; learn_emacs_redis.el ends here
