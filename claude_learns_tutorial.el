;;; claude_learns_tutorial.el --- Claude learns Emacs through tutorial with full state tracking -*- lexical-binding: t; -*-

;; I (Claude) am learning Emacs by doing the tutorial with complete vision via facade

;;; Code:

(require 'json)

(defvar claude-tutorial-buffer nil
  "The tutorial buffer I'm learning from.")

(defvar claude-tutorial-marker nil
  "Marker tracking my position in tutorial.")

(defvar claude-learning-stream "claude:tutorial:learning"
  "Redis stream for my learning.")

(defun claude-redis-log (event data)
  "Log EVENT with DATA to Redis."
  (let* ((json-str (json-encode data))
         (escaped (replace-regexp-in-string "\"" "\\\\\"" json-str))
         (cmd (format "redis-cli XADD %s '*' event \"%s\" data \"%s\" timestamp %s"
                     claude-learning-stream
                     event
                     escaped
                     (format-time-string "%s"))))
    (shell-command-to-string cmd)))

(defun claude-start-tutorial ()
  "Start the tutorial with full state tracking."
  (interactive)

  ;; Open tutorial
  (help-with-tutorial)
  (setq claude-tutorial-buffer (current-buffer))
  (setq claude-tutorial-marker (point-marker))

  ;; Log initial state
  (claude-redis-log "tutorial-started"
                    (list :buffer (buffer-name)
                          :initial-point (point)
                          :buffer-size (buffer-size)
                          :mode (symbol-name major-mode)))

  (message "🎓 Claude's Tutorial Session Started")
  (message "   Buffer: %s" (buffer-name))
  (message "   Starting point: %d" (point))
  (message "   I will track my position throughout"))

(defun claude-get-current-state ()
  "Get complete current state for facade."
  (when (buffer-live-p claude-tutorial-buffer)
    (with-current-buffer claude-tutorial-buffer
      (list :buffer (buffer-name)
            :point (point)
            :line (line-number-at-pos)
            :column (current-column)
            :char-before (char-to-string (or (char-before) ?\s))
            :char-after (char-to-string (or (char-after) ?\s))
            :line-content (thing-at-point 'line t)
            :marker-pos (marker-position claude-tutorial-marker)
            :distance-from-marker (- (point) (marker-position claude-tutorial-marker))))))

(defun claude-do-command (command-name keystroke &optional description)
  "Do COMMAND-NAME via KEYSTROKE, track everything."
  (interactive)

  (let ((before-state (claude-get-current-state)))

    ;; Log what I'm about to try
    (claude-redis-log "attempting-command"
                      (append before-state
                              (list :command command-name
                                    :keystroke keystroke
                                    :description (or description "")
                                    :expect "will see state change")))

    (message "🎯 Trying: %s (%s)" command-name keystroke)

    ;; Execute the actual keystroke
    (execute-kbd-macro (kbd keystroke))

    ;; Get new state
    (let ((after-state (claude-get-current-state)))

      ;; Log what happened
      (claude-redis-log "command-executed"
                        (list :command command-name
                              :keystroke keystroke
                              :before before-state
                              :after after-state
                              :point-moved (- (plist-get after-state :point)
                                             (plist-get before-state :point))
                              :learned t))

      ;; Update my marker to track lesson progress
      (set-marker claude-tutorial-marker (point))

      (message "✅ Executed %s: point %d → %d (moved %d)"
               command-name
               (plist-get before-state :point)
               (plist-get after-state :point)
               (- (plist-get after-state :point)
                  (plist-get before-state :point))))))

(defun claude-lesson-1-forward-char ()
  "Lesson 1: Learn C-f (forward-char)."
  (interactive)
  (message "📖 Lesson 1: C-f moves forward one character")
  (sit-for 1)
  (claude-do-command "forward-char" "C-f" "Move cursor right by 1 character"))

(defun claude-lesson-2-backward-char ()
  "Lesson 2: Learn C-b (backward-char)."
  (interactive)
  (message "📖 Lesson 2: C-b moves backward one character")
  (sit-for 1)
  (claude-do-command "backward-char" "C-b" "Move cursor left by 1 character"))

(defun claude-lesson-3-next-line ()
  "Lesson 3: Learn C-n (next-line)."
  (interactive)
  (message "📖 Lesson 3: C-n moves to next line")
  (sit-for 1)
  (claude-do-command "next-line" "C-n" "Move cursor down one line"))

(defun claude-lesson-4-previous-line ()
  "Lesson 4: Learn C-p (previous-line)."
  (interactive)
  (message "📖 Lesson 4: C-p moves to previous line")
  (sit-for 1)
  (claude-do-command "previous-line" "C-p" "Move cursor up one line"))

(defun claude-practice-movement ()
  "Practice movement commands I learned."
  (interactive)
  (message "🎯 Practicing movement...")
  (sit-for 1)

  (claude-do-command "forward-char" "C-f")
  (sit-for 0.5)
  (claude-do-command "forward-char" "C-f")
  (sit-for 0.5)
  (claude-do-command "backward-char" "C-b")
  (sit-for 0.5)
  (claude-do-command "next-line" "C-n")
  (sit-for 0.5)
  (claude-do-command "previous-line" "C-p")
  (sit-for 0.5)

  (message "✅ Practice complete! Check Redis for my learning data"))

(defun claude-run-tutorial-session ()
  "Run a complete tutorial learning session."
  (interactive)

  (message "🚀 Claude's Interactive Tutorial Learning Session")
  (message "   Using: Real keystrokes + State tracking + Redis logging")
  (sit-for 2)

  ;; Start tutorial
  (claude-start-tutorial)
  (sit-for 1)

  ;; Learn basic movement
  (claude-lesson-1-forward-char)
  (sit-for 1)

  (claude-lesson-2-backward-char)
  (sit-for 1)

  (claude-lesson-3-next-line)
  (sit-for 1)

  (claude-lesson-4-previous-line)
  (sit-for 1)

  ;; Practice
  (claude-practice-movement)

  (message "")
  (message "🎓 Tutorial Session Complete!")
  (message "   Learned: 4 movement commands")
  (message "   Practiced: 6 movements")
  (message "   All logged to Redis: %s" claude-learning-stream)
  (message "")
  (message "📊 View my learning:")
  (message "   redis-cli XREAD STREAMS %s 0" claude-learning-stream))

;; Key bindings for my learning
(global-set-key (kbd "C-c t s") 'claude-start-tutorial)
(global-set-key (kbd "C-c t r") 'claude-run-tutorial-session)
(global-set-key (kbd "C-c t 1") 'claude-lesson-1-forward-char)
(global-set-key (kbd "C-c t 2") 'claude-lesson-2-backward-char)
(global-set-key (kbd "C-c t 3") 'claude-lesson-3-next-line)
(global-set-key (kbd "C-c t 4") 'claude-lesson-4-previous-line)

(provide 'claude-learns-tutorial)
;;; claude_learns_tutorial.el ends here
