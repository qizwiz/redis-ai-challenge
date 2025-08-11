#!/usr/bin/env python3
"""
Code Analyzer Agent - Advanced AI agent for real-time code analysis
Part of the AI-Emacs Integration System
"""

import asyncio
import json
import re
import ast
import redis
import time
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
from redis_coordination_protocol import AIAgent, EventType, CoordinationEvent


@dataclass
class SyntaxIssue:
    """Represents a syntax issue found in code"""

    line: int
    column: int
    severity: str  # 'error', 'warning', 'info'
    message: str
    suggestion: Optional[str] = None


@dataclass
class CodeMetrics:
    """Code quality metrics"""

    lines_of_code: int
    complexity_score: float
    documentation_ratio: float
    duplication_score: float
    maintainability_index: float


class EmacsLispAnalyzer:
    """Analyzer specifically for Emacs Lisp code"""

    def __init__(self):
        self.known_functions = self._load_elisp_functions()
        self.style_patterns = self._load_style_patterns()

    def _load_elisp_functions(self) -> Set[str]:
        """Load known Emacs Lisp functions (placeholder for now)"""
        return set()

    def _load_style_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Load Emacs Lisp style guide patterns"""
        return {
            "function_naming": {
                "pattern": r"^[a-z][a-z0-9-]*[a-z0-9]$",
                "message": "Function names should use lowercase with hyphens",
                "severity": "warning",
            },
            "variable_naming": {
                "pattern": r"^[a-z][a-z0-9-]*[a-z0-9]$",
                "message": "Variable names should use lowercase with hyphens",
                "severity": "warning",
            },
            "line_length": {
                "max_length": 80,
                "message": "Lines should not exceed 80 characters",
                "severity": "info",
            },
            "documentation": {
                "pattern": r'^\s*"[^"]*"',
                "message": "Functions should have documentation strings",
                "severity": "info",
            },
        }

    def analyze(self, content: str) -> Tuple[List[SyntaxIssue], CodeMetrics]:
        """Analyze Emacs Lisp code"""
        issues = []
        lines = content.split("\n")

        # Basic syntax validation
        issues.extend(self._check_parentheses(content))
        issues.extend(self._check_style_guide(lines))
        issues.extend(self._check_function_usage(content))

        # Calculate metrics
        metrics = self._calculate_metrics(lines)

        return issues, metrics

    def _check_parentheses(self, content: str) -> List[SyntaxIssue]:
        """Check for balanced parentheses"""
        issues = []
        stack = []
        lines = content.split("\n")

        for line_num, line in enumerate(lines, 1):
            for col_num, char in enumerate(line):
                if char == "(":
                    stack.append((line_num, col_num))
                elif char == ")":
                    if not stack:
                        issues.append(
                            SyntaxIssue(
                                line=line_num,
                                column=col_num,
                                severity="error",
                                message="Unmatched closing parenthesis",
                                suggestion="Remove this parenthesis or add matching opening parenthesis",
                            )
                        )
                    else:
                        stack.pop()

        # Check for unmatched opening parentheses
        for line_num, col_num in stack:
            issues.append(
                SyntaxIssue(
                    line=line_num,
                    column=col_num,
                    severity="error",
                    message="Unmatched opening parenthesis",
                    suggestion="Add matching closing parenthesis",
                )
            )

        return issues

    def _check_style_guide(self, lines: List[str]) -> List[SyntaxIssue]:
        """Check style guide compliance"""
        issues = []

        for line_num, line in enumerate(lines, 1):
            # Check line length
            if len(line) > self.style_patterns["line_length"]["max_length"]:
                issues.append(
                    SyntaxIssue(
                        line=line_num,
                        column=len(line),
                        severity=self.style_patterns["line_length"]["severity"],
                        message=self.style_patterns["line_length"]["message"],
                        suggestion="Break long line into multiple lines",
                    )
                )

            # Check function definitions
            if line.strip().startswith("(defun "):
                func_match = re.search(r"\(defun\s+([a-zA-Z0-9-]+)", line)
                if func_match:
                    func_name = func_match.group(1)
                    if not re.match(
                        self.style_patterns["function_naming"]["pattern"], func_name
                    ):
                        issues.append(
                            SyntaxIssue(
                                line=line_num,
                                column=func_match.start(1),
                                severity=self.style_patterns["function_naming"][
                                    "severity"
                                ],
                                message=self.style_patterns["function_naming"][
                                    "message"
                                ],
                                suggestion=f'Rename "{func_name}" to use lowercase with hyphens',
                            )
                        )

        return issues

    def _calculate_metrics(self, lines: List[str]) -> CodeMetrics:
        """Calculate code quality metrics"""
        total_lines = len(lines)
        code_lines = sum(
            1 for line in lines if line.strip() and not line.strip().startswith(";")
        )
        comment_lines = sum(1 for line in lines if line.strip().startswith(";"))

        # Simple complexity based on nested structures
        complexity = 0
        for line in lines:
            complexity += (
                line.count("(if ") + line.count("(when ") + line.count("(unless ")
            )
            complexity += line.count("(while ") + line.count("(dolist ")

        # Documentation ratio
        doc_lines = sum(1 for line in lines if re.match(r'^\s*"[^"]*"', line))
        doc_ratio = doc_lines / max(code_lines, 1)

        # Simple duplication detection
        line_counts = {}
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith(";"):
                line_counts[stripped] = line_counts.get(stripped, 0) + 1

        duplicated_lines = sum(count - 1 for count in line_counts.values() if count > 1)
        duplication_score = duplicated_lines / max(code_lines, 1)

        # Maintainability index (simplified)
        maintainability = max(0, 100 - complexity * 5 - duplication_score * 20)

        return CodeMetrics(
            lines_of_code=code_lines,
            complexity_score=complexity / max(code_lines, 1),
            documentation_ratio=doc_ratio,
            duplication_score=duplication_score,
            maintainability_index=maintainability,
        )


class PythonAnalyzer:
    """Analyzer for Python code"""

    def analyze(self, content: str) -> Tuple[List[SyntaxIssue], CodeMetrics]:
        """Analyze Python code"""
        issues = []

        try:
            # Parse with AST for syntax validation
            tree = ast.parse(content)
            issues.extend(self._analyze_ast(tree))
        except SyntaxError as e:
            issues.append(
                SyntaxIssue(
                    line=e.lineno or 1,
                    column=e.offset or 1,
                    severity="error",
                    message=f"Syntax error: {e.msg}",
                    suggestion="Fix syntax error",
                )
            )

        # Calculate metrics
        lines = content.split("\n")
        metrics = self._calculate_python_metrics(lines)

        return issues, metrics

    def _analyze_ast(self, tree: ast.AST) -> List[SyntaxIssue]:
        """Analyze Python AST for issues"""
        issues = []

        for node in ast.walk(tree):
            # Check for potential issues
            if isinstance(node, ast.FunctionDef):
                if len(node.name) < 3:
                    issues.append(
                        SyntaxIssue(
                            line=node.lineno,
                            column=node.col_offset,
                            severity="warning",
                            message=f'Function name "{node.name}" is too short',
                            suggestion="Use more descriptive function names",
                        )
                    )

            elif isinstance(node, ast.Name) and node.id.isupper() and len(node.id) > 1:
                if not hasattr(node, "annotation"):  # Not a constant
                    issues.append(
                        SyntaxIssue(
                            line=node.lineno,
                            column=node.col_offset,
                            severity="info",
                            message=f'Variable "{node.id}" uses all caps',
                            suggestion="Reserve ALL_CAPS for constants",
                        )
                    )

        return issues

    def _calculate_python_metrics(self, lines: List[str]) -> CodeMetrics:
        """Calculate Python code metrics"""
        code_lines = sum(
            1 for line in lines if line.strip() and not line.strip().startswith("#")
        )
        comment_lines = sum(1 for line in lines if line.strip().startswith("#"))

        # Simple complexity calculation
        complexity = 0
        for line in lines:
            complexity += line.count("if ") + line.count("elif ") + line.count("else:")
            complexity += line.count("for ") + line.count("while ")
            complexity += line.count("try:") + line.count("except")

        doc_ratio = comment_lines / max(code_lines, 1)

        return CodeMetrics(
            lines_of_code=code_lines,
            complexity_score=complexity / max(code_lines, 1),
            documentation_ratio=doc_ratio,
            duplication_score=0.0,  # Would need more sophisticated analysis
            maintainability_index=max(0, 100 - complexity * 3),
        )


class AdvancedCodeAnalyzerAgent(AIAgent):
    """Advanced AI agent for comprehensive code analysis"""

    def __init__(self, redis_client: redis.Redis):
        super().__init__(
            agent_id="advanced_code_analyzer",
            agent_type="analysis",
            capabilities=[
                "syntax_analysis",
                "code_quality",
                "style_checking",
                "metrics_calculation",
                "multi_language_support",
            ],
            redis_client=redis_client,
        )

        self.analyzers = {"elisp": EmacsLispAnalyzer(), "python": PythonAnalyzer()}

        self.analysis_cache = {}
        self.performance_metrics = {
            "analyses_performed": 0,
            "average_analysis_time": 0.0,
            "cache_hits": 0,
        }

    async def _register_handlers(self):
        """Register event handlers for content changes"""
        self.coordinator.register_event_handler(
            EventType.CONTENT_CHANGE, self._handle_content_change
        )

    def _handle_content_change(self, event: CoordinationEvent):
        print(
            f"DEBUG: Entering _handle_content_change for event type: {event.event_type}"
        )
        """Handle content change events with comprehensive analysis"""
        start_time = time.time()

        buffer_name = event.data.get("buffer_name", "")
        content = event.data.get("content", "")
        position = event.data.get("position", 0)

        # Skip empty content or very small changes
        if len(content) < 10:
            print(
                f"DEBUG: Skipping content change for {buffer_name} due to small content length ({len(content)})"
            )
            return

        # Check cache
        content_hash = hash(content)
        if content_hash in self.analysis_cache:
            cached_result = self.analysis_cache[content_hash]
            self.performance_metrics["cache_hits"] += 1

            # Publish cached results
            self.coordinator.publish_ai_analysis(
                self.agent_id, "cached_analysis", cached_result, event.correlation_id
            )
            print(f"DEBUG: Cache hit for {buffer_name}. Published cached analysis.")
            return

        # Detect language
        language = self._detect_language(buffer_name, content)
        print(
            f"DEBUG: _handle_content_change - buffer_name: {buffer_name}, content_len: {len(content)}, language: {language}"
        )

        if language in self.analyzers:
            try:
                # Perform analysis
                analyzer = self.analyzers[language]
                issues, metrics = analyzer.analyze(content)

                # Prepare results
                analysis_results = {
                    "language": language,
                    "buffer_name": buffer_name,
                    "analysis_timestamp": time.time(),
                    "syntax_issues": [
                        {
                            "line": issue.line,
                            "column": issue.column,
                            "severity": issue.severity,
                            "message": issue.message,
                            "suggestion": issue.suggestion,
                        }
                        for issue in issues
                    ],
                    "code_metrics": {
                        "lines_of_code": metrics.lines_of_code,
                        "complexity_score": metrics.complexity_score,
                        "documentation_ratio": metrics.documentation_ratio,
                        "duplication_score": metrics.duplication_score,
                        "maintainability_index": metrics.maintainability_index,
                    },
                    "quality_score": self._calculate_quality_score(issues, metrics),
                    "recommendations": self._generate_recommendations(issues, metrics),
                }

                # Cache results
                self.analysis_cache[content_hash] = analysis_results

                # Update performance metrics
                analysis_time = time.time() - start_time
                self.performance_metrics["analyses_performed"] += 1
                self.performance_metrics["average_analysis_time"] = (
                    self.performance_metrics["average_analysis_time"]
                    * (self.performance_metrics["analyses_performed"] - 1)
                    + analysis_time
                ) / self.performance_metrics["analyses_performed"]

                # Publish results
                self.coordinator.publish_ai_analysis(
                    self.agent_id,
                    "comprehensive_analysis",
                    analysis_results,
                    event.correlation_id,
                )

                # Log performance
                print(
                    f"Analysis completed in {analysis_time:.3f}s for {language} code ({len(content)} chars)"
                )

            except Exception as e:
                # Handle analysis errors gracefully
                error_result = {
                    "error": str(e),
                    "language": language,
                    "buffer_name": buffer_name,
                    "analysis_timestamp": time.time(),
                }

                self.coordinator.publish_ai_analysis(
                    self.agent_id, "analysis_error", error_result, event.correlation_id
                )
                print(f"ERROR: Analysis failed for {buffer_name} ({language}): {e}")
        else:
            # Unknown language - provide basic analysis
            basic_result = {
                "language": "unknown",
                "buffer_name": buffer_name,
                "analysis_timestamp": time.time(),
                "content_stats": {
                    "total_lines": len(content.split("\n")),
                    "total_characters": len(content),
                    "non_empty_lines": len(
                        [line for line in content.split("\n") if line.strip()]
                    ),
                },
                "message": f"Language not recognized for buffer {buffer_name}",
            }

            self.coordinator.publish_ai_analysis(
                self.agent_id, "basic_analysis", basic_result, event.correlation_id
            )
            print(
                f"DEBUG: Language not recognized for {buffer_name}. Published basic analysis."
            )

    def _generate_recommendations(
        self, issues: List[SyntaxIssue], metrics: CodeMetrics
    ) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []

        # Issue-based recommendations
        error_count = sum(1 for issue in issues if issue.severity == "error")
        warning_count = sum(1 for issue in issues if issue.severity == "warning")

        if error_count > 0:
            recommendations.append(
                f"Fix {error_count} syntax error(s) to improve code stability"
            )

        if warning_count > 0:
            recommendations.append(
                f"Address {warning_count} warning(s) to improve code quality"
            )

        # Metrics-based recommendations
        if metrics.complexity_score > 0.5:
            recommendations.append(
                "Consider breaking down complex functions for better maintainability"
            )

        if metrics.documentation_ratio < 0.2:
            recommendations.append("Add more documentation to improve code readability")

        if metrics.duplication_score > 0.3:
            recommendations.append("Refactor duplicated code into reusable functions")

        if metrics.maintainability_index < 50:
            recommendations.append(
                "Consider refactoring to improve overall maintainability"
            )

        return recommendations

    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get agent performance metrics"""
        return {
            "agent_id": self.agent_id,
            "performance": self.performance_metrics,
            "cache_size": len(self.analysis_cache),
            "supported_languages": list(self.analyzers.keys()),
        }


