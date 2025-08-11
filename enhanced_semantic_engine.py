#!/usr/bin/env python3
"""
Enhanced Semantic Coverage Engine
Expands docstring synthesis for complex development commands
"""

import redis
import json
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import time


@dataclass
class SemanticPattern:
    pattern: str
    elisp_template: str
    confidence: float
    usage_count: int
    last_used: float


class EnhancedSemanticEngine:
    def __init__(self):
        self.redis_client = redis.Redis(decode_responses=True)
        self.semantic_patterns = self._load_enhanced_patterns()

    def _load_enhanced_patterns(self) -> Dict[str, SemanticPattern]:
        """Load expanded semantic patterns for complex commands"""

        enhanced_patterns = {
            # Development workflow patterns
            "commit_changes": SemanticPattern(
                pattern=r"commit.*changes|git.*commit|save.*work",
                elisp_template="(magit-commit-create)",
                confidence=0.9,
                usage_count=0,
                last_used=0,
            ),
            "run_tests": SemanticPattern(
                pattern=r"run.*tests?|execute.*tests?|test.*suite",
                elisp_template="(projectile-test-project)",
                confidence=0.85,
                usage_count=0,
                last_used=0,
            ),
            "search_project": SemanticPattern(
                pattern=r"search.*project|find.*in.*project|grep.*project",
                elisp_template="(projectile-grep)",
                confidence=0.8,
                usage_count=0,
                last_used=0,
            ),
            # Buffer management patterns
            "recent_files": SemanticPattern(
                pattern=r"recent.*files?|open.*recent|last.*files?",
                elisp_template="(recentf-open-files)",
                confidence=0.85,
                usage_count=0,
                last_used=0,
            ),
            "split_window_right": SemanticPattern(
                pattern=r"split.*right|window.*right|vertical.*split",
                elisp_template="(split-window-right)",
                confidence=0.9,
                usage_count=0,
                last_used=0,
            ),
            "split_window_below": SemanticPattern(
                pattern=r"split.*below|split.*down|horizontal.*split",
                elisp_template="(split-window-below)",
                confidence=0.9,
                usage_count=0,
                last_used=0,
            ),
            # Navigation patterns
            "goto_definition": SemanticPattern(
                pattern=r"go.*to.*definition|find.*definition|jump.*definition",
                elisp_template="(xref-find-definitions (thing-at-point 'symbol))",
                confidence=0.9,
                usage_count=0,
                last_used=0,
            ),
            "find_references": SemanticPattern(
                pattern=r"find.*references|show.*references|where.*used",
                elisp_template="(xref-find-references (thing-at-point 'symbol))",
                confidence=0.85,
                usage_count=0,
                last_used=0,
            ),
            # Code manipulation patterns
            "format_code": SemanticPattern(
                pattern=r"format.*code|indent.*code|beautify.*code",
                elisp_template="(indent-region (point-min) (point-max))",
                confidence=0.8,
                usage_count=0,
                last_used=0,
            ),
            "comment_region": SemanticPattern(
                pattern=r"comment.*region|comment.*out|add.*comment",
                elisp_template="(comment-region (region-beginning) (region-end))",
                confidence=0.85,
                usage_count=0,
                last_used=0,
            ),
            # Terminal and shell patterns
            "open_terminal": SemanticPattern(
                pattern=r"open.*terminal|start.*shell|launch.*terminal",
                elisp_template="(shell)",
                confidence=0.9,
                usage_count=0,
                last_used=0,
            ),
            "run_command": SemanticPattern(
                pattern=r"run.*command|execute.*command|shell.*command",
                elisp_template='(shell-command (read-string "Command: "))',
                confidence=0.75,
                usage_count=0,
                last_used=0,
            ),
            # Org-mode patterns
            "create_org_heading": SemanticPattern(
                pattern=r"create.*heading|new.*heading|add.*heading",
                elisp_template="(org-insert-heading)",
                confidence=0.8,
                usage_count=0,
                last_used=0,
            ),
            "toggle_todo": SemanticPattern(
                pattern=r"toggle.*todo|mark.*todo|todo.*state",
                elisp_template="(org-todo)",
                confidence=0.85,
                usage_count=0,
                last_used=0,
            ),
            # Complex workflow patterns
            "save_all_buffers": SemanticPattern(
                pattern=r"save.*all|save.*everything|save.*buffers",
                elisp_template="(save-some-buffers t)",
                confidence=0.9,
                usage_count=0,
                last_used=0,
            ),
            "kill_other_buffers": SemanticPattern(
                pattern=r"close.*other.*buffers|kill.*other.*buffers",
                elisp_template="(mapc 'kill-buffer (delq (current-buffer) (buffer-list)))",
                confidence=0.8,
                usage_count=0,
                last_used=0,
            ),
            # Redis-specific patterns for our system
            "check_redis_status": SemanticPattern(
                pattern=r"redis.*status|check.*redis|redis.*health",
                elisp_template='(shell-command "redis-cli ping")',
                confidence=0.85,
                usage_count=0,
                last_used=0,
            ),
            "clear_redis_streams": SemanticPattern(
                pattern=r"clear.*redis.*streams|reset.*redis|clean.*redis",
                elisp_template='(shell-command "redis-cli FLUSHDB")',
                confidence=0.7,
                usage_count=0,
                last_used=0,
            ),
        }

        return enhanced_patterns

    def analyze_command(self, natural_command: str) -> Optional[Tuple[str, float]]:
        """Analyze natural language command and return best elisp match"""

        command_lower = natural_command.lower()
        best_match = None
        best_confidence = 0.0

        for pattern_name, pattern_data in self.semantic_patterns.items():
            if re.search(pattern_data.pattern, command_lower):
                # Boost confidence based on usage patterns
                usage_boost = min(0.1, pattern_data.usage_count * 0.01)
                recency_boost = (
                    0.05 if (time.time() - pattern_data.last_used) < 3600 else 0
                )

                total_confidence = pattern_data.confidence + usage_boost + recency_boost

                if total_confidence > best_confidence:
                    best_confidence = total_confidence
                    best_match = (pattern_data.elisp_template, total_confidence)

                    # Update usage statistics
                    pattern_data.usage_count += 1
                    pattern_data.last_used = time.time()

        return best_match

    def synthesize_docstring(self, elisp_command: str, context: str = "") -> str:
        """Generate comprehensive docstring for elisp command"""

        # Enhanced docstring templates
        docstring_templates = {
            "magit-commit-create": "Create a new git commit with staged changes. Opens commit message buffer for editing.",
            "projectile-test-project": "Run the test suite for the current project. Uses project-specific test runner.",
            "projectile-grep": "Search for text across all files in the current project using grep.",
            "recentf-open-files": "Display and open from list of recently accessed files.",
            "split-window-right": "Split current window vertically, creating new window to the right.",
            "split-window-below": "Split current window horizontally, creating new window below.",
            "xref-find-definitions": "Jump to definition of symbol at point. Works with LSP and tags.",
            "xref-find-references": "Find all references to symbol at point across project.",
            "indent-region": "Auto-format and indent code in selected region or entire buffer.",
            "comment-region": "Comment out selected text region. Toggle if already commented.",
            "shell": "Open interactive shell buffer for running command-line programs.",
            "shell-command": "Execute single shell command and display output.",
            "org-insert-heading": "Create new heading in org-mode document at current level.",
            "org-todo": "Cycle through TODO states (TODO → DONE → none → TODO...).",
            "save-some-buffers": "Save all modified buffers, optionally prompting for each.",
            "redis-cli ping": "Test Redis server connectivity. Returns PONG if successful.",
        }

        # Extract base command for template lookup
        base_command = (
            elisp_command.strip("()").split()[0]
            if elisp_command.strip().startswith("(")
            else elisp_command
        )

        # Get template or generate generic one
        docstring = docstring_templates.get(
            base_command, f"Execute {base_command} command"
        )

        # Add context if provided
        if context:
            docstring += f"\n\nContext: {context}"

        # Add usage pattern if available
        for pattern_name, pattern_data in self.semantic_patterns.items():
            if base_command in pattern_data.elisp_template:
                if pattern_data.usage_count > 0:
                    docstring += (
                        f"\n\nUsage frequency: {pattern_data.usage_count} times"
                    )
                break

        return docstring

    def learn_new_pattern(self, natural_command: str, elisp_result: str, success: bool):
        """Learn new semantic patterns from successful command executions"""

        if not success:
            return

        # Simple pattern learning: extract key terms
        key_terms = re.findall(r"\b\w{3,}\b", natural_command.lower())
        pattern_candidate = "|".join(key_terms[:3])  # Use first 3 significant terms

        # Store as potential new pattern
        pattern_key = f"learned_{hash(natural_command) % 10000}"

        new_pattern = SemanticPattern(
            pattern=pattern_candidate,
            elisp_template=elisp_result,
            confidence=0.6,  # Start with medium confidence
            usage_count=1,
            last_used=time.time(),
        )

        # Store in Redis for persistence
        self.redis_client.hset(
            f"semantic:learned:{pattern_key}",
            mapping={
                "pattern": new_pattern.pattern,
                "elisp": new_pattern.elisp_template,
                "confidence": str(new_pattern.confidence),
                "usage_count": str(new_pattern.usage_count),
                "last_used": str(new_pattern.last_used),
                "natural_command": natural_command,
            },
        )

        print(f"✅ Learned new pattern: '{pattern_candidate}' → '{elisp_result}'")

    def get_coverage_stats(self) -> Dict[str, int]:
        """Get statistics about semantic coverage"""

        total_patterns = len(self.semantic_patterns)
        used_patterns = sum(
            1 for p in self.semantic_patterns.values() if p.usage_count > 0
        )
        learned_patterns = len(self.redis_client.keys("semantic:learned:*"))

        return {
            "total_builtin_patterns": total_patterns,
            "used_patterns": used_patterns,
            "learned_patterns": learned_patterns,
            "coverage_percentage": (
                int((used_patterns / total_patterns) * 100) if total_patterns > 0 else 0
            ),
        }


