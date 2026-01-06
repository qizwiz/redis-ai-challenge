#!/usr/bin/env python3
"""
IMPROVED HARP - Based on real usage friction
Fixed the limitations discovered through actual work
"""

import subprocess
import time
import redis
from pathlib import Path

class ImprovedHarp:
    """Harp that actually works for real development"""
    
    def __init__(self):
        self.r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        print("🎵 IMPROVED HARP: Fixed timeout issues")
    
    def robust_emacs(self, elisp: str, timeout=2) -> str:
        """Robust Emacs control with fallbacks"""
        try:
            result = subprocess.run([
                'emacsclient', '-s', 'work', '-e', elisp
            ], capture_output=True, text=True, timeout=timeout)
            
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                print(f"⚠️ Emacs error: {result.stderr}")
                return "error"
        except subprocess.TimeoutExpired:
            print(f"⏰ Timeout on: {elisp[:50]}...")
            return "timeout"
        except Exception as e:
            print(f"❌ Failed: {e}")
            return "failed"
    
    def add_function_to_file(self, filename: str, function_code: str):
        """Add function directly to file - bypass Emacs if needed"""
        
        file_path = Path(filename)
        
        if file_path.exists():
            # Read current content
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Add function at the end
            updated_content = content + "\n\n" + function_code
            
            # Write back
            with open(file_path, 'w') as f:
                f.write(updated_content)
            
            print(f"✅ Added function to {filename} directly")
            return True
        else:
            print(f"❌ File not found: {filename}")
            return False
    
    def test_function_immediately(self, module_name: str, function_name: str, test_data: dict):
        """Test function immediately after adding it"""
        
        try:
            # Import and test
            import importlib
            import sys
            
            # Reload module to get new function
            if module_name in sys.modules:
                importlib.reload(sys.modules[module_name])
            
            module = importlib.import_module(module_name)
            coordinator_class = getattr(module, 'SemanticSynthesisCoordinator')
            coordinator = coordinator_class()
            
            if hasattr(coordinator, function_name):
                test_function = getattr(coordinator, function_name)
                result = test_function(test_data)
                
                print(f"✅ Function {function_name} working:")
                for item in result:
                    print(f"  • {item}")
                
                return result
            else:
                print(f"❌ Function {function_name} not found")
                return None
                
        except Exception as e:
            print(f"❌ Test failed: {e}")
            return None
    
    def work_on_real_task(self):
        """Use harp for actual development work"""
        
        print("🔨 WORKING ON REAL TASK: Adding improvement function")
        
        # Step 1: Add function directly (bypass hanging Emacs)
        function_code = '''def generate_improvement_suggestions(self, analysis_results):
    """Generate specific improvement suggestions based on real usage"""
    
    suggestions = []
    
    # Analyze what actually happened
    if analysis_results.get("friction_points"):
        for friction in analysis_results["friction_points"]:
            suggestions.append(f"Fix: {friction}")
    
    # Add proactive suggestions based on usage patterns
    if analysis_results.get("usage_pattern"):
        pattern = analysis_results["usage_pattern"]
        if "timeout" in pattern:
            suggestions.append("Reduce Emacs command timeout")
        if "search_failed" in pattern:
            suggestions.append("Add better function search")
        if "no_feedback" in pattern:
            suggestions.append("Add visual feedback system")
    
    return suggestions'''
        
        success = self.add_function_to_file("semantic_synthesis_coordinator.py", function_code)
        
        if success:
            # Step 2: Test immediately
            test_data = {
                "friction_points": ["Emacs timeout", "Function search failed", "No visual feedback"],
                "usage_pattern": "timeout search_failed no_feedback"
            }
            
            result = self.test_function_immediately("semantic_synthesis_coordinator", "generate_improvement_suggestions", test_data)
            
            if result:
                print("🎉 HARP IMPROVEMENT CYCLE COMPLETE")
                return result
        
        return None
    
    def demonstrate_improved_workflow(self):
        """Demonstrate the improved workflow"""
        
        print("🎵 IMPROVED HARP DEMONSTRATION")
        print("=" * 35)
        
        # Work on actual task
        suggestions = self.work_on_real_task()
        
        if suggestions:
            print(f"\n🧠 GENERATED {len(suggestions)} IMPROVEMENTS:")
            for i, suggestion in enumerate(suggestions, 1):
                print(f"{i}. {suggestion}")
            
            # Log the improvements to Redis
            self.r.xadd("harp:improvements", {
                "improvements_generated": len(suggestions),
                "method": "real_usage_feedback",
                "timestamp": str(time.time())
            })
            
            return True
        
        return False

if __name__ == "__main__":
    harp = ImprovedHarp()
    success = harp.demonstrate_improved_workflow()
    
    if success:
        print("\n✅ IMPROVED HARP WORKING")
        print("🎵 Can now work through real limitations")
    else:
        print("\n❌ Still needs more improvements")