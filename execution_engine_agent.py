#!/usr/bin/env python3
"""
Execution Engine Agent with Safe Code Generation
Safely executes code, generates implementations, and manages execution environments
"""

import redis
import json
import time
import hashlib
import subprocess
import tempfile
import os
import sys
import ast
import re
from typing import Dict, List, Optional, Tuple, Set, Any, Union
from dataclasses import dataclass, asdict
from collections import deque
from pathlib import Path
import fastmcp


@dataclass
class ExecutionResult:
    execution_id: str
    code: str
    language: str
    execution_mode: str  # 'safe', 'sandbox', 'preview', 'full'
    success: bool
    output: str
    error: str
    execution_time: float
    timestamp: float
    security_analysis: Dict[str, Any]


@dataclass
class CodeTemplate:
    template_id: str
    name: str
    language: str
    template_code: str
    parameters: List[str]
    description: str
    safety_level: str  # 'safe', 'moderate', 'requires_review'


class SecurityAnalyzer:
    def __init__(self):
        self.dangerous_patterns = {
            "file_system": [
                r"\bopen\s*\(",
                r"\bfile\s*\(",
                r"\bos\..*",
                r"\bshutil\..*",
                r"\bpathlib\..*\.write",
                r"__file__",
                r"__import__",
            ],
            "network": [
                r"\burllib\.",
                r"\brequests\.",
                r"\bsocket\.",
                r"\bhttp\.",
                r"\bftplib\.",
                r"\bsmtplib\.",
            ],
            "system": [
                r"\bsubprocess\.",
                r"\bos\.system",
                r"\beval\s*\(",
                r"\bexec\s*\(",
                r"\b__.*__",
                r"\bgetattr\s*\(",
                r"\bsetattr\s*\(",
                r"\bdelattr\s*\(",
            ],
            "dangerous_builtins": [
                r"\bglobals\s*\(",
                r"\blocals\s*\(",
                r"\bvars\s*\(",
                r"\bdir\s*\(",
                r"\bcompile\s*\(",
                r"\bmemoryview\s*\(",
            ],
        }

        self.safe_patterns = {
            "data_structures": [
                r"\blist\s*\(",
                r"\bdict\s*\(",
                r"\bset\s*\(",
                r"\btuple\s*\(",
                r"\.append\s*\(",
                r"\.extend\s*\(",
                r"\.update\s*\(",
            ],
            "math_operations": [
                r"\bmath\.",
                r"\bstatistics\.",
                r"\bnumpy\.",
                r"\bpandas\.",
                r"\+|\-|\*|\/|\%",
                r"\bsum\s*\(",
                r"\bmin\s*\(",
                r"\bmax\s*\(",
            ],
            "string_operations": [
                r"\.join\s*\(",
                r"\.split\s*\(",
                r"\.replace\s*\(",
                r"\.format\s*\(",
                r'f".*"',
                r"f'.*'",
            ],
        }

    def analyze_code(self, code: str, language: str = "python") -> Dict[str, Any]:
        """Analyze code for security risks"""
        if language != "python":
            # For non-Python code, do basic pattern analysis
            return self._analyze_generic_code(code, language)

        analysis = {
            "safety_level": "safe",
            "risk_score": 0.0,
            "dangerous_patterns": [],
            "safe_patterns": [],
            "imports": [],
            "functions_defined": [],
            "syntax_valid": True,
            "recommendations": [],
        }

        # Check syntax validity
        try:
            ast.parse(code)
        except SyntaxError as e:
            analysis["syntax_valid"] = False
            analysis["syntax_error"] = str(e)
            analysis["safety_level"] = "unsafe"
            return analysis

        # Analyze imports
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        analysis["imports"].append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        analysis["imports"].append(node.module)
                elif isinstance(node, ast.FunctionDef):
                    analysis["functions_defined"].append(node.name)
        except:
            pass

        # Pattern analysis
        code_lower = code.lower()

        # Check dangerous patterns
        total_dangerous = 0
        for category, patterns in self.dangerous_patterns.items():
            found_patterns = []
            for pattern in patterns:
                matches = re.findall(pattern, code, re.IGNORECASE)
                if matches:
                    found_patterns.extend(matches)
                    total_dangerous += len(matches)

            if found_patterns:
                analysis["dangerous_patterns"].append(
                    {
                        "category": category,
                        "patterns": found_patterns,
                        "count": len(found_patterns),
                    }
                )

        # Check safe patterns
        total_safe = 0
        for category, patterns in self.safe_patterns.items():
            found_patterns = []
            for pattern in patterns:
                matches = re.findall(pattern, code, re.IGNORECASE)
                if matches:
                    found_patterns.extend(matches)
                    total_safe += len(matches)

            if found_patterns:
                analysis["safe_patterns"].append(
                    {"category": category, "count": len(found_patterns)}
                )

        # Calculate risk score
        analysis["risk_score"] = total_dangerous / max(total_dangerous + total_safe, 1)

        # Determine safety level
        if total_dangerous == 0:
            analysis["safety_level"] = "safe"
        elif total_dangerous <= 2 and analysis["risk_score"] < 0.3:
            analysis["safety_level"] = "moderate"
            analysis["recommendations"].append(
                "Review dangerous patterns before execution"
            )
        else:
            analysis["safety_level"] = "unsafe"
            analysis["recommendations"].append(
                "Code contains multiple dangerous patterns - avoid execution"
            )

        # Specific import warnings
        dangerous_imports = ["os", "subprocess", "sys", "eval", "exec"]
        for imp in analysis["imports"]:
            if any(danger in imp for danger in dangerous_imports):
                analysis["recommendations"].append(f"Review import: {imp}")

        return analysis


