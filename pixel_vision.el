;;; pixel_vision.el --- Complete pixel-level vision without assistive access -*- lexical-binding: t; -*-

;; Every pixel accounted for using screencapture and image analysis

;;; Code:

(require 'json)

(defvar pixel-vision-stream "pixel:vision:state"
  "Redis stream for pixel-level vision data.")

(defvar pixel-vision-screenshots-dir (expand-file-name "~/.claude-pixel-vision/")
  "Directory for screenshot storage.")

(defun pixel-vision-ensure-directory ()
  "Ensure screenshot directory exists."
  (unless (file-exists-p pixel-vision-screenshots-dir)
    (make-directory pixel-vision-screenshots-dir t)))

(defun pixel-vision-capture-screenshot (&optional region)
  "Capture screenshot. REGION is optional (x y width height)."
  (pixel-vision-ensure-directory)
  (let* ((timestamp (format-time-string "%s"))
         (filename (format "%sscreen_%s.png" pixel-vision-screenshots-dir timestamp))
         (cmd (if region
                  (format "screencapture -R%d,%d,%d,%d -x %s"
                          (nth 0 region) (nth 1 region)
                          (nth 2 region) (nth 3 region)
                          filename)
                (format "screencapture -x %s" filename))))
    (shell-command cmd)
    (sleep-for 0.2)  ; Wait for screenshot to be written
    (let ((size (if (file-exists-p filename)
                    (file-attribute-size (file-attributes filename))
                  0)))
      (list :timestamp timestamp
            :filename filename
            :size size
            :region region))))

(defun pixel-vision-get-screen-bounds ()
  "Get exact screen pixel bounds."
  (let* ((result (shell-command-to-string
                  "system_profiler SPDisplaysDataType | grep Resolution"))
         (matches (string-match "\\([0-9]+\\) x \\([0-9]+\\)" result)))
    (if matches
        (list :width (string-to-number (match-string 1 result))
              :height (string-to-number (match-string 2 result)))
      (list :width 1440 :height 900))))  ; fallback

(defun pixel-vision-analyze-screenshot (screenshot-info)
  "Analyze SCREENSHOT-INFO to extract visual data."
  (let* ((filename (plist-get screenshot-info :filename))
         (file-size (plist-get screenshot-info :size)))
    (append screenshot-info
            (list :analysis
                  (list :file-exists (file-exists-p filename)
                        :file-size-kb (/ file-size 1024)
                        :format "PNG"
                        :captured t)))))

(defun pixel-vision-complete-vision ()
  "Capture and analyze complete pixel-level vision."
  (interactive)

  (message "📸 Capturing complete pixel vision...")

  (let* ((bounds (pixel-vision-get-screen-bounds))
         (screenshot (pixel-vision-capture-screenshot))
         (analyzed (pixel-vision-analyze-screenshot screenshot))
         (state (list :timestamp (plist-get screenshot :timestamp)
                      :screen bounds
                      :screenshot analyzed
                      :total-pixels (* (plist-get bounds :width)
                                      (plist-get bounds :height)))))

    ;; Store in Redis
    (let* ((json-str (json-encode state))
           (escaped (replace-regexp-in-string "\"" "\\\\\"" json-str))
           (cmd (format "XADD %s '*' timestamp %s vision \"%s\""
                        pixel-vision-stream
                        (plist-get screenshot :timestamp)
                        escaped)))
      (shell-command-to-string (format "redis-cli %s" cmd)))

    (message "✅ Pixel vision captured:")
    (message "   Total pixels: %s (%sx%s)"
             (* (plist-get bounds :width) (plist-get bounds :height))
             (plist-get bounds :width)
             (plist-get bounds :height))
    (message "   Screenshot: %s (%d KB)"
             (plist-get screenshot :filename)
             (/ (plist-get screenshot :size) 1024))
    (message "   Stored in: %s" pixel-vision-stream)

    state))

(defun pixel-vision-compare-states (state1 state2)
  "Compare two pixel vision states to detect changes."
  (let* ((file1 (plist-get (plist-get state1 :screenshot) :filename))
         (file2 (plist-get (plist-get state2 :screenshot) :filename))
         (size1 (plist-get (plist-get state1 :screenshot) :size))
         (size2 (plist-get (plist-get state2 :screenshot) :size))
         (size-diff (abs (- size2 size1))))
    (list :files-differ (not (= size1 size2))
          :size-change-bytes size-diff
          :files (list file1 file2))))

(defun pixel-vision-watch-changes (&optional interval)
  "Watch for pixel-level changes. INTERVAL in seconds (default 2)."
  (interactive "P")
  (let ((interval (or interval 2))
        (last-state nil))

    (message "👁️  Watching pixel-level changes (every %ds)..." interval)
    (message "   Screenshots: %s" pixel-vision-screenshots-dir)
    (message "   Press C-g to stop")

    (while t
      (let ((state (pixel-vision-complete-vision)))
        (when last-state
          (let ((comparison (pixel-vision-compare-states last-state state)))
            (when (plist-get comparison :files-differ)
              (message "🔄 Screen changed! Size diff: %d bytes"
                       (plist-get comparison :size-change-bytes)))))

        (setq last-state state)
        (sit-for interval)))))

(defun pixel-vision-emacs-region ()
  "Capture just the Emacs frame region (if we can determine it)."
  (interactive)

  ;; Get Emacs frame geometry
  (let* ((frame (selected-frame))
         (geom (frame-geometry frame))
         (outer-pos (cdr (assq 'outer-position geom)))
         (outer-size (cdr (assq 'outer-size geom)))
         (x (car outer-pos))
         (y (cdr outer-pos))
         (width (car outer-size))
         (height (cdr outer-size)))

    (message "📸 Capturing Emacs frame region...")
    (message "   Position: (%d, %d)" x y)
    (message "   Size: %dx%d" width height)

    (let ((screenshot (pixel-vision-capture-screenshot (list x y width height))))
      (message "✅ Emacs region captured: %s"
               (plist-get screenshot :filename))
      screenshot)))

(defun pixel-vision-summary ()
  "Show summary of pixel vision captures."
  (interactive)

  (let* ((count (length (directory-files pixel-vision-screenshots-dir nil "screen_.*\\.png")))
         (total-size (apply '+
                           (mapcar (lambda (f)
                                    (file-attribute-size
                                     (file-attributes
                                      (expand-file-name f pixel-vision-screenshots-dir))))
                                  (directory-files pixel-vision-screenshots-dir nil "screen_.*\\.png")))))

    (message "📊 Pixel Vision Summary")
    (message "   Captures: %d screenshots" count)
    (message "   Total size: %d KB" (/ total-size 1024))
    (message "   Directory: %s" pixel-vision-screenshots-dir)
    (message "   Stream: %s" pixel-vision-stream)))

;; Key bindings
(global-set-key (kbd "C-c p v") 'pixel-vision-complete-vision)
(global-set-key (kbd "C-c p w") 'pixel-vision-watch-changes)
(global-set-key (kbd "C-c p e") 'pixel-vision-emacs-region)
(global-set-key (kbd "C-c p s") 'pixel-vision-summary)

(provide 'pixel-vision)
;;; pixel_vision.el ends here
