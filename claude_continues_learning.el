;;; claude_continues_learning.el --- Continue learning Emacs with facade vision -*- lexical-binding: t; -*-

;; Now that I have complete macOS facade, I can see EVERYTHING while I learn

;;; Code:

(require 'json)

;; Load the facade
(load-file (expand-file-name "redis-ai-challenge/integrated_facade.el" "~/src/"))

(defvar claude-learning-stream "claude:emacs:learning"
  "Redis stream logging my Emacs learning journey.")

(defun claude-redis (cmd)
  "Execute Redis CMD."
  (string-trim (shell-command-to-string (format "redis-cli %s" cmd))))

(defun claude-log-lesson (lesson-name what-i-learned &optional evidence)
  "Log a lesson I learned to Redis."
  (let ((timestamp (format-time-string "%s"))
        (escaped-learning (replace-regexp-in-string "\"" "\\\\\"" what-i-learned))
        (escaped-evidence (if evidence
                             (replace-regexp-in-string "\"" "\\\\\"" evidence)
                           "verified")))
    (claude-redis
     (format "XADD %s '*' ts %s lesson \"%s\" learned \"%s\" evidence \"%s\""
             claude-learning-stream
             timestamp
             lesson-name
             escaped-learning
             escaped-evidence))

    ;; Also capture facade state at time of learning
    (facade-capture-all)

    (message "📚 Logged: %s" lesson-name)))

(defun claude-learn-buffer-commands ()
  "Learn and verify buffer manipulation commands."
  (interactive)

  (message "📚 Learning buffer commands with facade verification...")

  ;; Lesson 1: Create and switch to buffer
  (let ((test-buffer "*claude-learning-test*"))
    (with-current-buffer (get-buffer-create test-buffer)
      (erase-buffer)
      (insert "I am learning Emacs!\n")
      (insert "Buffer: " (buffer-name) "\n")
      (insert "Point: " (number-to-string (point)) "\n")

      (claude-log-lesson
       "create-and-populate-buffer"
       "Created buffer, inserted text, queried buffer-name and point"
       (format "Buffer: %s, Point: %d, Content length: %d"
               (buffer-name)
               (point)
               (buffer-size))))

    ;; Lesson 2: Count all buffers
    (let ((buffer-count (length (buffer-list))))
      (claude-log-lesson
       "count-buffers"
       (format "There are %d buffers open" buffer-count)
       (format "buffer-list returned %d items" buffer-count)))

    ;; Lesson 3: Get buffer content
    (with-current-buffer test-buffer
      (let ((content (buffer-string)))
        (claude-log-lesson
         "extract-buffer-content"
         "Used buffer-string to extract all text"
         (format "Got %d characters: %s"
                 (length content)
                 (substring content 0 (min 50 (length content)))))))

    ;; Lesson 4: Navigate point
    (with-current-buffer test-buffer
      (goto-char (point-min))
      (let ((start-point (point)))
        (forward-line 2)
        (claude-log-lesson
         "navigate-with-point"
         "Used goto-char and forward-line to navigate"
         (format "Moved from point %d to %d" start-point (point)))))

    ;; Lesson 5: Search in buffer
    (with-current-buffer test-buffer
      (goto-char (point-min))
      (when (search-forward "learning" nil t)
        (claude-log-lesson
         "search-forward"
         "Found text using search-forward"
         (format "Found 'learning' at point %d" (point)))))

    (message "✅ Learned 5 buffer commands, all logged to Redis")))

(defun claude-learn-window-commands ()
  "Learn window manipulation with facade tracking."
  (interactive)

  (message "📚 Learning window commands...")

  ;; Lesson 1: Count windows
  (let ((window-count (length (window-list))))
    (claude-log-lesson
     "count-windows"
     (format "Currently %d windows open" window-count)
     (format "window-list length: %d" window-count)))

  ;; Lesson 2: Split window
  (let ((before-count (length (window-list))))
    (split-window-below)
    (let ((after-count (length (window-list))))
      (claude-log-lesson
       "split-window-below"
       "Split window vertically"
       (format "Windows before: %d, after: %d" before-count after-count))

      ;; Clean up
      (when (> after-count before-count)
        (delete-window))))

  ;; Lesson 3: Window dimensions
  (let ((width (window-width))
        (height (window-height)))
    (claude-log-lesson
     "window-dimensions"
     (format "Current window is %dx%d characters" width height)
     (format "window-width: %d, window-height: %d" width height)))

  (message "✅ Learned 3 window commands"))

(defun claude-learn-file-operations ()
  "Learn file operations with verification."
  (interactive)

  (message "📚 Learning file operations...")

  (let ((test-file "/tmp/claude-emacs-test.txt"))

    ;; Lesson 1: Write file
    (with-temp-buffer
      (insert "Claude learned to write files!\n")
      (insert "Timestamp: " (current-time-string) "\n")
      (write-file test-file)
      (claude-log-lesson
       "write-file"
       "Created file with write-file"
       (format "Wrote to %s, size: %d bytes"
               test-file
               (file-attribute-size (file-attributes test-file)))))

    ;; Lesson 2: Read file
    (with-temp-buffer
      (insert-file-contents test-file)
      (let ((content (buffer-string)))
        (claude-log-lesson
         "read-file"
         "Read file contents with insert-file-contents"
         (format "Read %d characters from %s"
                 (length content)
                 test-file))))

    ;; Lesson 3: File existence
    (claude-log-lesson
     "check-file-exists"
     "Used file-exists-p to verify file"
     (format "file-exists-p %s: %s"
             test-file
             (if (file-exists-p test-file) "YES" "NO")))

    ;; Lesson 4: Delete file
    (delete-file test-file)
    (claude-log-lesson
     "delete-file"
     "Deleted file and verified removal"
     (format "file-exists-p after delete: %s"
             (if (file-exists-p test-file) "still exists!" "gone"))))

  (message "✅ Learned 4 file operations"))

(defun claude-show-learning-progress ()
  "Show my learning progress from Redis."
  (interactive)

  (let ((lesson-count (string-to-number
                      (or (claude-redis (format "XLEN %s" claude-learning-stream))
                          "0"))))

    (with-current-buffer (get-buffer-create "*Claude Learning Progress*")
      (erase-buffer)
      (insert "╔════════════════════════════════════════════════════╗\n")
      (insert "║         CLAUDE'S EMACS LEARNING JOURNEY           ║\n")
      (insert "╚════════════════════════════════════════════════════╝\n\n")

      (insert (format "📚 Total lessons learned: %d\n\n" lesson-count))

      (if (> lesson-count 0)
          (let* ((cmd (format "XREAD COUNT 10 STREAMS %s 0" claude-learning-stream))
                 (result (claude-redis cmd)))
            (insert "Recent lessons:\n")
            (insert "─────────────────────────────────────────────────\n")
            (insert result)
            (insert "\n\n"))
        (insert "No lessons logged yet. Run:\n")
        (insert "  M-x claude-learn-buffer-commands\n")
        (insert "  M-x claude-learn-window-commands\n")
        (insert "  M-x claude-learn-file-operations\n"))

      (insert "\n💾 All learning stored in Redis stream: ")
      (insert claude-learning-stream)

      (goto-char (point-min))
      (special-mode))

    (switch-to-buffer "*Claude Learning Progress*")))

(defun claude-learn-everything ()
  "Run all learning modules with facade tracking."
  (interactive)

  (message "🚀 Starting comprehensive learning session...")

  ;; Capture initial state
  (facade-capture-all)
  (message "📸 Captured initial system state")
  (sit-for 1)

  ;; Learn buffer commands
  (claude-learn-buffer-commands)
  (sit-for 1)

  ;; Learn window commands
  (claude-learn-window-commands)
  (sit-for 1)

  ;; Learn file operations
  (claude-learn-file-operations)
  (sit-for 1)

  ;; Capture final state
  (facade-capture-all)
  (message "📸 Captured final system state")

  ;; Show progress
  (claude-show-learning-progress)

  (message "✅ Learning session complete! Check *Claude Learning Progress* buffer"))

;; Keybindings
(global-set-key (kbd "C-c C-l b") 'claude-learn-buffer-commands)
(global-set-key (kbd "C-c C-l w") 'claude-learn-window-commands)
(global-set-key (kbd "C-c C-l f") 'claude-learn-file-operations)
(global-set-key (kbd "C-c C-l a") 'claude-learn-everything)
(global-set-key (kbd "C-c C-l p") 'claude-show-learning-progress)

(provide 'claude-continues-learning)
;;; claude_continues_learning.el ends here
