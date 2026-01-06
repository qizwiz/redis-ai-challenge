;;; macos_facade_complete.el --- Complete macOS state facade through Redis -*- lexical-binding: t; -*-

;; Complete vision through state representation, not screenshots
;; Every piece of the Mac represented as data in Redis

;;; Code:

(require 'json)

(defvar macos-facade-state-key "macos:facade:current"
  "Redis key for current macOS state.")

(defvar macos-facade-history-stream "macos:facade:history"
  "Redis stream for state change history.")

(defun macos-redis (cmd)
  "Execute Redis CMD and return result."
  (string-trim (shell-command-to-string (format "redis-cli %s" cmd))))

(defun macos-get-display-info ()
  "Get display configuration and geometry."
  (let* ((displays-raw (shell-command-to-string "system_profiler SPDisplaysDataType -json"))
         (displays-json (ignore-errors (json-read-from-string displays-raw))))
    (list :raw-available (> (length displays-raw) 0)
          :resolution-from-finder
          (let ((bounds (shell-command-to-string
                        "osascript -e 'tell application \"Finder\" to get bounds of window of desktop' 2>&1")))
            (if (string-match-p "error" bounds)
                (list :error bounds)
              (let ((parts (split-string (string-trim bounds) ", ")))
                (list :x0 (string-to-number (nth 0 parts))
                      :y0 (string-to-number (nth 1 parts))
                      :x1 (string-to-number (nth 2 parts))
                      :y1 (string-to-number (nth 3 parts))
                      :width (- (string-to-number (nth 2 parts))
                               (string-to-number (nth 0 parts)))
                      :height (- (string-to-number (nth 3 parts))
                                (string-to-number (nth 1 parts))))))))))

(defun macos-get-running-processes ()
  "Get all running processes with details."
  (let* ((ps-output (shell-command-to-string "ps aux"))
         (lines (split-string ps-output "\n" t))
         (process-count (1- (length lines))))  ; -1 for header
    (list :total-processes process-count
          :sample-output (substring ps-output 0 (min 500 (length ps-output))))))

(defun macos-get-application-list ()
  "Get all running GUI applications."
  (let* ((apps-str (shell-command-to-string
                   "osascript -e 'tell application \"System Events\" to get name of every process whose background only is false' 2>&1")))
    (if (string-match-p "error" apps-str)
        (list :error apps-str)
      (let ((apps (split-string (string-trim apps-str) ", ")))
        (list :applications apps
              :count (length apps))))))

(defun macos-get-network-info ()
  "Get network interface and connectivity info."
  (list :interfaces (split-string
                     (string-trim (shell-command-to-string "ifconfig | grep '^[a-z]' | cut -d: -f1"))
                     "\n")
        :active-connections (string-to-number
                            (shell-command-to-string "netstat -an | grep ESTABLISHED | wc -l"))))

(defun macos-get-file-system-info ()
  "Get file system state."
  (list :home-dir (expand-file-name "~")
        :current-dir default-directory
        :disk-usage (shell-command-to-string "df -h / | tail -1")))

(defun macos-get-emacs-state ()
  "Get complete Emacs internal state."
  (let ((geom (frame-geometry (selected-frame))))
    (list :version emacs-version
          :pid (emacs-pid)
          :frames (length (frame-list))
          :buffers (length (buffer-list))
          :current-buffer (buffer-name)
          :point (point)
          :mark (or (mark t) 0)
          :windows (length (window-list))
          :frame-position (list :x (cdr (assq 'left (frame-parameters)))
                               :y (cdr (assq 'top (frame-parameters))))
          :frame-size (list :width (cdr (assq 'width (frame-parameters)))
                           :height (cdr (assq 'height (frame-parameters)))))))

(defun macos-get-environment ()
  "Get environment variables and shell state."
  (list :shell (getenv "SHELL")
        :path (getenv "PATH")
        :home (getenv "HOME")
        :user (getenv "USER")
        :lang (getenv "LANG")))

(defun macos-get-time-state ()
  "Get temporal state."
  (list :timestamp (format-time-string "%s")
        :iso-time (format-time-string "%Y-%m-%dT%H:%M:%S%z")
        :uptime (string-trim (shell-command-to-string "uptime"))))

(defun macos-get-memory-state ()
  "Get memory and resource usage."
  (let ((vm-stat (shell-command-to-string "vm_stat")))
    (list :vm-stat-available (> (length vm-stat) 0)
          :top-memory (shell-command-to-string "top -l 1 | head -10"))))

(defun macos-get-clipboard ()
  "Get clipboard contents."
  (let ((clip (condition-case nil
                  (shell-command-to-string "pbpaste")
                (error nil))))
    (list :length (length clip)
          :preview (if clip (substring clip 0 (min 100 (length clip))) "")
          :has-content (> (length clip) 0))))

(defun macos-capture-complete-facade ()
  "Capture COMPLETE macOS state - every observable piece of the system."
  (interactive)

  (let* ((timestamp (format-time-string "%s"))
         (state (list :meta (list :captured-at timestamp
                                 :facade-version "1.0.0"
                                 :capture-method "direct-api-calls")
                     :display (macos-get-display-info)
                     :applications (macos-get-application-list)
                     :processes (macos-get-running-processes)
                     :network (macos-get-network-info)
                     :filesystem (macos-get-file-system-info)
                     :emacs (macos-get-emacs-state)
                     :environment (macos-get-environment)
                     :time (macos-get-time-state)
                     :memory (macos-get-memory-state)
                     :clipboard (macos-get-clipboard))))

    ;; Store current state in Redis (single key, always latest)
    (let* ((json-str (json-encode state))
           (escaped (replace-regexp-in-string "\"" "\\\\\""
                    (replace-regexp-in-string "\n" "\\\\n" json-str))))
      (macos-redis (format "SET %s \"%s\"" macos-facade-state-key escaped))

      ;; Also append to history stream
      (macos-redis (format "XADD %s '*' timestamp %s state \"%s\""
                          macos-facade-history-stream
                          timestamp
                          escaped)))

    (message "✅ Complete macOS facade captured")
    (message "   Current state: GET %s" macos-facade-state-key)
    (message "   History: XREAD STREAMS %s" macos-facade-history-stream)

    state))

(defun macos-facade-view-current ()
  "View current macOS facade state from Redis."
  (interactive)

  (let* ((json-str (macos-redis (format "GET %s" macos-facade-state-key)))
         (state (json-read-from-string json-str)))

    (with-current-buffer (get-buffer-create "*macOS Facade*")
      (erase-buffer)
      (insert "🖥️  COMPLETE macOS FACADE - Every Observable State\n")
      (insert "═══════════════════════════════════════════════════\n\n")

      ;; Display info
      (let ((display (cdr (assq 'display state))))
        (insert (format "📺 DISPLAY\n"))
        (insert (format "   Resolution: %s\n"
                       (cdr (assq 'resolution-from-finder display)))))

      ;; Applications
      (let* ((apps (cdr (assq 'applications state)))
             (app-list (cdr (assq 'applications apps)))
             (count (cdr (assq 'count apps))))
        (insert (format "\n📱 APPLICATIONS (%d running)\n" count))
        (dolist (app (seq-take app-list 10))
          (insert (format "   • %s\n" app)))
        (when (> count 10)
          (insert (format "   ... and %d more\n" (- count 10)))))

      ;; Processes
      (let ((procs (cdr (assq 'processes state))))
        (insert (format "\n⚙️  PROCESSES\n"))
        (insert (format "   Total: %d\n" (cdr (assq 'total-processes procs)))))

      ;; Network
      (let ((net (cdr (assq 'network state))))
        (insert (format "\n🌐 NETWORK\n"))
        (insert (format "   Interfaces: %s\n" (cdr (assq 'interfaces net))))
        (insert (format "   Active connections: %d\n" (cdr (assq 'active-connections net)))))

      ;; Emacs state
      (let ((em (cdr (assq 'emacs state))))
        (insert (format "\n🟣 EMACS\n"))
        (insert (format "   Version: %s (PID %d)\n"
                       (cdr (assq 'version em))
                       (cdr (assq 'pid em))))
        (insert (format "   Frames: %d, Buffers: %d\n"
                       (cdr (assq 'frames em))
                       (cdr (assq 'buffers em))))
        (insert (format "   Current: %s (point: %d)\n"
                       (cdr (assq 'current-buffer em))
                       (cdr (assq 'point em)))))

      ;; Clipboard
      (let ((clip (cdr (assq 'clipboard state))))
        (insert (format "\n📋 CLIPBOARD\n"))
        (insert (format "   Length: %d chars\n" (cdr (assq 'length clip))))
        (when (> (cdr (assq 'length clip)) 0)
          (insert (format "   Preview: %s...\n" (cdr (assq 'preview clip))))))

      ;; Time
      (let ((time (cdr (assq 'time state))))
        (insert (format "\n⏰ TIME\n"))
        (insert (format "   %s\n" (cdr (assq 'iso-time time))))
        (insert (format "   %s\n" (cdr (assq 'uptime time)))))

      (insert "\n═══════════════════════════════════════════════════\n")
      (insert (format "Facade stored in Redis: %s\n" macos-facade-state-key))

      (goto-char (point-min))
      (special-mode))

    (switch-to-buffer "*macOS Facade*")))

(defun macos-facade-diff-states (state1 state2)
  "Compare two facade states and return differences."
  (let ((diffs '()))

    ;; Compare applications
    (let ((apps1 (plist-get (plist-get state1 :applications) :applications))
          (apps2 (plist-get (plist-get state2 :applications) :applications)))
      (when (not (equal apps1 apps2))
        (push (list :type "applications-changed"
                   :old-count (length apps1)
                   :new-count (length apps2))
              diffs)))

    ;; Compare Emacs buffer
    (let ((buf1 (plist-get (plist-get state1 :emacs) :current-buffer))
          (buf2 (plist-get (plist-get state2 :emacs) :current-buffer)))
      (when (not (equal buf1 buf2))
        (push (list :type "buffer-changed"
                   :from buf1
                   :to buf2)
              diffs)))

    diffs))

(defun macos-facade-watch (&optional interval)
  "Watch for state changes. INTERVAL in seconds (default 2)."
  (interactive "P")
  (let ((interval (or interval 2))
        (last-state nil))

    (message "👁️  Watching macOS facade for changes...")

    (while t
      (let ((state (macos-capture-complete-facade)))

        (when last-state
          (let ((diffs (macos-facade-diff-states last-state state)))
            (when diffs
              (message "🔄 State changed: %S" diffs))))

        (setq last-state state)
        (sit-for interval)))))

;; Key bindings
(global-set-key (kbd "C-c f c") 'macos-capture-complete-facade)
(global-set-key (kbd "C-c f v") 'macos-facade-view-current)
(global-set-key (kbd "C-c f w") 'macos-facade-watch)

(provide 'macos-facade-complete)
;;; macos_facade_complete.el ends here
