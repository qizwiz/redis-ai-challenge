;; -*- lexical-binding: t; -*-
;; Smooth Contained Aquarium

(defvar aquarium-active nil)
(defvar fish-positions '((20 5) (35 8) (50 12) (25 15) (60 18)))
(defvar fish-types '("🐠" "🐟" "🐡" "🦈" "🐟"))
(defvar fish-colors '("blue" "orange" "gold" "gray" "purple"))

(defun create-aquarium-container ()
  "Create a fixed aquarium container"
  (with-current-buffer "*aquarium*"
    (let ((inhibit-read-only t))
      (erase-buffer)
      
      ;; Top border
      (insert (propertize "┌" 'face '(:foreground "gray" :weight bold)))
      (insert (propertize (make-string 78 ?─) 'face '(:foreground "gray" :weight bold)))
      (insert (propertize "┐\n" 'face '(:foreground "gray" :weight bold)))
      
      ;; Water space with side borders
      (dotimes (row 20)
        (insert (propertize "│" 'face '(:foreground "gray" :weight bold)))
        (insert (propertize (make-string 78 ? ) 'face '(:background "#4682B4")))
        (insert (propertize "│\n" 'face '(:foreground "gray" :weight bold))))
      
      ;; Bottom border  
      (insert (propertize "└" 'face '(:foreground "gray" :weight bold)))
      (insert (propertize (make-string 78 ?─) 'face '(:foreground "gray" :weight bold)))
      (insert (propertize "┘" 'face '(:foreground "gray" :weight bold)))
      
      (setq buffer-read-only t)
      (setq cursor-type nil))))

(defun move-fish ()
  "Move fish smoothly within container bounds"
  (when aquarium-active
    (with-current-buffer "*aquarium*"
      (let ((inhibit-read-only t))
        
        ;; Clear old fish positions by redrawing water
        (dotimes (i (length fish-positions))
          (let ((pos (nth i fish-positions)))
            (goto-char (+ (point-min) (* (+ (nth 1 pos) 1) 80) (+ (nth 0 pos) 1)))
            (delete-char 1)
            (insert (propertize " " 'face '(:background "#4682B4")))))
        
        ;; Update fish positions with smooth movement
        (setq fish-positions
              (cl-mapcar (lambda (pos fish-type)
                          (let* ((x (nth 0 pos))
                                 (y (nth 1 pos))
                                 ;; Smooth, small movements
                                 (dx (if (< (random 10) 3) (- (random 3) 1) 0))
                                 (dy (if (< (random 10) 2) (- (random 3) 1) 0))
                                 (new-x (+ x dx))
                                 (new-y (+ y dy)))
                            
                            ;; Keep within container bounds
                            (setq new-x (max 1 (min 77 new-x)))
                            (setq new-y (max 1 (min 19 new-y)))
                            
                            (list new-x new-y)))
                        fish-positions fish-types))
        
        ;; Draw fish at new positions
        (dotimes (i (length fish-positions))
          (let* ((pos (nth i fish-positions))
                 (fish-char (nth i fish-types))
                 (fish-color (nth i fish-colors))
                 (x (nth 0 pos))
                 (y (nth 1 pos)))
            
            (goto-char (+ (point-min) (* (+ y 1) 80) (+ x 1)))
            (delete-char 1)
            (insert (propertize fish-char 'face `(:foreground ,fish-color :weight bold)
                               'help-echo (format "Fish swimming at (%d,%d)" x y)))))
        
        ;; Continue animation
        (run-with-timer 0.5 nil #'move-fish)))))

(defun start-smooth-aquarium ()
  "Start the smooth contained aquarium"
  (interactive)
  (switch-to-buffer "*aquarium*")
  (create-aquarium-container)
  (setq aquarium-active t)
  (move-fish))

(defun stop-aquarium ()
  "Stop aquarium animation"
  (interactive)
  (setq aquarium-active nil))

(provide 'smooth-aquarium)