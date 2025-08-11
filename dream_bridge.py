#!/usr/bin/env python3
"""
Dream Bridge - Real-time bidirectional communication between emergent system and Emacs

This creates the nervous system that allows the emergent AI to truly inhabit
the development environment - seeing, thinking, and acting in real-time.
"""

import redis
import json
import time
import asyncio
import threading
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass, field
from datetime import datetime
import subprocess
import tempfile
import os

@dataclass
class EmacsPulse:
    """Real-time pulse from Emacs system"""
    timestamp: float
    event_type: str
    data: Dict[str, Any]
    source_buffer: Optional[str] = None
    cursor_position: Optional[int] = None
    change_magnitude: float = 0.0

@dataclass
class AIResponse:
    """AI response flowing back to Emacs"""
    timestamp: float
    response_type: str
    target_buffer: Optional[str]
    elisp_command: Optional[str]
    message: Optional[str]
    confidence: float = 1.0

class DreamBridge:
    """Real-time bidirectional bridge between AI and Emacs"""
    
    def __init__(self, redis_host='localhost', redis_port=6379):
        self.redis = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
        self.running = False
        
        # Communication channels
        self.emacs_to_ai_stream = "dream:emacs_to_ai"
        self.ai_to_emacs_stream = "dream:ai_to_emacs"
        self.pulse_stream = "dream:pulse"
        
        # Real-time state
        self.current_emacs_state = {}
        self.ai_conversation_context = []
        self.development_session = {
            "start_time": time.time(),
            "interactions": 0,
            "learning_events": 0,
            "evolution_triggers": 0
        }
        
        # Event handlers
        self.pulse_handlers = []
        self.command_handlers = {}
        
        # Bridge threads
        self.pulse_thread = None
        self.response_thread = None
        
    def start_bridge(self):
        """Start the real-time bridge"""
        print("🌉 Starting Dream Bridge...")
        
        self.running = True
        
        # Start pulse monitoring (Emacs → AI)
        self.pulse_thread = threading.Thread(target=self._pulse_monitor_loop, daemon=True)
        self.pulse_thread.start()
        
        # Start response delivery (AI → Emacs)  
        self.response_thread = threading.Thread(target=self._response_delivery_loop, daemon=True)
        self.response_thread.start()
        
        # Install Emacs bridge
        self._install_emacs_bridge()
        
        print("✅ Dream Bridge active - AI can now inhabit Emacs")
        
    def _install_emacs_bridge(self):
        """Install the Emacs side of the bridge"""
        bridge_elisp = '''
;;; dream-bridge.el --- Real-time AI bridge

(require 'json)

(defvar dream-bridge-active t "Whether dream bridge is active")
(defvar dream-bridge-pulse-timer nil "Pulse timer")
(defvar dream-bridge-last-state nil "Last state sent")

(defun dream-bridge-send-pulse ()
  "Send real-time pulse to AI system"
  (when dream-bridge-active
    (let* ((current-state (dream-bridge-capture-state))
           (pulse-data (json-encode current-state)))
      
      ;; Only send if state changed significantly
      (unless (equal current-state dream-bridge-last-state)
        (shell-command-to-string 
         (format "redis-cli XADD dream:pulse * type pulse data '%s'" 
                 (shell-quote-argument pulse-data)))
        (setq dream-bridge-last-state current-state)))))

(defun dream-bridge-capture-state ()
  "Capture current Emacs state for AI"
  `((timestamp . ,(float-time))
    (current-buffer . ,(buffer-name))
    (buffer-size . ,(buffer-size))
    (point . ,(point))
    (line . ,(line-number-at-pos))
    (column . ,(current-column))
    (window-count . ,(length (window-list)))
    (major-mode . ,(symbol-name major-mode))
    (minor-modes . ,(mapcar #'symbol-name 
                           (seq-filter #'symbol-value minor-mode-list)))
    (recent-command . ,(symbol-name (or last-command 'none)))
    (region-active . ,(region-active-p))
    (region-text . ,(if (region-active-p) 
                       (buffer-substring (region-beginning) (region-end))
                     nil))
    (buffer-modified . ,(buffer-modified-p))
    (project-root . ,(when (fboundp 'projectile-project-root)
                      (ignore-errors (projectile-project-root))))
    (git-branch . ,(when (fboundp 'magit-get-current-branch)
                    (ignore-errors (magit-get-current-branch))))))

(defun dream-bridge-process-ai-responses ()
  "Process responses from AI system"
  (when dream-bridge-active
    (let ((response-json (shell-command-to-string 
                         "redis-cli XREAD BLOCK 100 STREAMS dream:ai_to_emacs 0")))
      (when (and response-json (not (string-empty-p response-json)))
        (dream-bridge-handle-ai-response response-json)))))

(defun dream-bridge-handle-ai-response (response-json)
  "Handle AI response"
  (condition-case err
      (let* ((response-data (json-parse-string response-json :object-type 'alist))
             (response-type (alist-get 'response_type response-data))
             (elisp-command (alist-get 'elisp_command response-data))
             (message-text (alist-get 'message response-data)))
        
        (cond
         ((string= response-type "elisp")
          (when elisp-command
            (eval (read elisp-command))))
         
         ((string= response-type "message")
          (when message-text
            (message "🤖 AI: %s" message-text)))
         
         ((string= response-type "buffer-edit")
          (dream-bridge-apply-buffer-edit response-data))
         
         (t
          (message "🤖 Unknown AI response: %s" response-type))))
    
    (error
     (message "🚨 Dream bridge error: %s" (error-message-string err)))))

(defun dream-bridge-apply-buffer-edit (edit-data)
  "Apply AI-suggested buffer edit"
  (let ((target-buffer (alist-get 'target_buffer edit-data))
        (edit-command (alist-get 'elisp_command edit-data)))
    (when (and target-buffer edit-command)
      (with-current-buffer target-buffer
        (eval (read edit-command))))))

(defun dream-bridge-start ()
  "Start the dream bridge"
  (interactive)
  (setq dream-bridge-active t)
  
  ;; Start pulse timer - send state every 2 seconds
  (setq dream-bridge-pulse-timer 
        (run-with-timer 0 2 #'dream-bridge-send-pulse))
  
  ;; Start response processing timer
  (run-with-timer 0 1 #'dream-bridge-process-ai-responses)
  
  (message "🌉 Dream Bridge started - AI is now connected"))

(defun dream-bridge-stop ()
  "Stop the dream bridge"
  (interactive)
  (setq dream-bridge-active nil)
  
  (when dream-bridge-pulse-timer
    (cancel-timer dream-bridge-pulse-timer)
    (setq dream-bridge-pulse-timer nil))
  
  (message "🌉 Dream Bridge stopped"))

;; Auto-start if Redis is available
(when (executable-find "redis-cli")
  (run-with-timer 1 nil #'dream-bridge-start))

(provide 'dream-bridge)
'''
        
        # Write to temporary file and load in Emacs
        with tempfile.NamedTemporaryFile(mode='w', suffix='.el', delete=False) as f:
            f.write(bridge_elisp)
            elisp_file = f.name
            
        # Load in Emacs
        subprocess.run(['emacs', '--batch', '-l', elisp_file, '--eval', '(dream-bridge-start)'], 
                      capture_output=True)
        
        # Clean up
        os.unlink(elisp_file)
        
        print("📡 Emacs bridge installed and activated")
        
    def _pulse_monitor_loop(self):
        """Monitor real-time pulses from Emacs"""
        print("💓 Pulse monitor started")
        
        last_id = "0"
        
        while self.running:
            try:
                # Read new pulses from Emacs
                streams = self.redis.xread({self.pulse_stream: last_id}, block=1000)
                
                for stream_name, messages in streams:
                    for message_id, fields in messages:
                        pulse_data = json.loads(fields.get('data', '{}'))
                        
                        pulse = EmacsPulse(
                            timestamp=pulse_data.get('timestamp', time.time()),
                            event_type=fields.get('type', 'pulse'),
                            data=pulse_data,
                            source_buffer=pulse_data.get('current-buffer'),
                            cursor_position=pulse_data.get('point'),
                            change_magnitude=self._calculate_change_magnitude(pulse_data)
                        )
                        
                        # Process the pulse
                        self._process_emacs_pulse(pulse)
                        
                        last_id = message_id
                        
            except Exception as e:
                print(f"💔 Pulse monitor error: {e}")
                time.sleep(5)
                
    def _calculate_change_magnitude(self, pulse_data: Dict[str, Any]) -> float:
        """Calculate how significant this change is"""
        if not self.current_emacs_state:
            return 1.0  # First pulse is always significant
            
        magnitude = 0.0
        
        # Buffer change
        if pulse_data.get('current-buffer') != self.current_emacs_state.get('current-buffer'):
            magnitude += 0.5
            
        # Point movement
        old_point = self.current_emacs_state.get('point', 0)
        new_point = pulse_data.get('point', 0)
        if abs(new_point - old_point) > 10:  # Significant movement
            magnitude += 0.3
            
        # Mode changes
        old_modes = set(self.current_emacs_state.get('minor-modes', []))
        new_modes = set(pulse_data.get('minor-modes', []))
        if old_modes != new_modes:
            magnitude += 0.4
            
        # Command execution
        if pulse_data.get('recent-command') != 'none':
            magnitude += 0.2
            
        return min(magnitude, 1.0)
        
                
            
    def _generate_ai_response(self, pulse: EmacsPulse) -> Optional[AIResponse]:
        """Generate AI response to Emacs pulse"""
        # Simple heuristic responses - this is where real AI would go
        
        buffer_name = pulse.source_buffer or ""
        recent_command = pulse.data.get('recent-command', 'none')
        
        # Respond to programming activity
        if buffer_name.endswith('.py'):
            if recent_command in ['newline', 'self-insert-command']:
                return AIResponse(
                    timestamp=time.time(),
                    response_type="message",
                    target_buffer=buffer_name,
                    elisp_command=None,
                    message=f"Python development detected in {buffer_name}",
                    confidence=0.8
                )
                
        # Respond to git activity  
        if 'magit' in buffer_name.lower():
            return AIResponse(
                timestamp=time.time(),
                response_type="message", 
                target_buffer=buffer_name,
                elisp_command=None,
                message="Git workflow active - monitoring for commit patterns",
                confidence=0.9
            )
            
        # Respond to configuration changes
        if buffer_name.endswith('.el'):
            return AIResponse(
                timestamp=time.time(),
                response_type="elisp",
                target_buffer=buffer_name,
                elisp_command='(message "🧠 AI: Elisp editing detected - syntax checking enabled")',
                message=None,
                confidence=0.7
            )
            
        return None
        
        
                
    # Public interface for extending the bridge
    def register_pulse_handler(self, handler: Callable[[EmacsPulse], None]):
        """Register handler for Emacs pulses"""
        self.pulse_handlers.append(handler)
        
    def send_elisp_command(self, command: str, target_buffer: str = None):
        """Send Elisp command to Emacs"""
        response = AIResponse(
            timestamp=time.time(),
            response_type="elisp",
            target_buffer=target_buffer,
            elisp_command=command,
            message=None,
            confidence=1.0
        )
        self._send_ai_response(response)
        
    def send_message(self, message: str):
        """Send message to Emacs"""
        response = AIResponse(
            timestamp=time.time(),
            response_type="message",
            target_buffer=None,
            elisp_command=None,
            message=message,
            confidence=1.0
        )
        self._send_ai_response(response)
        
    def get_current_state(self) -> Dict[str, Any]:
        """Get current Emacs state"""
        return self.current_emacs_state.copy()
        
    def get_session_stats(self) -> Dict[str, Any]:
        """Get development session statistics"""
        session_duration = time.time() - self.development_session["start_time"]
        return {
            **self.development_session,
            "session_duration": session_duration,
            "interactions_per_minute": self.development_session["interactions"] / (session_duration / 60)
        }
        
    def stop_bridge(self):
        """Stop the dream bridge"""
        print("🌉 Stopping Dream Bridge...")
        self.running = False
        
        # Send stop command to Emacs
        self.send_elisp_command("(dream-bridge-stop)")
        
        # Wait for threads
        if self.pulse_thread:
            self.pulse_thread.join(timeout=5)
        if self.response_thread:
            self.response_thread.join(timeout=5)
            
        print("✅ Dream Bridge stopped")

