;;; macos_facade.el --- Complete macOS vision through Redis -*- lexical-binding: t; -*-

;; Complete vision of macOS - every pixel, every window, every app
;; Like EmacsFacade but for entire Mac

;;; Code:

(require 'json)

(defvar macos-facade-stream "macos:facade:state"
  "Redis stream for macOS state snapshots.")

(defvar macos-facade-changes-stream "macos:facade:changes"
  "Redis stream for state change events.")

(defun macos-redis-exec (cmd)
  "Execute Redis CMD and return result."
  (string-trim
   (shell-command-to-string
    (format "redis-cli %s" cmd))))

(defun macos-get-screen-info ()
  "Get complete screen dimensions and bounds."
  (let* ((bounds-str (shell-command-to-string
                      "osascript -e 'tell application \"Finder\" to get bounds of window of desktop'"))
         (bounds (split-string (string-trim bounds-str) ", ")))
    (list :x0 (string-to-number (nth 0 bounds))
          :y0 (string-to-number (nth 1 bounds))
          :width (string-to-number (nth 2 bounds))
          :height (string-to-number (nth 3 bounds))
          :bounds bounds)))

(defun macos-get-frontmost-app ()
  "Get frontmost application info."
  (let ((app-name (string-trim
                   (shell-command-to-string
                    "osascript -e 'tell application \"System Events\" to get name of first application process whose frontmost is true'"))))
    (list :name app-name)))

(defun macos-get-window-info ()
  "Get frontmost window information with position and size."
  (condition-case err
      (let* ((script "tell application \"System Events\"
    set frontApp to name of first application process whose frontmost is true
    tell process frontApp
        if (count of windows) > 0 then
            set frontWindow to window 1
            set windowTitle to name of frontWindow
            set windowPos to position of frontWindow
            set windowSize to size of frontWindow
            return {frontApp, windowTitle, item 1 of windowPos, item 2 of windowPos, item 1 of windowSize, item 2 of windowSize}
        else
            return {frontApp, \"no windows\", 0, 0, 0, 0}
        end if
    end tell
end tell")
             (result (shell-command-to-string
                      (format "osascript -e '%s' 2>&1"
                              (replace-regexp-in-string "'" "'\\\\''" script))))
             (parts (split-string (string-trim result) ", ")))
        (if (>= (length parts) 6)
            (list :app (nth 0 parts)
                  :title (nth 1 parts)
                  :x (string-to-number (nth 2 parts))
                  :y (string-to-number (nth 3 parts))
                  :width (string-to-number (nth 4 parts))
                  :height (string-to-number (nth 5 parts)))
          (list :app "unknown" :error result)))
    (error (list :error (error-message-string err)))))

(defun macos-get-all-windows ()
  "Get all windows from all applications."
  (condition-case err
      (let* ((script "tell application \"System Events\"
    set allWindows to {}
    repeat with proc in (every process whose background only is false)
        set procName to name of proc
        tell proc
            repeat with w in windows
                set end of allWindows to {procName, name of w}
            end repeat
        end tell
    end repeat
    return allWindows
end tell")
             (result (shell-command-to-string
                      (format "osascript -e '%s' 2>&1"
                              (replace-regexp-in-string "'" "'\\\\''" script)))))
        (list :raw result :count (length (split-string result ","))))
    (error (list :error (error-message-string err)))))

(defun macos-get-running-apps ()
  "Get all running applications."
  (condition-case err
      (let* ((result (shell-command-to-string
                      "osascript -e 'tell application \"System Events\" to get name of every process whose background only is false' 2>&1"))
             (apps (split-string (string-trim result) ", ")))
        (list :apps apps :count (length apps)))
    (error (list :error (error-message-string err)))))

(defun macos-get-mouse-position ()
  "Get current mouse position if cliclick is available."
  (if (executable-find "cliclick")
      (let* ((result (shell-command-to-string "cliclick p"))
             (parts (split-string result ",")))
        (if (= (length parts) 2)
            (list :x (string-to-number (nth 0 parts))
                  :y (string-to-number (nth 1 parts)))
          (list :unavailable t)))
    (list :unavailable "cliclick not installed")))

(defun macos-get-system-info ()
  "Get system information."
  (list :hostname (string-trim (shell-command-to-string "hostname"))
        :user (string-trim (shell-command-to-string "whoami"))
        :uptime (string-trim (shell-command-to-string "uptime"))))

(defun macos-capture-complete-state ()
  "Capture complete macOS state - every pixel accounted for."
  (let* ((timestamp (format-time-string "%s"))
         (screen (macos-get-screen-info))
         (frontmost-window (macos-get-window-info))
         (all-windows (macos-get-all-windows))
         (running-apps (macos-get-running-apps))
         (mouse (macos-get-mouse-position))
         (system (macos-get-system-info))
         (state (list :timestamp timestamp
                      :screen screen
                      :frontmost frontmost-window
                      :windows all-windows
                      :applications running-apps
                      :mouse mouse
                      :system system)))

    ;; Store in Redis
    (let* ((json-str (json-encode state))
           (escaped (replace-regexp-in-string "\"" "\\\\\"" json-str))
           (cmd (format "XADD %s '*' timestamp %s state \"%s\""
                        macos-facade-stream
                        timestamp
                        escaped)))
      (macos-redis-exec cmd))

    state))

(defun macos-facade-summary (state)
  "Create human-readable summary of STATE."
  (let* ((screen (plist-get state :screen))
         (frontmost (plist-get state :frontmost))
         (apps (plist-get state :applications))
         (mouse (plist-get state :mouse))
         (system (plist-get state :system)))
    (format "🖥️  macOS FACADE - Complete Vision
┌─ Screen: %sx%s pixels
├─ Frontmost: %s
│  └─ Window: %s at (%s,%s) size %sx%s
├─ Running Apps: %s total
├─ Mouse: (%s,%s)
└─ System: %s@%s"
            (or (plist-get screen :width) "?")
            (or (plist-get screen :height) "?")
            (or (plist-get frontmost :app) "?")
            (or (plist-get frontmost :title) "?")
            (or (plist-get frontmost :x) "?")
            (or (plist-get frontmost :y) "?")
            (or (plist-get frontmost :width) "?")
            (or (plist-get frontmost :height) "?")
            (or (plist-get apps :count) "?")
            (or (plist-get mouse :x) "?")
            (or (plist-get mouse :y) "?")
            (or (plist-get system :user) "?")
            (or (plist-get system :hostname) "?"))))

(defun macos-facade-demo ()
  "Demonstrate complete macOS vision."
  (interactive)

  (message "🖥️  Capturing complete macOS state...")
  (sit-for 0.5)

  (let ((state (macos-capture-complete-state)))
    (message "\n%s" (macos-facade-summary state))
    (message "\n✅ Complete state captured and stored in Redis")
    (message "   Stream: %s" macos-facade-stream)
    (message "\n📊 View state:")
    (message "   redis-cli XREAD STREAMS %s 0" macos-facade-stream)

    state))

(defun macos-facade-watch (&optional interval)
  "Watch macOS state changes. INTERVAL in seconds (default 1)."
  (interactive "P")
  (let ((interval (or interval 1))
        (last-state nil))

    (message "👁️  Watching macOS state (every %ds)..." interval)
    (message "   Press C-g to stop")

    (while t
      (let ((state (macos-capture-complete-state)))

        ;; Detect changes
        (when (and last-state
                   (not (equal state last-state)))
          (let ((frontmost (plist-get state :frontmost))
                (last-frontmost (plist-get last-state :frontmost)))
            (when (not (equal frontmost last-frontmost))
              (message "🔄 App changed: %s → %s"
                       (plist-get last-frontmost :app)
                       (plist-get frontmost :app))

              ;; Log change to Redis
              (macos-redis-exec
               (format "XADD %s '*' event \"app-changed\" from \"%s\" to \"%s\" timestamp %s"
                       macos-facade-changes-stream
                       (plist-get last-frontmost :app)
                       (plist-get frontmost :app)
                       (format-time-string "%s"))))))

        (setq last-state state)
        (sit-for interval)))))

(defun macos-facade-find-emacs-window ()
  "Find Emacs window position and dimensions."
  (interactive)
  (let ((state (macos-capture-complete-state))
        (frontmost (plist-get (macos-capture-complete-state) :frontmost)))

    (if (string-match-p "Emacs" (plist-get frontmost :app))
        (progn
          (message "✅ Found Emacs window:")
          (message "   Position: (%d, %d)"
                   (plist-get frontmost :x)
                   (plist-get frontmost :y))
          (message "   Size: %dx%d"
                   (plist-get frontmost :width)
                   (plist-get frontmost :height))
          frontmost)
      (message "⚠️  Emacs is not frontmost. Current: %s"
               (plist-get frontmost :app))
      nil)))

;; Key bindings
(global-set-key (kbd "C-c m d") 'macos-facade-demo)
(global-set-key (kbd "C-c m w") 'macos-facade-watch)
(global-set-key (kbd "C-c m e") 'macos-facade-find-emacs-window)

(provide 'macos-facade)
;;; macos_facade.el ends here
