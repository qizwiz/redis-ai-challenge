;; -*- lexical-binding: t; -*-
;; True 2D Aquarium - Fish move in continuous space, not lines

(defvar aquarium-active nil)
(defvar fish-data '((20.5 8.3 0.2 -0.1 "🐠" "blue")     ; x y vx vy char color
                    (35.7 12.1 -0.15 0.05 "🐟" "orange")
                    (50.2 6.8 0.1 0.2 "🐡" "gold") 
                    (25.9 15.4 0.3 -0.05 "🦈" "gray")
                    (60.1 18.2 -0.25 0.15 "🐟" "purple")))

(defun create-water-space ()
  "Create fixed water container - no scrolling"
  (with-current-buffer "*aquarium*"
    (let ((inhibit-read-only t))
      (erase-buffer)
      (setq truncate-lines t)  ; No line wrapping!
      
      ;; Create fixed 80x22 water space
      (insert "🌊 CONTINUOUS WATER SPACE - NO LINES 🌊\n")
      (insert "┌────────────────────────────────────────────────────────────────────────────┐\n")
      
      ;; 20 rows of water - each is a fixed container row, not "text lines"
      (dotimes (row 20)
        (insert "│")
        (insert (make-string 78 ? ))  ; Water space
        (insert "│\n"))
      
      (insert "└────────────────────────────────────────────────────────────────────────────┘")
      
      (goto-char (point-min))
      (setq buffer-read-only t)
      (setq cursor-type nil))))

(defun update-fish-physics ()
  "Update fish positions using 2D physics, not line-based movement"
  (setq fish-data
        (mapcar (lambda (fish)
                  (let* ((x (nth 0 fish))
                         (y (nth 1 fish)) 
                         (vx (nth 2 fish))
                         (vy (nth 3 fish))
                         (char (nth 4 fish))
                         (color (nth 5 fish))
                         ;; Physics update - continuous 2D space
                         (new-vx (+ vx (* 0.1 (- (random 20) 10))))  ; Random swim
                         (new-vy (+ vy (* 0.05 (- (random 10) 5))))
                         (new-x (+ x new-vx))
                         (new-y (+ y new-vy)))
                    
                    ;; Bounce off walls (2D boundaries, not line boundaries)
                    (when (or (< new-x 1) (> new-x 77))
                      (setq new-vx (- new-vx))
                      (setq new-x (max 1 (min 77 new-x))))
                    
                    (when (or (< new-y 1) (> new-y 19))
                      (setq new-vy (- new-vy))  
                      (setq new-y (max 1 (min 19 new-y))))
                    
                    (list new-x new-y new-vx new-vy char color)))
                fish-data)))

(defun render-fish ()
  "Render fish at their 2D coordinates - not line positions"
  (with-current-buffer "*aquarium*"
    (let ((inhibit-read-only t))
      
      ;; Clear water space (redraw background)
      (goto-char (+ (point-min) 82))  ; Skip header
      (dotimes (row 20)
        (forward-char 1)  ; Skip border
        (delete-char 78)
        (insert (make-string 78 ? ))
        (forward-char 2))  ; Skip border + newline
      
      ;; Place fish at their exact 2D coordinates
      (dolist (fish fish-data)
        (let* ((x (round (nth 0 fish)))    ; Convert float to pixel position
               (y (round (nth 1 fish)))
               (char (nth 4 fish))
               (color (nth 5 fish))
               ;; Calculate exact buffer position for (x,y) coordinate
               (buffer-pos (+ (point-min) 82 (* y 80) x)))
          
          (goto-char buffer-pos)
          (delete-char 1)
          (insert (propertize char 'face `(:foreground ,color :weight bold)
                             'help-echo (format "Swimming at (%.1f, %.1f)" 
                                               (nth 0 fish) (nth 1 fish)))))))))

(defun animate-aquarium ()
  "Main animation loop - continuous 2D movement"
  (when aquarium-active
    (update-fish-physics)
    (render-fish)
    (run-with-timer 0.3 nil #'animate-aquarium)))

(defun start-true-aquarium ()
  "Start continuous 2D aquarium"
  (interactive)
  (switch-to-buffer "*aquarium*")
  (create-water-space)
  (setq aquarium-active t)
  (animate-aquarium))

(defun stop-true-aquarium ()
  "Stop aquarium"
  (interactive)
  (setq aquarium-active nil))

(provide 'true-aquarium)