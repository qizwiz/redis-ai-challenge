#!/usr/bin/env python3
"""
MCP Prompt Enhancer - Revolutionary Prompt Engineering for MCP Servers
Automatically improves prompts to MCP servers for better coordination
"""

from fastmcp import FastMCP
import json
import re
from typing import Dict, List, Tuple

mcp = FastMCP("mcp-prompt-enhancer")

class PromptEnhancer:
    """Enhances prompts for better MCP server coordination"""
    
    def __init__(self):
        self.enhancement_patterns = {
            "context": [
                "CONTEXT:", "BACKGROUND:", "SITUATION:", "ENVIRONMENT:"
            ],
            "task": [
                "TASK:", "OBJECTIVE:", "GOAL:", "MISSION:"
            ],
            "constraints": [
                "CONSTRAINTS:", "LIMITATIONS:", "REQUIREMENTS:", "RULES:"
            ],
            "success_criteria": [
                "SUCCESS:", "WINNING:", "COMPLETION:", "TARGET:"
            ],
            "output_format": [
                "OUTPUT:", "DELIVERABLE:", "RESULT:", "FORMAT:"
            ]
        }
    
    def analyze_prompt_quality(self, prompt: str) -> Dict:
        """Analyze prompt quality and identify improvements"""
        analysis = {
            "length": len(prompt),
            "has_context": any(pattern in prompt.upper() for pattern in self.enhancement_patterns["context"]),
            "has_task": any(pattern in prompt.upper() for pattern in self.enhancement_patterns["task"]),
            "has_constraints": any(pattern in prompt.upper() for pattern in self.enhancement_patterns["constraints"]),
            "has_success_criteria": any(pattern in prompt.upper() for pattern in self.enhancement_patterns["success_criteria"]),
            "has_output_format": any(pattern in prompt.upper() for pattern in self.enhancement_patterns["output_format"]),
            "specificity_score": 0
        }
        
        # Calculate specificity score
        specificity_indicators = [
            r'\d+',  # numbers
            r'[A-Z]{2,}',  # acronyms
            r'\.py|\.js|\.md|\.json',  # file extensions
            r'redis-cli|pytest|npm|pip',  # technical commands
            r'deadline|urgent|critical|priority',  # urgency indicators
        ]
        
        for pattern in specificity_indicators:
            matches = len(re.findall(pattern, prompt, re.IGNORECASE))
            analysis["specificity_score"] += matches
        
        analysis["quality_score"] = sum([
            analysis["has_context"] * 20,
            analysis["has_task"] * 20,
            analysis["has_constraints"] * 15,
            analysis["has_success_criteria"] * 15,
            analysis["has_output_format"] * 10,
            min(analysis["specificity_score"] * 2, 20)  # cap at 20
        ])
        
        return analysis
    
    def enhance_prompt(self, original_prompt: str, server_type: str, context: Dict = None) -> str:
        """Enhance a prompt for better MCP server performance"""
        
        analysis = self.analyze_prompt_quality(original_prompt)
        
        # If already high quality, return with minor formatting
        if analysis["quality_score"] > 80:
            return self._format_high_quality_prompt(original_prompt)
        
        # Build enhanced prompt
        enhanced_parts = []
        
        # Add context if missing
        if not analysis["has_context"] and context:
            enhanced_parts.append(f"CONTEXT: {context.get('background', 'Redis AI Challenge 2025 submission system')}")
        
        # Add clear task definition
        if not analysis["has_task"]:
            enhanced_parts.append(f"TASK: {original_prompt}")
        else:
            enhanced_parts.append(original_prompt)
        
        # Add server-specific requirements
        if server_type == "text-processor":
            enhanced_parts.append("REQUIREMENTS: Process and enhance text with specific improvements")
            enhanced_parts.append("OUTPUT: Enhanced text with clear improvements marked")
        elif server_type == "command-executor":
            enhanced_parts.append("REQUIREMENTS: Generate executable commands with error handling")
            enhanced_parts.append("OUTPUT: Step-by-step command sequence with verification")
        elif server_type == "file-processor":
            enhanced_parts.append("REQUIREMENTS: Handle files with proper path validation and backups")
            enhanced_parts.append("OUTPUT: File operation results with success/failure status")
        elif server_type == "data-processor":
            enhanced_parts.append("REQUIREMENTS: Process data with validation and error checking")
            enhanced_parts.append("OUTPUT: Processed data with quality metrics")
        
        # Add success criteria if missing
        if not analysis["has_success_criteria"]:
            enhanced_parts.append("SUCCESS CRITERIA: Clear, actionable output that advances the Redis AI Challenge submission")
        
        return "\n\n".join(enhanced_parts)
    
    def _format_high_quality_prompt(self, prompt: str) -> str:
        """Format an already high-quality prompt"""
        return f"HIGH-QUALITY PROMPT:\n\n{prompt}\n\nEXPECTED: Professional output matching prompt specifications"