class CodeGenerator:
    def __init__(self):
        self.templates = self._load_templates()

    def _load_templates(self) -> Dict[str, CodeTemplate]:
        """Load code generation templates"""
        templates = {}

        # MCP Server template
        templates["mcp_server"] = CodeTemplate(
            template_id="mcp_server",
            name="FastMCP Server",
            language="python",
            template_code='''#!/usr/bin/env python3
"""
{description}
"""

import fastmcp

mcp = fastmcp.FastMCP("{server_name}")

@mcp.tool()
def {function_name}({parameters}) -> str:
    """{function_description}"""
    # Implementation here
    return "Function executed successfully"

if __name__ == "__main__":
    print("🚀 Starting {server_name} FastMCP Server")
    fastmcp.run_stdio_async(mcp)
''',
            parameters=[
                "server_name",
                "function_name",
                "parameters",
                "function_description",
                "description",
            ],
            description="Template for creating FastMCP servers",
            safety_level="safe",
        )

        # Elisp function template
        templates["elisp_function"] = CodeTemplate(
            template_id="elisp_function",
            name="Emacs Lisp Function",
            language="elisp",
            template_code="""(defun {function_name} ({parameters})
  "{docstring}"
  (interactive)
  ;; Implementation here
  {body})
""",
            parameters=["function_name", "parameters", "docstring", "body"],
            description="Template for creating Emacs Lisp functions",
            safety_level="safe",
        )

        # Redis coordination class
        templates["redis_coordinator"] = CodeTemplate(
            template_id="redis_coordinator",
            name="Redis Coordinator",
            language="python",
            template_code='''import redis
import json
import time
from typing import Dict, List, Optional

class {class_name}:
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client or redis.Redis(decode_responses=True)
        self.stream_name = "{stream_name}"
    
    def publish_event(self, event_type: str, data: Dict[str, any]) -> str:
        """Publish event to Redis stream"""
        event_data = {{
            'event_type': event_type,
            'timestamp': time.time(),
            'data': json.dumps(data)
        }}
        
        message_id = self.redis_client.xadd(self.stream_name, event_data)
        return message_id
    
    def consume_events(self, count: int = 10) -> List[Dict[str, any]]:
        """Consume events from Redis stream"""
        messages = self.redis_client.xrange(self.stream_name, count=count)
        
        events = []
        for message_id, fields in messages:
            events.append({{
                'message_id': message_id,
                'event_type': fields['event_type'],
                'timestamp': float(fields['timestamp']),
                'data': json.loads(fields['data'])
            }})
        
        return events
''',
            parameters=["class_name", "stream_name"],
            description="Template for Redis coordination classes",
            safety_level="safe",
        )

        return templates

    def generate_code(self, template_id: str, parameters: Dict[str, str]) -> str:
        """Generate code from template"""
        if template_id not in self.templates:
            raise ValueError(f"Template {template_id} not found")

        template = self.templates[template_id]
        code = template.template_code

        # Replace parameters
        for param, value in parameters.items():
            placeholder = f"{{{param}}}"
            code = code.replace(placeholder, value)

        return code

    def get_available_templates(self) -> List[Dict[str, str]]:
        """Get list of available templates"""
        return [
            {
                "id": template.template_id,
                "name": template.name,
                "language": template.language,
                "description": template.description,
                "safety_level": template.safety_level,
                "parameters": template.parameters,
            }
            for template in self.templates.values()
        ]


