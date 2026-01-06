;;; homoiconic_learning_demo.el --- Demonstrate Redis homoiconicity with Elisp -*- lexical-binding: t; -*-

;; Demonstrate: Redis lists = Lisp s-expressions
;; Both are homoiconic: code and data have same representation

;;; Code:

(defun homoiconic-demo-store-lesson ()
  "Store a lesson as Redis list (homoiconic s-expression)."
  ;; Lisp: (progn (insert "hello") (point))
  ;; Redis: ["progn" ["insert" "hello"] ["point"]]

  (let ((lesson '((insert "Hello from homoiconic Redis")
                  (point)
                  (buffer-string))))

    ;; Store lesson structure in Redis as JSON (preserving s-exp structure)
    (shell-command-to-string
     (format "redis-cli SET homoiconic:lesson:1 '%s'"
             (json-encode lesson)))

    (message "✅ Stored lesson as Redis data: %S" lesson)
    lesson))

(defun homoiconic-demo-execute-lesson ()
  "Execute lesson from Redis (data becomes code)."
  ;; Get lesson from Redis
  (let* ((redis-data (shell-command-to-string
                      "redis-cli GET homoiconic:lesson:1"))
         (lesson (json-read-from-string redis-data)))

    (message "📖 Retrieved lesson from Redis: %S" lesson)

    ;; Execute the lesson (data AS code)
    (with-temp-buffer
      (let ((results '()))
        (dolist (form lesson)
          (let ((result (eval form)))
            (push result results)))
        (setq results (reverse results))
        (message "✅ Executed lesson, results: %S" results)
        results))))

(defun homoiconic-demo-improve-lesson ()
  "Improve lesson by modifying its structure (code modifying code)."
  ;; Get original lesson
  (let* ((redis-data (shell-command-to-string
                      "redis-cli GET homoiconic:lesson:1"))
         (lesson (json-read-from-string redis-data)))

    ;; IMPROVEMENT: Add logging (modify the code structure)
    (let ((improved-lesson
           `((message "Starting lesson...")
             ,@lesson
             (message "Lesson complete!"))))

      ;; Store improved version
      (shell-command-to-string
       (format "redis-cli SET homoiconic:lesson:1:improved '%s'"
               (json-encode improved-lesson)))

      (message "✅ Improved lesson (added logging): %S" improved-lesson)

      ;; Demonstrate: original vs improved
      (message "Original: %d forms" (length lesson))
      (message "Improved: %d forms" (length improved-lesson))

      improved-lesson)))

(defun homoiconic-demo-meta-property ()
  "Demonstrate the homoiconic property."
  (let ((code '(+ 1 2 3)))

    (message "")
    (message "🎯 Homoiconic Property Demonstration")
    (message "")
    (message "This IS data (a list):")
    (message "  %S" code)
    (message "")
    (message "This IS ALSO code (an s-expression):")
    (message "  Result of evaluation: %S" (eval code))
    (message "")
    (message "Same representation = Homoiconic!")
    (message "")

    ;; Store in Redis
    (shell-command-to-string
     (format "redis-cli SET homoiconic:demo '%s'" (json-encode code)))

    (message "Stored in Redis: redis-cli GET homoiconic:demo")
    (message "Redis sees it as: data")
    (message "Elisp sees it as: code")
    (message "BOTH are correct = Homoiconic!")))

(defun homoiconic-demo-learning-streams ()
  "Show how my learning system is homoiconic."
  (message "")
  (message "🎓 My Learning System is Homoiconic:")
  (message "")
  (message "1. Lessons stored in Redis streams = DATA")
  (message "2. Lessons can be executed = CODE")
  (message "3. Improvements modify lessons = CODE MODIFYING CODE")
  (message "4. Meta-learning modifies improvements = META-CODE")
  (message "")
  (message "All stored in Redis with same representation!")
  (message "")

  ;; Example: Store a self-modifying lesson
  (let ((self-modifying-lesson
         '(lambda ()
            (message "I can modify myself")
            ;; Get my own definition from Redis
            (let ((my-code (json-read-from-string
                            (shell-command-to-string
                             "redis-cli GET homoiconic:self"))))
              ;; Modify it
              (push '(message "I was modified!") my-code)
              ;; Store back
              (shell-command-to-string
               (format "redis-cli SET homoiconic:self '%s'"
                       (json-encode my-code)))
              my-code))))

    (message "Self-modifying lesson: %S" self-modifying-lesson)
    (message "This is HOMOICONICITY in action!")))

(defun homoiconic-demo-run-all ()
  "Run complete homoiconic demo."
  (interactive)
  (message "")
  (message "🚀 Redis Homoiconicity Demonstration")
  (message "")

  (homoiconic-demo-store-lesson)
  (sit-for 1)

  (homoiconic-demo-execute-lesson)
  (sit-for 1)

  (homoiconic-demo-improve-lesson)
  (sit-for 1)

  (homoiconic-demo-meta-property)
  (sit-for 1)

  (homoiconic-demo-learning-streams)

  (message "")
  (message "✅ Demo complete!")
  (message "")
  (message "Check Redis:")
  (message "  redis-cli GET homoiconic:lesson:1")
  (message "  redis-cli GET homoiconic:lesson:1:improved")
  (message "  redis-cli GET homoiconic:demo"))

;; Run when loaded with emacsclient
(when (not noninteractive)
  (homoiconic-demo-run-all))

(provide 'homoiconic-learning-demo)
;;; homoiconic_learning_demo.el ends here
