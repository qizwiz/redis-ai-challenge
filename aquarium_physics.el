;; -*- lexical-binding: t; -*-
;; Physics-Enabled Aquarium

(defvar aquarium-physics-active nil)
(defvar water-current-direction 1)
(defvar fish-physics '((blue-tang 10 5 0.2 0.1 mid)
                       (clownfish 20 8 0.3 -0.05 shallow)
                       (pufferfish 30 12 0.1 0.15 deep)
                       (angelfish 40 6 0.25 0.08 mid)
                       (shark 50 15 0.4 0.02 deep)
                       (parrotfish 60 10 0.15 -0.1 shallow)
                       (grouper 70 18 0.1 0.05 bottom)))

(defun update-physics ()
  "Update fish positions based on physics"
  ;; Random current changes
  (setq water-current-direction 
        (if (< (random 100) 5) 
            (* water-current-direction -1) 
            water-current-direction))
  
  ;; Update each fish
  (setq fish-physics 
        (mapcar (lambda (fish)
                  (let* ((name (nth 0 fish))
                         (x (nth 1 fish))
                         (y (nth 2 fish))
                         (vx (nth 3 fish))
                         (vy (nth 4 fish))
                         (depth (nth 5 fish))
                         ;; Physics forces
                         (current-effect (* water-current-direction 0.1))
                         (buoyancy (cond ((eq depth 'shallow) -0.05)
                                        ((eq depth 'mid) 0.0)
                                        ((eq depth 'deep) 0.03)
                                        ((eq depth 'bottom) 0.08)))
                         ;; Update velocity
                         (new-vx (+ vx current-effect (/ (- (random 20) 10) 100.0)))
                         (new-vy (+ vy buoyancy (/ (- (random 10) 5) 100.0)))
                         ;; Update position
                         (new-x (+ x new-vx))
                         (new-y (+ y new-vy)))
                    
                    ;; Boundary collisions
                    (when (< new-x 5) 
                      (setq new-x 75 new-vx (abs new-vx)))
                    (when (> new-x 75) 
                      (setq new-x 5 new-vx (- (abs new-vx))))
                    (when (< new-y 3) 
                      (setq new-y 3 new-vy (abs new-vy)))
                    (when (> new-y 18) 
                      (setq new-y 18 new-vy (- (abs new-vy))))
                    
                    (list name (round new-x) (round new-y) new-vx new-vy depth)))
                fish-physics)))

(defun draw-physics-aquarium ()
  "Draw aquarium with physics visualization"
  (with-current-buffer "*aquarium*"
    (let ((inhibit-read-only t))
      (erase-buffer)
      
      ;; Header with current direction
      (insert (propertize "🌊 PHYSICS-ENABLED AQUARIUM 🌊" 
                         'face '(:foreground "cyan" :weight bold)))
      (insert (propertize (format "  Current: %s" 
                                 (if (> water-current-direction 0) "→" "←"))
                         'face '(:foreground "lightblue")))
      (insert "\n\n")
      
      ;; Draw water layers with depth coloring
      (dotimes (row 20)
        (dotimes (col 80)
          (let ((depth-color (cond ((< row 5) "#E0F6FF")    ; Light cyan - shallow
                                  ((< row 10) "#87CEEB")   ; Sky blue - mid
                                  ((< row 15) "#4682B4")   ; Steel blue - deep  
                                  (t "#191970"))))         ; Midnight blue - bottom
            (insert (propertize " " 'face `(:background ,depth-color)))))
        (insert "\n"))
      
      ;; Draw fish at their physics positions
      (dolist (fish fish-physics)
        (let* ((name (nth 0 fish))
               (x (nth 1 fish))
               (y (nth 2 fish))
               (depth (nth 5 fish))
               (fish-char (cond ((eq name 'blue-tang) "🐠")
                               ((eq name 'clownfish) "🐟")
                               ((eq name 'pufferfish) "🐡")
                               ((eq name 'angelfish) "🐠")
                               ((eq name 'shark) "🦈")
                               ((eq name 'parrotfish) "🐡")
                               ((eq name 'grouper) "🐟")))
               (fish-color (cond ((eq name 'blue-tang) "blue")
                                ((eq name 'clownfish) "orange")
                                ((eq name 'pufferfish) "gold")
                                ((eq name 'angelfish) "green")
                                ((eq name 'shark) "gray")
                                ((eq name 'parrotfish) "magenta")
                                ((eq name 'grouper) "purple")))
               (tooltip (format "%s - %s layer, affected by currents and buoyancy" 
                               (capitalize (symbol-name name)) 
                               (symbol-name depth))))
          
          (goto-char (+ (point-min) (* (+ y 2) 81) x))
          (delete-char 1)
          (insert (propertize fish-char 
                             'face `(:foreground ,fish-color :weight bold)
                             'help-echo tooltip))))
      
      ;; Footer
      (goto-char (point-max))
      (insert (propertize "\n🪸 Physics: Buoyancy, Currents, Depth Layers 🪸" 
                         'face '(:foreground "coral" :weight bold))))))

(defun run-aquarium-physics ()
  "Main physics loop"
  (when aquarium-physics-active
    (update-physics)
    (draw-physics-aquarium)
    (run-with-timer 1.5 nil 'run-aquarium-physics)))

(defun start-physics-aquarium ()
  "Start the physics-enabled aquarium"
  (interactive)
  (switch-to-buffer "*aquarium*")
  (setq aquarium-physics-active t)
  (run-aquarium-physics))

(defun stop-physics-aquarium ()
  "Stop the physics simulation"
  (interactive)
  (setq aquarium-physics-active nil))

(provide 'aquarium-physics)