class ExecutionEngineAgent:
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client or redis.Redis(decode_responses=True)
        self.security_analyzer = SecurityAnalyzer()
        self.code_generator = CodeGenerator()
        self.execution_history = deque(maxlen=100)

        # Safe execution environments
        self.safe_builtins = {
            "len",
            "str",
            "int",
            "float",
            "bool",
            "list",
            "dict",
            "set",
            "tuple",
            "min",
            "max",
            "sum",
            "abs",
            "round",
            "sorted",
            "reversed",
            "enumerate",
            "zip",
            "map",
            "filter",
            "range",
            "print",
        }

    def execute_code(
        self, code: str, language: str = "python", execution_mode: str = "safe"
    ) -> ExecutionResult:
        """Execute code with safety analysis"""

        execution_id = hashlib.md5(f"{code}{time.time()}".encode()).hexdigest()[:12]
        start_time = time.time()

        # Analyze security
        security_analysis = self.security_analyzer.analyze_code(code, language)

        # Determine if execution is allowed
        if execution_mode == "safe" and security_analysis["safety_level"] == "unsafe":
            return ExecutionResult(
                execution_id=execution_id,
                code=code,
                language=language,
                execution_mode=execution_mode,
                success=False,
                output="",
                error="Code rejected due to security analysis",
                execution_time=0,
                timestamp=time.time(),
                security_analysis=security_analysis,
            )

        # Execute based on mode and language
        try:
            if language == "python":
                output, error = self._execute_python(code, execution_mode)
            elif language == "elisp":
                output, error = self._execute_elisp(code, execution_mode)
            else:
                output, error = "", f"Unsupported language: {language}"

            success = error == ""

        except Exception as e:
            output, error = "", str(e)
            success = False

        execution_time = time.time() - start_time

        result = ExecutionResult(
            execution_id=execution_id,
            code=code,
            language=language,
            execution_mode=execution_mode,
            success=success,
            output=output,
            error=error,
            execution_time=execution_time,
            timestamp=time.time(),
            security_analysis=security_analysis,
        )

        # Store result
        self._store_execution_result(result)

        return result

    def _execute_python(self, code: str, execution_mode: str) -> Tuple[str, str]:
        """Execute Python code with different safety levels"""

        if execution_mode == "preview":
            return f"[PREVIEW MODE - Would execute]\n{code}", ""

        elif execution_mode == "safe":
            # Restricted execution
            safe_globals = {
                name: getattr(__builtins__, name)
                for name in self.safe_builtins
                if hasattr(__builtins__, name)
            }
            safe_globals["__builtins__"] = {}

            try:
                # Capture output
                import io
                import contextlib

                output_buffer = io.StringIO()

                with contextlib.redirect_stdout(output_buffer):
                    exec(code, safe_globals, {})

                return output_buffer.getvalue(), ""

            except Exception as e:
                return "", str(e)

        elif execution_mode == "sandbox":
            # Execute in temporary file (more isolation)
            try:
                with tempfile.NamedTemporaryFile(
                    mode="w", suffix=".py", delete=False
                ) as f:
                    f.write(code)
                    temp_file = f.name

                result = subprocess.run(
                    [sys.executable, temp_file],
                    capture_output=True,
                    text=True,
                    timeout=10,  # 10 second timeout
                    cwd=tempfile.gettempdir(),  # Run in temp directory
                )

                os.unlink(temp_file)  # Clean up

                if result.returncode == 0:
                    return result.stdout, ""
                else:
                    return result.stdout, result.stderr

            except subprocess.TimeoutExpired:
                return "", "Execution timed out (10 seconds)"
            except Exception as e:
                return "", str(e)

        else:  # full execution
            return "", "Full execution mode not implemented for security reasons"

    def _store_execution_result(self, result: ExecutionResult):
        """Store execution result in Redis"""

        # Store in stream for real-time monitoring
        self.redis_client.xadd(
            "execution:results",
            {
                "execution_id": result.execution_id,
                "language": result.language,
                "execution_mode": result.execution_mode,
                "success": str(result.success),
                "execution_time": str(result.execution_time),
                "timestamp": str(result.timestamp),
                "safety_level": result.security_analysis.get("safety_level", "unknown"),
            },
        )

        # Store detailed result
        result_data = asdict(result)
        # Convert security_analysis to JSON string
        result_data["security_analysis"] = json.dumps(result.security_analysis)

        self.redis_client.hset(
            f"execution:detail:{result.execution_id}",
            mapping={key: str(value) for key, value in result_data.items()},
        )

        # Set expiration (keep results for 24 hours)
        self.redis_client.expire(f"execution:detail:{result.execution_id}", 24 * 3600)

    def get_execution_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent execution history"""
        results = self.redis_client.xrevrange("execution:results", count=limit)

        history = []
        for message_id, fields in results:
            history.append(
                {
                    "message_id": message_id,
                    "execution_id": fields["execution_id"],
                    "language": fields["language"],
                    "execution_mode": fields["execution_mode"],
                    "success": fields["success"] == "True",
                    "execution_time": float(fields["execution_time"]),
                    "timestamp": float(fields["timestamp"]),
                    "safety_level": fields["safety_level"],
                }
            )

        return history


# FastMCP Server
mcp = fastmcp.FastMCP("execution-engine")
agent = ExecutionEngineAgent()


@mcp.tool()
def execute_code(
    code: str, language: str = "python", execution_mode: str = "safe"
) -> str:
    """Execute code with security analysis and safety controls"""
    result = agent.execute_code(code, language, execution_mode)

    response = f"⚙️ **EXECUTION RESULT: {result.execution_id}**\n\n"
    response += f"**Language:** {result.language}\n"
    response += f"**Mode:** {result.execution_mode}\n"
    response += f"**Success:** {'✅' if result.success else '❌'}\n"
    response += f"**Execution Time:** {result.execution_time:.3f}s\n"
    response += f"**Safety Level:** {result.security_analysis.get('safety_level', 'unknown')}\n\n"

    if result.success and result.output:
        response += f"**Output:**\n```\n{result.output}\n```\n\n"

    if result.error:
        response += f"**Error:**\n```\n{result.error}\n```\n\n"

    # Security analysis summary
    analysis = result.security_analysis
    if "dangerous_patterns" in analysis and analysis["dangerous_patterns"]:
        response += f"**Security Warnings:** {len(analysis['dangerous_patterns'])} dangerous patterns detected\n"

    if "recommendations" in analysis and analysis["recommendations"]:
        response += f"**Recommendations:**\n"
        for rec in analysis["recommendations"]:
            response += f"  - {rec}\n"

    return response


@mcp.tool()
def analyze_code_security(code: str, language: str = "python") -> str:
    """Analyze code for security risks without executing"""
    analysis = agent.security_analyzer.analyze_code(code, language)

    response = f"🔒 **SECURITY ANALYSIS**\n\n"
    response += f"**Language:** {language}\n"
    response += f"**Safety Level:** {analysis.get('safety_level', 'unknown')}\n"
    response += f"**Risk Score:** {analysis.get('risk_score', 0):.2f}\n"
    response += (
        f"**Syntax Valid:** {'✅' if analysis.get('syntax_valid', True) else '❌'}\n\n"
    )

    if "dangerous_patterns" in analysis and analysis["dangerous_patterns"]:
        response += f"**Dangerous Patterns Found:**\n"
        for pattern_group in analysis["dangerous_patterns"]:
            response += (
                f"  - {pattern_group['category']}: {pattern_group['count']} matches\n"
            )
        response += "\n"

    if "imports" in analysis and analysis["imports"]:
        response += f"**Imports:** {', '.join(analysis['imports'])}\n\n"

    if "recommendations" in analysis and analysis["recommendations"]:
        response += f"**Recommendations:**\n"
        for rec in analysis["recommendations"]:
            response += f"  - {rec}\n"

    return response


@mcp.tool()
def generate_code_from_template(template_id: str, parameters: dict) -> str:
    """Generate code from a template"""
    try:
        code = agent.code_generator.generate_code(template_id, parameters)

        # Analyze generated code
        analysis = agent.security_analyzer.analyze_code(code)

        response = f"🏗️ **CODE GENERATED: {template_id}**\n\n"
        response += f"**Safety Level:** {analysis.get('safety_level', 'unknown')}\n\n"
        response += f"**Generated Code:**\n```{agent.code_generator.templates[template_id].language}\n{code}\n```\n\n"

        if analysis.get("recommendations"):
            response += f"**Recommendations:**\n"
            for rec in analysis["recommendations"]:
                response += f"  - {rec}\n"

        return response

    except Exception as e:
        return f"❌ Code generation failed: {str(e)}"


@mcp.tool()
def list_code_templates() -> str:
    """List available code generation templates"""
    templates = agent.code_generator.get_available_templates()

    response = f"🏗️ **AVAILABLE CODE TEMPLATES**\n\n"

    for template in templates:
        response += f"**{template['name']} ({template['id']})**\n"
        response += f"  Language: {template['language']}\n"
        response += f"  Safety: {template['safety_level']}\n"
        response += f"  Description: {template['description']}\n"
        response += f"  Parameters: {', '.join(template['parameters'])}\n\n"

    return response


@mcp.tool()
def get_execution_history(limit: int = 5) -> str:
    """Get recent code execution history"""
    history = agent.get_execution_history(limit)

    if not history:
        return "📜 No execution history available"

    response = f"📜 **EXECUTION HISTORY**\n\n"

    for entry in history:
        time_str = time.strftime("%H:%M:%S", time.localtime(entry["timestamp"]))
        status = "✅" if entry["success"] else "❌"

        response += f"**{time_str} - {entry['execution_id']}**\n"
        response += f"  {status} {entry['language']} ({entry['execution_mode']}) - {entry['execution_time']:.3f}s\n"
        response += f"  Safety: {entry['safety_level']}\n\n"

    return response


@mcp.tool()
def execution_engine_status() -> str:
    """Get execution engine status and statistics"""
    # Get execution stats
    total_executions = agent.redis_client.xlen("execution:results")

    # Get recent success rate
    recent_results = agent.redis_client.xrevrange("execution:results", count=20)
    if recent_results:
        recent_successes = sum(
            1 for _, fields in recent_results if fields.get("success") == "True"
        )
        success_rate = (recent_successes / len(recent_results)) * 100
    else:
        success_rate = 0

    # Get language distribution
    language_counts = {}
    for _, fields in recent_results:
        lang = fields.get("language", "unknown")
        language_counts[lang] = language_counts.get(lang, 0) + 1

    response = f"⚙️ **EXECUTION ENGINE STATUS**\n\n"
    response += f"**Total Executions:** {total_executions}\n"
    response += f"**Recent Success Rate:** {success_rate:.1f}% (last 20)\n"
    response += f"**Available Templates:** {len(agent.code_generator.templates)}\n\n"

    if language_counts:
        response += f"**Recent Language Usage:**\n"
        for lang, count in sorted(
            language_counts.items(), key=lambda x: x[1], reverse=True
        ):
            response += f"  - {lang}: {count}\n"

    response += f"\n**Execution Modes Available:**\n"
    response += f"  - safe: Restricted Python execution\n"
    response += f"  - sandbox: Isolated subprocess execution\n"
    response += f"  - preview: Code analysis without execution\n"

    return response


if __name__ == "__main__":
    print("⚙️ Starting Execution Engine Agent FastMCP Server")
    mcp.run()
