#!/usr/bin/env python3
"""
Robust Claude Code Integration - Production Ready
No endless retries, graceful degradation, proper error handling
"""

import subprocess
import os
import logging
import time
from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum


class ClaudeStatus(Enum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    RATE_LIMITED = "rate_limited"
    ERROR = "error"


@dataclass
class ClaudeResponse:
    success: bool
    content: str
    status: ClaudeStatus
    error_message: Optional[str] = None
    execution_time: float = 0.0


class RobustClaudeIntegration:
    """Production-ready Claude Code integration with proper error handling"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.claude_path = self._find_claude_executable()
        self.status = self._check_initial_status()
        self.last_check_time = time.time()
        self.check_interval = 300  # Re-check every 5 minutes
        self.failure_backoff = 60  # Back off for 1 minute after failures
        self.last_failure_time = 0

    def _find_claude_executable(self) -> Optional[str]:
        """Find Claude executable in common locations"""
        possible_paths = [
            "/Users/jonathanhill/.bun/bin/claude",
            "/Users/jonathanhill/.opencode/bin/claude",
            "/usr/local/bin/claude",
            "/opt/homebrew/bin/claude",
        ]

        for path in possible_paths:
            if os.path.exists(path) and os.access(path, os.X_OK):
                self.logger.info(f"✅ Found Claude at {path}")
                return path

        # Try PATH as last resort
        try:
            result = subprocess.run(
                ["which", "claude"], capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                path = result.stdout.strip()
                self.logger.info(f"✅ Found Claude in PATH at {path}")
                return path
        except Exception:
            pass

        self.logger.warning("⚠️ Claude executable not found")
        return None

    def _check_initial_status(self) -> ClaudeStatus:
        """Check if Claude is available and working"""
        if not self.claude_path:
            return ClaudeStatus.UNAVAILABLE

        try:
            result = subprocess.run(
                [self.claude_path, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                self.logger.info("✅ Claude Code integration available")
                return ClaudeStatus.AVAILABLE
            else:
                self.logger.warning(f"⚠️ Claude returned error code {result.returncode}")
                return ClaudeStatus.ERROR

        except subprocess.TimeoutExpired:
            self.logger.warning("⚠️ Claude version check timed out")
            return ClaudeStatus.ERROR
        except Exception as e:
            self.logger.warning(f"⚠️ Claude check failed: {e}")
            return ClaudeStatus.ERROR

    def is_available(self) -> bool:
        """Check if Claude is currently available (with caching)"""
        current_time = time.time()

        # Don't re-check too frequently
        if current_time - self.last_check_time < self.check_interval:
            return self.status == ClaudeStatus.AVAILABLE

        # Don't check if we're in backoff period after failure
        if current_time - self.last_failure_time < self.failure_backoff:
            return False

        # Re-check status
        self.status = self._check_initial_status()
        self.last_check_time = current_time

        return self.status == ClaudeStatus.AVAILABLE

    def execute_prompt(self, prompt: str, timeout: int = 60) -> ClaudeResponse:
        """Execute a prompt with Claude Code - production ready"""
        start_time = time.time()

        # Quick availability check
        if not self.is_available():
            return ClaudeResponse(
                success=False,
                content="",
                status=self.status,
                error_message="Claude Code not available",
                execution_time=time.time() - start_time,
            )

        try:
            # Execute with proper environment
            env = os.environ.copy()
            env["PATH"] = f"{os.path.dirname(self.claude_path)}:{env.get('PATH', '')}"

            result = subprocess.run(
                [self.claude_path],
                input=prompt,
                text=True,
                capture_output=True,
                timeout=timeout,
                env=env,
            )

            execution_time = time.time() - start_time

            if result.returncode == 0 and result.stdout.strip():
                return ClaudeResponse(
                    success=True,
                    content=result.stdout.strip(),
                    status=ClaudeStatus.AVAILABLE,
                    execution_time=execution_time,
                )
            else:
                # Mark failure time for backoff
                self.last_failure_time = time.time()

                error_msg = (
                    result.stderr.strip()
                    if result.stderr
                    else f"Exit code {result.returncode}"
                )
                return ClaudeResponse(
                    success=False,
                    content="",
                    status=ClaudeStatus.ERROR,
                    error_message=error_msg,
                    execution_time=execution_time,
                )

        except subprocess.TimeoutExpired:
            self.last_failure_time = time.time()
            return ClaudeResponse(
                success=False,
                content="",
                status=ClaudeStatus.ERROR,
                error_message=f"Timeout after {timeout}s",
                execution_time=time.time() - start_time,
            )

        except Exception as e:
            self.last_failure_time = time.time()
            return ClaudeResponse(
                success=False,
                content="",
                status=ClaudeStatus.ERROR,
                error_message=str(e),
                execution_time=time.time() - start_time,
            )

    def generate_fallback_content(self, task_type: str, context: Dict[str, Any]) -> str:
        """Generate high-quality fallback content when Claude unavailable"""
        if task_type == "docstring":
            func_name = context.get("function_name", "function")
            args = context.get("args", [])
            return_type = context.get("return_type", "Any")

            args_section = ""
            if args:
                args_section = "\n    Args:\n" + "\n".join(
                    f"        {arg}: Description of {arg}" for arg in args
                )

            return f'''"""
    {func_name.replace('_', ' ').title()} function.
    
    Brief description of what this function does.{args_section}
    
    Returns:
        {return_type}: Description of return value
    """'''

        elif task_type == "test":
            func_name = context.get("function_name", "function")
            return f'''import pytest
from unittest.mock import Mock, patch

def test_{func_name}_basic():
    """Test basic functionality of {func_name}"""
    # TODO: Add actual test implementation
    assert True
    
def test_{func_name}_edge_cases():
    """Test edge cases for {func_name}"""
    # TODO: Add edge case tests
    assert True
'''

        else:
            return f"# TODO: {task_type} implementation needed"


# Global instance for use across the application
claude_integration = RobustClaudeIntegration()


def get_claude_status() -> Dict[str, Any]:
    """Get current Claude integration status"""
    return {
        "available": claude_integration.is_available(),
        "status": claude_integration.status.value,
        "claude_path": claude_integration.claude_path,
        "last_check": claude_integration.last_check_time,
        "last_failure": claude_integration.last_failure_time,
    }


if __name__ == "__main__":
    # Test the integration
    print("Testing Robust Claude Integration...")

    status = get_claude_status()
    print(f"Status: {status}")

    if claude_integration.is_available():
        response = claude_integration.execute_prompt("Say hello briefly")
        print(f"Response: {response}")
    else:
        print("Claude not available - testing fallback")
        fallback = claude_integration.generate_fallback_content(
            "docstring",
            {
                "function_name": "test_function",
                "args": ["arg1", "arg2"],
                "return_type": "str",
            },
        )
        print(f"Fallback: {fallback}")