def main():
    """Test the enhanced semantic engine"""
    engine = EnhancedSemanticEngine()

    # Test various commands
    test_commands = [
        "commit my changes",
        "run the test suite",
        "search for TODO in project",
        "open recent files",
        "split window to the right",
        "go to definition",
        "format this code",
        "open a terminal",
        "save all my work",
        "check redis status",
    ]

    print("🧠 Enhanced Semantic Coverage Engine Test")
    print("=" * 50)

    for cmd in test_commands:
        result = engine.analyze_command(cmd)
        if result:
            elisp_cmd, confidence = result
            docstring = engine.synthesize_docstring(elisp_cmd, f"Command: {cmd}")

            print(f"\n📝 Natural: '{cmd}'")
            print(f"⚡ Elisp: {elisp_cmd}")
            print(f"🎯 Confidence: {confidence:.2f}")
            print(f"📖 Docstring: {docstring}")
        else:
            print(f"\n❓ No match for: '{cmd}'")

    # Show coverage stats
    stats = engine.get_coverage_stats()
    print(f"\n📊 Coverage Statistics:")
    print(f"   Built-in patterns: {stats['total_builtin_patterns']}")
    print(f"   Used patterns: {stats['used_patterns']}")
    print(f"   Learned patterns: {stats['learned_patterns']}")
    print(f"   Coverage: {stats['coverage_percentage']}%")


if __name__ == "__main__":
    main()