# Testing and Demo Functions


async def demo_code_analyzer():
    """Demonstrate the advanced code analyzer agent"""
    print("Starting Advanced Code Analyzer Demo")

    # Initialize Redis client
    redis_client = redis.Redis(decode_responses=True)

    try:
        redis_client.ping()
    except redis.ConnectionError:
        print("Could not connect to Redis. Make sure Redis is running.")
        return

    # Create and start analyzer agent
    analyzer = AdvancedCodeAnalyzerAgent(redis_client)
    await analyzer.start()

    # Test with Emacs Lisp code
    elisp_code = """
(defun my-test-function ()
  "A test function with some issues."
  (let ((x 1)
        (y 2))
    (if (> x y)
        (message "x is greater")
      (message "y is greater"))
    (when (and x y)
      (message "Both x and y exist"))))

(defvar my-test-variable 42
  "A test variable.")
"""

    # Simulate content change
    analyzer.coordinator.publish_content_change("test.el", elisp_code, 100)

    # Wait for analysis
    await asyncio.sleep(1)

    # Test with Python code
    python_code = """
def calculate_something(a, b):
    if a > b:
        return a + b
    elif a < b:
        return a - b
    else:
        return a * b

def x():  # Short function name
    VARIABLE = 5  # All caps variable
    return VARIABLE
"""

    # Simulate Python content change
    analyzer.coordinator.publish_content_change("test.py", python_code, 200)

    # Wait for analysis
    await asyncio.sleep(1)

    # Get performance metrics
    metrics = await analyzer.get_performance_metrics()
    print(f"Analyzer performance: {metrics}")

    # Stop analyzer
    await analyzer.stop()

    print("Code analyzer demo completed")


if __name__ == "__main__":
    asyncio.run(demo_code_analyzer())
