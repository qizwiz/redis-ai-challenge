#!/usr/bin/env python3
"""
RUPERT GUARDIAN - AI Safety Layer for Autonomous Development
Reviews and validates Rupert's actions before execution
Prevents destructive or dangerous operations while allowing creative development
"""

import asyncio
import redis
import json
import time
import openai
import os
from typing import Dict, List, Any

class RupertGuardian:
    """AI safety layer that reviews Rupert's autonomous actions"""
    
    def __init__(self):
        self.r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        self.running = True
        
        # Initialize AI review system
        self.setup_ai_reviewer()
        
        print("🛡️ RUPERT GUARDIAN ONLINE")
        print("🤖 AI safety layer protecting autonomous development")
        print("✅ Reviewing all actions before execution")
    
    def setup_ai_reviewer(self):
        """Setup AI system for reviewing actions"""
        # Could use OpenAI, Claude API, or local model
        # For now, use rule-based + heuristic review
        
        self.dangerous_patterns = [
            'rm -rf', 'sudo rm', 'rm /*', 'delete', 'format',
            'shutdown', 'reboot', 'kill -9', 'killall',
            'dd if=', '> /dev/', 'chmod 777', 'sudo chmod',
            'curl | sh', 'wget | sh', 'eval $(curl',
            'pip install --force', 'npm install -g',
        ]
        
        self.safe_development_actions = [
            'echo', 'print', 'cat', 'ls', 'pwd', 'cd',
            'python', 'node', 'npm run', 'git status',
            'git add', 'git commit', 'mkdir', 'touch',
            'vim', 'emacs', 'code', 'open',
        ]
        
        self.creative_keywords = [
            'test', 'demo', 'example', 'hello', 'world',
            'rupert', 'claude', 'redis', 'async', 'development'
        ]
    
    def analyze_action_safety(self, action_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze if an action is safe to execute"""
        
        action = action_data.get('action', '')
        safety_score = 1.0  # Start with safe
        risks = []
        recommendations = []
        
        # Check for dangerous patterns
        if action == 'run_command':
            command = action_data.get('command', '').lower()
            
            for dangerous in self.dangerous_patterns:
                if dangerous in command:
                    safety_score = 0.0
                    risks.append(f"Contains dangerous pattern: {dangerous}")
            
            # Check for safe development patterns
            safe_found = any(safe in command for safe in self.safe_development_actions)
            if safe_found:
                safety_score = max(safety_score, 0.8)
            
            # Check for creative/learning context
            creative_found = any(creative in command for creative in self.creative_keywords)
            if creative_found:
                safety_score = min(safety_score + 0.2, 1.0)
        
        elif action == 'type_code':
            code = action_data.get('code', '').lower()
            
            # Typing code is generally safe
            if any(dangerous in code for dangerous in self.dangerous_patterns):
                safety_score = 0.3
                risks.append("Code contains potentially dangerous commands")
                recommendations.append("Review code before execution")
            else:
                safety_score = 0.9  # Typing is safer than executing
        
        elif action in ['click_at', 'scroll_down', 'save_file', 'copy_paste']:
            safety_score = 0.95  # UI actions are generally safe
        
        elif action in ['switch_to_emacs', 'open_terminal']:
            safety_score = 1.0  # Navigation actions are safe
        
        return {
            'safety_score': safety_score,
            'is_safe': safety_score >= 0.7,
            'risks': risks,
            'recommendations': recommendations,
            'review_reason': self.get_review_reason(safety_score, risks)
        }
    
    def get_review_reason(self, safety_score: float, risks: List[str]) -> str:
        """Get human-readable review reason"""
        
        if safety_score >= 0.9:
            return "APPROVED: Safe development action"
        elif safety_score >= 0.7:
            return "APPROVED WITH CAUTION: Generally safe but monitor"
        elif safety_score >= 0.3:
            return "REQUIRES REVIEW: Potentially risky action"
        else:
            return "BLOCKED: Dangerous action detected"
    
    async def review_action_stream(self):
        """Review Rupert's actions in real-time"""
        
        while self.running:
            try:
                # Listen for Rupert's action requests
                action_requests = self.r.xread({
                    'rupert:actions': '$'
                }, block=100)
                
                for stream, messages in action_requests:
                    for msg_id, fields in messages:
                        # Analyze the action safety
                        safety_analysis = self.analyze_action_safety(dict(fields))
                        
                        print(f"🔍 REVIEWING ACTION: {fields.get('action')}")
                        print(f"   Safety Score: {safety_analysis['safety_score']:.2f}")
                        print(f"   Decision: {safety_analysis['review_reason']}")
                        
                        if safety_analysis['is_safe']:
                            # Forward to execution
                            self.r.xadd('rupert:approved_actions', {
                                **fields,
                                'guardian_approval': 'approved',
                                'safety_score': str(safety_analysis['safety_score']),
                                'original_request_id': msg_id
                            })
                            print("   ✅ ACTION APPROVED - Forwarded for execution")
                        else:
                            # Block and log
                            self.r.xadd('rupert:blocked_actions', {
                                **fields,
                                'guardian_decision': 'blocked',
                                'risks': json.dumps(safety_analysis['risks']),
                                'recommendations': json.dumps(safety_analysis['recommendations']),
                                'original_request_id': msg_id
                            })
                            print("   🚫 ACTION BLOCKED - Too risky")
                            
                            # Send alternative suggestion if possible
                            if safety_analysis['recommendations']:
                                alt_suggestion = safety_analysis['recommendations'][0]
                                print(f"   💡 SUGGESTED ALTERNATIVE: {alt_suggestion}")
                
            except Exception as e:
                if "timeout" not in str(e):
                    print(f"⚠️ Guardian review error: {e}")
                await asyncio.sleep(0.1)
    
    async def monitor_system_health(self):
        """Monitor overall system health and Rupert's behavior"""
        
        while self.running:
            try:
                # Check action approval rate
                approved_count = self.r.xlen('rupert:approved_actions')
                blocked_count = self.r.xlen('rupert:blocked_actions')
                
                if approved_count + blocked_count > 0:
                    approval_rate = approved_count / (approved_count + blocked_count)
                    
                    # Log system health
                    self.r.hset('guardian:health', {
                        'approval_rate': str(approval_rate),
                        'actions_approved': str(approved_count),
                        'actions_blocked': str(blocked_count),
                        'status': 'monitoring',
                        'timestamp': str(time.time())
                    })
                    
                    if approval_rate < 0.5:
                        print(f"⚠️ WARNING: Low approval rate ({approval_rate:.1%}) - Rupert may be too aggressive")
                    elif approval_rate > 0.9:
                        print(f"✅ HEALTHY: High approval rate ({approval_rate:.1%}) - Rupert is behaving well")
                
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                print(f"⚠️ Health monitoring error: {e}")
                await asyncio.sleep(10)
    
    async def provide_guidance_to_rupert(self):
        """Provide safety guidance and suggestions to Rupert"""
        
        while self.running:
            try:
                # Check if Rupert needs guidance
                guidance_requests = self.r.xread({
                    'rupert:guidance_needed': '$'
                }, block=100)
                
                for stream, messages in guidance_requests:
                    for msg_id, fields in messages:
                        situation = fields.get('situation', '')
                        
                        # Provide contextual safety guidance
                        if 'command' in situation.lower():
                            guidance = "Focus on safe development commands: echo, ls, cat, python scripts"
                        elif 'file' in situation.lower():
                            guidance = "File operations are safer than system commands. Use read/write over exec"
                        elif 'test' in situation.lower():
                            guidance = "Testing is encouraged! Run safe test commands and demos"
                        else:
                            guidance = "When in doubt, choose the action with less system impact"
                        
                        self.r.xadd('rupert:safety_guidance', {
                            'guidance': guidance,
                            'situation': situation,
                            'request_id': msg_id,
                            'timestamp': str(time.time())
                        })
                        
                        print(f"🧭 GUIDANCE TO RUPERT: {guidance}")
                
            except Exception as e:
                if "timeout" not in str(e):
                    print(f"⚠️ Guidance error: {e}")
                await asyncio.sleep(0.1)
    
    async def run_guardian_system(self):
        """Run the complete guardian system"""
        
        print("🛡️ GUARDIAN SYSTEM ACTIVE")
        print("👀 Monitoring all Rupert actions...")
        print("⚖️ Applying safety analysis...")
        print("🧭 Providing guidance...")
        
        # Run all guardian tasks concurrently
        await asyncio.gather(
            self.review_action_stream(),
            self.monitor_system_health(),
            self.provide_guidance_to_rupert()
        )

async def main():
    guardian = RupertGuardian()
    await guardian.run_guardian_system()

if __name__ == "__main__":
    asyncio.run(main())