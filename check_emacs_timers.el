;;; check_emacs_timers.el --- Check what timers were running

(defun show-timer-history ()
  "Show what timers were running before cancellation"
  (interactive)
  (switch-to-buffer "*Timer History*")
  (erase-buffer)
  (insert "Timer List History\n")
  (insert "==================\n\n")
  
  ;; Check if there are any remaining timers
  (if timer-list
      (progn
        (insert "REMAINING TIMERS:\n")
        (dolist (timer timer-list)
          (insert (format "- %s (repeat: %s)\n" 
                         (timer--function timer)
                         (timer--repeat-delay timer)))))
    (insert "No active timers remaining\n\n"))
  
  ;; Check idle timers too
  (if timer-idle-list
      (progn
        (insert "\nREMAINING IDLE TIMERS:\n")
        (dolist (timer timer-idle-list)
          (insert (format "- %s (repeat: %s)\n"
                         (timer--function timer)
                         (timer--repeat-delay timer)))))
    (insert "No active idle timers remaining\n"))
  
  (insert "\n\nNOTE: All timers were cancelled, so this shows what's left.\n")
  (insert "The 'disastrous victory' likely came from accumulated Redis commands\n")
  (insert "being processed all at once when the bridge restarted.\n"))

(provide 'check-emacs-timers)