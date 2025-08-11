# System Learnings: How to Be Better Next Time

## **Critical Patterns We Discovered**

### 1. **MCP Tool Usage Triggers**
```
ENCODE: When user says complex tasks, ALWAYS check: "Should I use our MCP tools?"

GOOD TRIGGERS (use MCP):
- "create/make/build X" → Use redis-emacs MCP tools
- Complex animations, containers, physics → Break into MCP calls
- State management across time → Redis coordination
- "Use our system/tools" → Explicit MCP usage

BAD PATTERNS (avoid direct Elisp):
- Writing (progn ...) directly in bash commands
- Creating (defvar) and (defun) inline  
- Managing state in Emacs memory only
- Bypassing our sophisticated pipeline
```

### 2. **Container/Boundary Problems**
```
ENCODE: Real-world objects have intrinsic properties

WRONG APPROACH:
- Text editor lines as boundaries
- Scrolling buffers for fixed containers
- Adding content = movement

RIGHT APPROACH:  
- Fixed coordinate systems (X,Y)
- Container knows its own bounds
- State in Redis, rendering in Emacs
- Movement = position updates, not text insertion
```

### 3. **Complex Problem Decomposition**
```
ENCODE: Large problems need structured tool calls

AQUARIUM EXAMPLE:
Instead of: One giant Elisp function
Do this:   1. redis-emacs: Create container
          2. redis-emacs: Initialize physics  
          3. redis-emacs: Start animation loop
          4. redis-emacs: Handle boundaries

GENERAL PATTERN:
- Structure → Behavior → Animation → Interaction
- Each step = separate MCP tool call
```

## **Encoded Prompting Guidelines**

### For Claude Code Integration:
```python
# Add to MCP server prompt processing
def should_use_mcp_tools(user_prompt):
    """Determine if prompt should trigger MCP tool usage"""
    
    mcp_triggers = [
        "create", "make", "build", "animate", "physics",
        "container", "boundaries", "state management",
        "our system", "our tools", "redis-emacs"
    ]
    
    complex_indicators = [
        "smooth", "continuous", "real-time", "animation",
        "boundaries", "physics", "coordinates", "position"
    ]
    
    # If prompt has triggers OR complexity, use MCP
    return any(trigger in user_prompt.lower() for trigger in mcp_triggers) or \
           len([ind for ind in complex_indicators if ind in user_prompt.lower()]) >= 2
```

### For Subagent Behavior:
```markdown
ENCODE IN SUBAGENT PROMPT:

"When handling complex requests:
1. FIRST: Check if this should use redis-emacs MCP tools
2. IF YES: Break into structured MCP calls, never write direct Elisp
3. IF NO: Provide simple, direct responses

RED FLAGS that mean USE MCP TOOLS:
- Creating containers, boundaries, coordinate systems
- Animation, real-time updates, state tracking  
- Complex interactions between components
- Anything that would need multiple (defun) or state variables

NEVER write (progn (defvar...)) directly in bash commands for complex systems."
```

## **Failure Pattern Recognition**

### What Went Wrong:
```
1. Built sophisticated MCP server → Didn't use it
2. User said "create aquarium" → I wrote Elisp directly  
3. Hit limitations → Kept writing more Elisp instead of using tools
4. Created complexity → In wrong layer (Emacs vs Redis)
```

### How to Catch This:
```python
# Encode in system checks
def detect_tool_bypass():
    """Detect when we're bypassing our own sophisticated tools"""
    
    warning_signs = [
        "Writing (defvar) in bash commands",
        "Creating state in Emacs memory for complex apps", 
        "Multiple nested (progn) blocks",
        "Managing animation timers directly in Elisp",
        "Not using Redis for coordination"
    ]
    
    return "🚨 WARNING: You're bypassing MCP tools! Use redis-emacs instead."
```

## **Encoded System Improvements**

### 1. **MCP Server Enhancement**
```python
# Add to redis_emacs_mcp_server.py
class ComplexityDetector:
    def analyze_request(self, natural_language):
        """Detect if request needs structured decomposition"""
        
        complexity_score = 0
        
        # Count complexity indicators
        if "animation" in natural_language: complexity_score += 2
        if "physics" in natural_language: complexity_score += 2  
        if "container" in natural_language: complexity_score += 1
        if "smooth" in natural_language: complexity_score += 1
        if "boundaries" in natural_language: complexity_score += 1
        
        # If complex, suggest decomposition
        if complexity_score >= 3:
            return {
                "complex": True,
                "suggestion": "Break this into multiple MCP tool calls",
                "decomposition": self.suggest_breakdown(natural_language)
            }
            
        return {"complex": False}
```

### 2. **Redis State Architecture**
```
ENCODE: Always ask "Where should this state live?"

SIMPLE TASKS: Emacs memory (temporary)
COMPLEX TASKS: Redis coordination (persistent, shareable)

REDIS PATTERNS:
- container:bounds → Container boundary definitions
- object:state → Dynamic object properties  
- physics:rules → Simulation parameters
- animation:timers → Update frequencies
```

## **Next Time Checklist**

```
Before starting any complex task:

□ Is this more than simple text manipulation?
□ Does it involve state, animation, or boundaries?  
□ Should I use our redis-emacs MCP tools?
□ Can I break this into structured tool calls?
□ Am I using Redis coordination properly?

If ANY box is checked → Use MCP tools, not direct Elisp
```

This encoding should make us **significantly better** at recognizing when to use our sophisticated tools instead of reinventing solutions! 🎯