def demo_dream_bridge():
    """Demo the real-time dream bridge"""
    print("🌉 DREAM BRIDGE DEMO")
    print("=" * 40)
    
    bridge = DreamBridge()
    
    # Add custom pulse handler
    def learning_handler(pulse: EmacsPulse):
    """
    Handles learning events based on Emacs pulse data with magnitude threshold filtering.

    This function processes EmacsPulse events and logs learning activities when the
    change magnitude exceeds a predefined threshold of 0.3. It's designed to capture
    significant editor events that indicate meaningful user activity worth learning from.

    Args:
        pulse (EmacsPulse): An EmacsPulse object containing event data including
            event_type, source_buffer, and change_magnitude attributes.

    Returns:
        None: This function performs logging and doesn't return a value.

    Example:
        >>> pulse = EmacsPulse(event_type="buffer-change", 
        ...                   source_buffer="main.py", 
        ...                   change_magnitude=0.5)
        >>> learning_handler(pulse)
        📚 Learning: buffer-change in main.py
    """
        if pulse.change_magnitude > 0.3:
            print(f"📚 Learning: {pulse.event_type} in {pulse.source_buffer}")
            
    bridge.register_pulse_handler(learning_handler)
    
    try:
        # Start the bridge
        bridge.start_bridge()
        
        print("\n🔄 Dream Bridge running...")
        print("The AI can now:")
        print("  • See real-time Emacs state changes")
        print("  • Respond with messages and Elisp commands")
        print("  • Learn from development patterns")
        print("  • Inhabit the development environment")
        print("\nTry editing files in Emacs to see AI responses!")
        
        # Let it run
        time.sleep(30)
        
        # Show session stats
        stats = bridge.get_session_stats()
        print(f"\n📊 Session Stats:")
        print(f"  Duration: {stats['session_duration']:.1f}s")
        print(f"  Interactions: {stats['interactions']}")
        print(f"  Rate: {stats['interactions_per_minute']:.1f} interactions/min")
        
    except KeyboardInterrupt:
        print("\n🛑 Stopping bridge...")
        
    finally:
        bridge.stop_bridge()
        print("✅ Dream Bridge demo complete")

if __name__ == "__main__":
    demo_dream_bridge()