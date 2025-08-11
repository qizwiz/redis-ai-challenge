;;; run_ai_workspace_tests.el --- Run AI Workspace Tests -*- lexical-binding: t; -*-

;; Load the ai-workspace module
(load-file "ai-workspace.el")

(defun run-ai-workspace-tests-batch ()
  "Run AI workspace tests and output results to stdout."
  (let ((test-results '()))
    
    ;; Test 1: Check if ai-workspace.el loaded correctly
    (push (cons "ai-workspace loaded" 
                (featurep 'ai-workspace)) 
          test-results)
    
    ;; Test 2: Check if variables are defined
    (push (cons "ai-workspace-buffer variable defined"
                (boundp 'ai-workspace-buffer))
          test-results)
    
    (push (cons "ai-workspace-redis-streams variable defined"
                (boundp 'ai-workspace-redis-streams))
          test-results)
    
    ;; Test 3: Check if functions are defined
    (push (cons "ai-workspace-create function defined"
                (fboundp 'ai-workspace-create))
          test-results)
    
    (push (cons "ai-workspace-redis-connected-p function defined"
                (fboundp 'ai-workspace-redis-connected-p))
          test-results)
    
    (push (cons "ai-workspace-coordinate-analysis function defined"
                (fboundp 'ai-workspace-coordinate-analysis))
          test-results)
    
    ;; Test 4: Test Redis connection check
    (push (cons "Redis connection test"
                (condition-case err
                    (ai-workspace-redis-connected-p)
                  (error (format "Error: %s" err))))
          test-results)
    
    ;; Test 5: Test keymap creation
    (push (cons "ai-workspace-mode-map defined"
                (keymapp ai-workspace-mode-map))
          test-results)
    
    ;; Test 6: Check if keybindings are set
    (push (cons "C-c a keybinding set"
                (not (null (lookup-key ai-workspace-mode-map (kbd "C-c a")))))
          test-results)
    
    (push (cons "C-c c keybinding set"
                (not (null (lookup-key ai-workspace-mode-map (kbd "C-c c")))))
          test-results)
    
    ;; Test 7: Test workspace creation function existence
    (push (cons "ai-workspace-create callable"
                (commandp 'ai-workspace-create))
          test-results)
    
    ;; Generate test report to stdout
    (princ "AI Workspace Integration Test Results\n")
    (princ "======================================\n\n")
    
    (let ((passed 0) (failed 0))
      (dolist (test (reverse test-results))
        (let ((name (car test))
              (result (cdr test)))
          (if result
              (progn
                (princ (format "✓ PASS: %s\n" name))
                (setq passed (1+ passed)))
            (princ (format "✗ FAIL: %s\n" name))
            (setq failed (1+ failed)))))
      
      (princ (format "\nSummary: %d passed, %d failed\n" passed failed))
      (princ (format "Success rate: %.1f%%\n" 
                     (* 100.0 (/ (float passed) (+ passed failed))))))
    
    ;; Test function calls (non-interactively)
    (princ "\nFunction Call Tests:\n")
    (princ "===================\n")
    
    ;; Test coordinate analysis function
    (princ "Testing ai-workspace-coordinate-analysis... ")
    (condition-case err
        (progn
          (ai-workspace-coordinate-analysis "test content" "syntax")
          (princ "✓ SUCCESS\n"))
      (error (princ (format "✗ FAILED: %s\n" err))))
    
    ;; Test sync content function
    (princ "Testing ai-workspace-sync-content... ")
    (condition-case err
        (progn
          (ai-workspace-sync-content "*scratch*")
          (princ "✓ SUCCESS\n"))
      (error (princ (format "✗ FAILED: %s\n" err))))
    
    ;; Test monitor documents function
    (princ "Testing ai-workspace-monitor-documents... ")
    (condition-case err
        (progn
          (ai-workspace-monitor-documents)
          (princ "✓ SUCCESS\n"))
      (error (princ (format "✗ FAILED: %s\n" err))))
    
    ;; Test query streams function
    (princ "Testing ai-workspace-query-streams... ")
    (condition-case err
        (progn
          (ai-workspace-query-streams "content" 5)
          (princ "✓ SUCCESS\n"))
      (error (princ (format "✗ FAILED: %s\n" err))))))

;; Run the tests
(run-ai-workspace-tests-batch)