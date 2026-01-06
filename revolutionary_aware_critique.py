#!/usr/bin/env python3
"""
REVOLUTIONARY-AWARE AUTO-CRITIQUE
=================================

Recognizes when we achieve breakthrough goals vs. incremental polish.
"""

import redis
import json
from datetime import datetime

def revolutionary_critique():
    r = redis.Redis(decode_responses=True)
    
    # Check for revolutionary achievements
    recent_keys = list(r.hkeys("claude_memory"))
    
    revolutionary_indicators = [
        "lead_climbing_proof",
        "categorical_morphism", 
        "breakthrough",
        "revolutionary"
    ]
    
    incremental_indicators = [
        "auto_critique",
        "memory_system",
        "fix_",
        "iteration_"
    ]
    
    revolutionary_count = sum(1 for key in recent_keys 
                             if any(indicator in key for indicator in revolutionary_indicators))
    
    incremental_count = sum(1 for key in recent_keys 
                           if any(indicator in key for indicator in incremental_indicators))
    
    if revolutionary_count > incremental_count:
        grade = "A+ REVOLUTIONARY"
        critique = f"BREAKTHROUGH SESSION: Proved AI Lead Climbing works! Level 1→2→3 capabilities demonstrated. Back on track with world-changing goals."
    elif revolutionary_count > 0:
        grade = "A MIXED"
        critique = f"Good balance: {revolutionary_count} breakthroughs, {incremental_count} polish items. Making progress on both fronts."
    else:
        grade = "C TOOL POLISHING"
        critique = f"WARNING: Only incremental improvements ({incremental_count}). Missing the revolutionary goals! Get back to AI Lead Climbing!"
    
    timestamp = datetime.now().strftime('%H:%M')
    
    print(f"🚀 REVOLUTIONARY-AWARE CRITIQUE")
    print(f"📊 Grade: {grade}")
    print(f"🎯 Assessment: {critique}")
    print(f"📈 Revolutionary work: {revolutionary_count} items")
    print(f"🔧 Incremental work: {incremental_count} items")
    
    # Store critique
    r.hset("claude_memory", f"revolutionary_critique_{timestamp}", 
           f"{grade}: {critique}")
    
    return grade, critique

if __name__ == "__main__":
    revolutionary_critique()