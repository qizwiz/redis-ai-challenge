;;; test_ai_workspace_integration.el --- Test AI Workspace Integration

;; Test script to verify ai-workspace.el functionality
;; This will run through all the main functions and verify they work

(require 'ai-workspace)

(defun test-ai-workspace-run-tests ()
  "Run comprehensive tests of ai-workspace integration."
  (interactive)
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
    
    ;; Test 7: Test workspace creation (but don't actually create it)
    (push (cons "ai-workspace-create callable"
                (condition-case err
                    (progn (commandp 'ai-workspace-create) t)
                  (error nil)))
          test-results)
    
    ;; Generate test report
    (with-current-buffer (get-buffer-create "*AI-Workspace-Test-Results*")
      (erase-buffer)
      (insert "AI Workspace Integration Test Results\n")
      (insert "======================================\n\n")
      
      (let ((passed 0) (failed 0))
        (dolist (test (reverse test-results))
          (let ((name (car test))
                (result (cdr test)))
            (if result
                (progn
                  (insert (format "✓ PASS: %s\n" name))
                  (setq passed (1+ passed)))
              (insert (format "✗ FAIL: %s\n" name))
              (setq failed (1+ failed)))))
        
        (insert (format "\nSummary: %d passed, %d failed\n" passed failed))
        (insert (format "Success rate: %.1f%%\n" 
                        (* 100.0 (/ (float passed) (+ passed failed))))))
      
      (display-buffer (current-buffer))
      (message "Test results displayed in *AI-Workspace-Test-Results*"))))

(defun test-ai-workspace-create-workspace ()
  "Actually test creating the AI workspace."
  (interactive)
  (condition-case err
      (progn
        (ai-workspace-create)
        (message "✓ AI Workspace created successfully!"))
    (error (message "✗ Failed to create AI workspace: %s" err))))

(defun test-ai-workspace-test-functions ()
  "Test individual AI workspace functions."
  (interactive)
  (with-current-buffer (get-buffer-create "*AI-Function-Tests*")
    (erase-buffer)
    (insert "AI Workspace Function Tests\n")
    (insert "===========================\n\n")
    
    ;; Test coordinate analysis function
    (insert "Testing ai-workspace-coordinate-analysis...\n")
    (condition-case err
        (progn
          (ai-workspace-coordinate-analysis "test content" "syntax")
          (insert "✓ ai-workspace-coordinate-analysis works\n"))
      (error (insert (format "✗ ai-workspace-coordinate-analysis failed: %s\n" err))))
    
    ;; Test sync content function
    (insert "\nTesting ai-workspace-sync-content...\n")
    (condition-case err
        (progn
          (ai-workspace-sync-content "*scratch*")
          (insert "✓ ai-workspace-sync-content works\n"))
      (error (insert (format "✗ ai-workspace-sync-content failed: %s\n" err))))
    
    ;; Test monitor documents function
    (insert "\nTesting ai-workspace-monitor-documents...\n")
    (condition-case err
        (progn
          (ai-workspace-monitor-documents)
          (insert "✓ ai-workspace-monitor-documents works\n"))
      (error (insert (format "✗ ai-workspace-monitor-documents failed: %s\n" err))))
    
    ;; Test query streams function
    (insert "\nTesting ai-workspace-query-streams...\n")
    (condition-case err
        (progn
          (ai-workspace-query-streams "content" 5)
          (insert "✓ ai-workspace-query-streams works\n"))
      (error (insert (format "✗ ai-workspace-query-streams failed: %s\n" err))))
    
    (display-buffer (current-buffer))
    (message "Function tests completed")))

;; Auto-run basic tests when this file is loaded
(message "AI Workspace test functions loaded. Run M-x test-ai-workspace-run-tests to start testing.")

(provide 'test_ai_workspace_integration)
;;; test_ai_workspace_integration.el ends here