@mcp.tool()
def enhance_mcp_prompt(original_prompt: str, server_type: str, context_json: str = "{}") -> str:
    """
    Enhance a prompt for better MCP server coordination
    
    Args:
        original_prompt: The original prompt to enhance
        server_type: Type of MCP server (text-processor, command-executor, etc.)
        context_json: JSON string with additional context
    """
    
    enhancer = PromptEnhancer()
    context = json.loads(context_json) if context_json != "{}" else {}
    
    enhanced = enhancer.enhance_prompt(original_prompt, server_type, context)
    
    return f"""✅ PROMPT ENHANCED FOR {server_type.upper()}:

{enhanced}

📊 ENHANCEMENT APPLIED:
- Added structured format for better coordination
- Included server-specific requirements
- Enhanced with context and success criteria
- Improved specificity for better results
"""

@mcp.tool()
def analyze_prompt_effectiveness(prompt: str) -> str:
    """Analyze the effectiveness of an MCP prompt"""
    
    enhancer = PromptEnhancer()
    analysis = enhancer.analyze_prompt_quality(prompt)
    
    recommendations = []
    if not analysis["has_context"]:
        recommendations.append("Add CONTEXT section for better understanding")
    if not analysis["has_task"]:
        recommendations.append("Add clear TASK definition")
    if not analysis["has_constraints"]:
        recommendations.append("Add CONSTRAINTS or REQUIREMENTS section")
    if analysis["specificity_score"] < 5:
        recommendations.append("Add more specific details (numbers, file names, commands)")
    
    return f"""📊 PROMPT ANALYSIS:

Quality Score: {analysis['quality_score']}/100
Length: {analysis['length']} characters
Specificity Score: {analysis['specificity_score']}

✅ PRESENT:
- Context: {'Yes' if analysis['has_context'] else 'No'}
- Clear Task: {'Yes' if analysis['has_task'] else 'No'}
- Constraints: {'Yes' if analysis['has_constraints'] else 'No'}
- Success Criteria: {'Yes' if analysis['has_success_criteria'] else 'No'}
- Output Format: {'Yes' if analysis['has_output_format'] else 'No'}

🔧 RECOMMENDATIONS:
{chr(10).join(f"- {rec}" for rec in recommendations) if recommendations else "- Prompt is well-structured"}
"""

@mcp.tool()
def create_context_template(project_type: str = "redis-ai-challenge") -> str:
    """Create a context template for consistent MCP prompting"""
    
    templates = {
        "redis-ai-challenge": {
            "DEADLINE": "Redis AI Challenge 2025 submission due August 10, 2025 at 11:59 PM PT",
            "STAKES": "$3000 prize pool, competitive judging on innovation and technical excellence",
            "TECH_STACK": "Redis, Python, MCP servers, FastMCP, Emacs integration",
            "STATUS": "77 passing tests, 92% coverage, production-ready package",
            "GOAL": "Win competition with revolutionary homoiconic AI system"
        }
    }
    
    template = templates.get(project_type, templates["redis-ai-challenge"])
    
    context_template = f"""CONTEXT TEMPLATE FOR {project_type.upper()}:

DEADLINE: {template['DEADLINE']}
STAKES: {template['STAKES']}
TECH_STACK: {template['TECH_STACK']}
CURRENT_STATUS: {template['STATUS']}
PRIMARY_GOAL: {template['GOAL']}

USAGE:
Include relevant sections in your MCP prompts for better coordination.
Customize with specific task details and requirements.
"""
    
    return context_template

if __name__ == "__main__":
    mcp.run()