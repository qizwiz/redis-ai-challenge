;;; emacs_redis_interactive.el --- Interactive Emacs-Redis Demo -*- lexical-binding: t; -*-

;; Demonstration of using Redis as a communication layer for Emacs

;;; Code:

(require 'json)

(defvar eri-redis-cmd-stream "emacs:commands"
  "Redis stream for incoming commands.")

(defvar eri-redis-result-stream "emacs:results"
  "Redis stream for command results.")

(defun eri-redis-exec (cmd)
  "Execute Redis command CMD."
  (string-trim
   (shell-command-to-string
    (format "redis-cli %s" cmd))))

(defun eri-send-command (command-type data)
  "Send COMMAND-TYPE with DATA to Redis."
  (let* ((json-data (json-encode data))
         (escaped (replace-regexp-in-string "\"" "\\\\\"" json-data))
         (timestamp (format-time-string "%s")))
    (eri-redis-exec
     (format "XADD %s '*' type \"%s\" data \"%s\" timestamp %s"
             eri-redis-cmd-stream
             command-type
             escaped
             timestamp))))

(defun eri-send-result (result-type data)
  "Send RESULT-TYPE with DATA to Redis results stream."
  (let* ((json-data (json-encode data))
         (escaped (replace-regexp-in-string "\"" "\\\\\"" json-data))
         (timestamp (format-time-string "%s")))
    (eri-redis-exec
     (format "XADD %s '*' type \"%s\" data \"%s\" timestamp %s"
             eri-redis-result-stream
             result-type
             escaped
             timestamp))))

;; Interactive Commands

(defun eri-buffer-info ()
  "Send current buffer info to Redis."
  (interactive)
  (let ((info (list
               :buffer (buffer-name)
               :file (buffer-file-name)
               :mode (symbol-name major-mode)
               :size (buffer-size)
               :point (point)
               :line (line-number-at-pos)
               :modified (buffer-modified-p))))
    (eri-send-command "buffer-info" info)
    (message "📤 Buffer info sent to Redis stream: %s" eri-redis-cmd-stream)))

(defun eri-buffer-stats ()
  "Send buffer statistics to Redis."
  (interactive)
  (let ((stats (list
                :buffer (buffer-name)
                :lines (count-lines (point-min) (point-max))
                :chars (buffer-size)
                :words (count-words (point-min) (point-max))
                :point (point)
                :mark (if mark-active
                          (list :start (region-beginning)
                                :end (region-end)
                                :size (- (region-end) (region-beginning)))
                        :inactive))))
    (eri-send-result "buffer-stats" stats)
    (message "📊 Buffer stats sent to Redis")))

(defun eri-send-region-to-redis ()
  "Send selected region text to Redis for processing."
  (interactive)
  (if mark-active
      (let* ((region-text (buffer-substring-no-properties
                           (region-beginning)
                           (region-end)))
             (data (list
                    :text region-text
                    :buffer (buffer-name)
                    :start (region-beginning)
                    :end (region-end))))
        (eri-send-command "region-text" data)
        (message "📤 Region sent to Redis (%d chars)" (length region-text)))
    (message "⚠️  No region selected")))

(defun eri-request-ai-completion ()
  "Request AI completion for current context via Redis."
  (interactive)
  (let* ((line (thing-at-point 'line t))
         (word (thing-at-point 'word t))
         (data (list
                :context "completion-request"
                :buffer (buffer-name)
                :file (buffer-file-name)
                :mode (symbol-name major-mode)
                :line line
                :word word
                :point (point))))
    (eri-send-command "ai-completion" data)
    (message "🤖 AI completion requested via Redis")))

(defun eri-log-keystroke-event (event-type)
  "Log keystroke EVENT-TYPE to Redis."
  (interactive "sEvent type: ")
  (let ((data (list
               :event event-type
               :buffer (buffer-name)
               :key (if (and last-command-event (characterp last-command-event))
                        (string last-command-event)
                      "special-key")
               :command (symbol-name (or last-command 'unknown))
               :point (point))))
    (eri-send-command "keystroke" data)
    (message "⌨️  Keystroke logged to Redis")))

(defun eri-stream-buffer-changes ()
  "Start streaming buffer change events to Redis."
  (interactive)
  (add-hook 'after-change-functions 'eri-after-change-handler nil t)
  (message "🔄 Buffer change streaming enabled"))

(defun eri-stop-streaming ()
  "Stop streaming buffer changes."
  (interactive)
  (remove-hook 'after-change-functions 'eri-after-change-handler t)
  (message "🛑 Buffer change streaming stopped"))

(defun eri-after-change-handler (beg end len)
  "Handle buffer changes from BEG to END with length LEN."
  (let ((data (list
               :buffer (buffer-name)
               :change-start beg
               :change-end end
               :deleted-length len
               :inserted-text (if (> end beg)
                                  (buffer-substring-no-properties beg end)
                                "")
               :timestamp (float-time))))
    (eri-send-command "buffer-change" data)))

(defun eri-query-redis-commands ()
  "Query and display commands from Redis."
  (interactive)
  (let* ((result (eri-redis-exec
                  (format "XREAD COUNT 10 STREAMS %s 0" eri-redis-cmd-stream)))
         (count (length (split-string result "\n" t))))
    (message "📥 Redis commands stream has %d entries" (/ count 6))
    (with-current-buffer (get-buffer-create "*Redis Commands*")
      (erase-buffer)
      (insert "=== Commands in Redis ===\n\n")
      (insert result)
      (goto-char (point-min))
      (display-buffer (current-buffer)))))

(defun eri-query-redis-results ()
  "Query and display results from Redis."
  (interactive)
  (let* ((result (eri-redis-exec
                  (format "XREAD COUNT 10 STREAMS %s 0" eri-redis-result-stream)))
         (count (length (split-string result "\n" t))))
    (message "📤 Redis results stream has %d entries" (/ count 6))
    (with-current-buffer (get-buffer-create "*Redis Results*")
      (erase-buffer)
      (insert "=== Results in Redis ===\n\n")
      (insert result)
      (goto-char (point-min))
      (display-buffer (current-buffer)))))

(defun eri-demo ()
  "Demonstrate Emacs-Redis integration."
  (interactive)
  (message "")
  (message "🎭 Emacs-Redis Interactive Demo")
  (message "")
  (message "Available commands:")
  (message "  M-x eri-buffer-info          - Send buffer info to Redis")
  (message "  M-x eri-buffer-stats         - Send buffer statistics")
  (message "  M-x eri-send-region-to-redis - Send selected region")
  (message "  M-x eri-request-ai-completion - Request AI completion")
  (message "  M-x eri-stream-buffer-changes - Stream live changes")
  (message "  M-x eri-query-redis-commands  - View commands in Redis")
  (message "  M-x eri-query-redis-results   - View results in Redis")
  (message "")
  (message "Try: Select some text and run M-x eri-send-region-to-redis")
  (message ""))

;; Key bindings
(global-set-key (kbd "C-c r i") 'eri-buffer-info)
(global-set-key (kbd "C-c r s") 'eri-buffer-stats)
(global-set-key (kbd "C-c r r") 'eri-send-region-to-redis)
(global-set-key (kbd "C-c r a") 'eri-request-ai-completion)
(global-set-key (kbd "C-c r c") 'eri-query-redis-commands)
(global-set-key (kbd "C-c r v") 'eri-query-redis-results)
(global-set-key (kbd "C-c r d") 'eri-demo)

(provide 'emacs-redis-interactive)
;;; emacs_redis_interactive.el ends here
