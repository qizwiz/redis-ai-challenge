#!/usr/bin/env python3
"""
Test with real Emacs docstrings using a simpler approach
"""

import subprocess
import json
from docstring_synthesis_engine import DocstringSynthesisEngine


def harvest_simple_emacs_docstrings():
    """Harvest some basic Emacs docstrings with a simpler approach"""

    # Simple commands we know exist
    commands = [
        "end-of-line",
        "beginning-of-line",
        "forward-char",
        "backward-char",
        "undo",
        "yank",
        "kill-line",
        "goto-line",
        "search-forward",
    ]

    docstrings = {}

    for command in commands:
        try:
            # Get docstring for individual command
            elisp = f"(documentation (quote {command}))"
            result = subprocess.run(
                ["emacsclient", "--eval", elisp],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                docstring = result.stdout.strip().strip('"')
                if docstring and docstring != "nil" and len(docstring) > 10:
                    # Clean up escaped quotes
                    docstring = docstring.replace('\\"', '"').replace("\\n", "\n")
                    docstrings[command] = docstring
                    print(f"✅ {command}: {docstring[:50]}...")

        except Exception as e:
            print(f"❌ Failed to get docstring for {command}: {e}")

    return docstrings


def test_real_emacs_docstrings():
    print("🚀 **TESTING WITH REAL EMACS DOCSTRINGS**")
    print("=" * 60)

    # Harvest real docstrings
    print("\n📝 **HARVESTING REAL EMACS DOCSTRINGS**")
    print("-" * 40)

    real_docstrings = harvest_simple_emacs_docstrings()

    if not real_docstrings:
        print("❌ No real docstrings harvested")
        return

    # Initialize engine
    engine = DocstringSynthesisEngine()

    # Build mappings from real docstrings
    mappings = []

    for command, docstring in real_docstrings.items():
        utterances = engine.synthesize_utterances_from_docstring(command, docstring)
        entities = engine.extract_entities_from_docstring(docstring)
        intent = engine.classify_intent(command, docstring)
        related = engine.find_related_commands(command, docstring, real_docstrings)
        confidence = min(len(utterances) * 0.1 + len(docstring) * 0.001, 1.0)

        from docstring_synthesis_engine import SemanticMapping

        mapping = SemanticMapping(
            canonical_command=command,
            docstring=docstring,
            synthesized_utterances=utterances,
            extracted_entities=entities,
            intent_category=intent,
            related_commands=related,
            confidence=confidence,
        )

        mappings.append(mapping)

    # Store in Redis
    engine.store_mappings_in_redis(mappings)

    print(f"\n✅ Created {len(mappings)} mappings from real Emacs docstrings")

    print("\n🎯 **TESTING REAL DOCSTRING UTTERANCES**")
    print("-" * 40)

    # Test the same utterances as requested
    test_utterances = [
        "move to end of line",
        "control e",
        "end of line",
        "go to line end",
        "undo that",
        "revert last change",
        "ctrl underscore",
    ]

    for utterance in test_utterances:
        canonical = engine.lookup_utterance(utterance)
        if canonical:
            print(f"✅ '{utterance}' → `{canonical}`")
        else:
            print(f"❌ '{utterance}' → No mapping found")

    print("\n🔮 **REAL DOCSTRING PREDICTIONS**")
    print("-" * 40)

    predictions = engine.predict_next_actions("end-of-line")
    if predictions:
        print("After 'end-of-line', likely next actions:")
        for action, score in predictions[:3]:
            print(f"  • {action}: {score:.1%}")

    print("\n📚 **SAMPLE REAL MAPPINGS**")
    print("-" * 40)

    for mapping in mappings[:3]:
        print(f"\n🎯 Command: `{mapping.canonical_command}`")
        print(f"   Real docstring: {mapping.docstring[:100]}...")
        print(f"   Generated utterances: {mapping.synthesized_utterances[:3]}")
        print(f"   Intent: {mapping.intent_category}")
        print(f"   Entities: {list(mapping.extracted_entities)[:3]}")


if __name__ == "__main__":
    test_real_emacs_docstrings()
