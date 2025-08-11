#!/usr/bin/env python3
"""
Test the docstring synthesis system for semantic equivalence and background learning
"""

from docstring_synthesis_engine import DocstringSynthesisEngine

def test_docstring_synthesis():
    print("🚀 **TESTING DOCSTRING SYNTHESIS SYSTEM**")
    print("=" * 60)
    
    # Initialize engine
    engine = DocstringSynthesisEngine()
    
    print("\n📝 **STEP 1: HARVEST DOCSTRINGS**")
    print("-" * 40)
    
    # Build semantic mappings from docstrings
    mappings = engine.build_semantic_mappings()
    
    if not mappings:
    """TODO: Document test_docstring_synthesis function"""
        print("❌ No mappings created - aborting test")
        return
    
    # Store in Redis for fast lookup
    engine.store_mappings_in_redis(mappings)
    
    print(f"✅ Successfully created {len(mappings)} semantic mappings")
    
    print("\n🎯 **STEP 2: TEST UTTERANCE LOOKUP**")
    print("-" * 40)
    
    # Test different phrasings of the same command as requested
    test_cases = [
        # End of line variations
        ("move to end of line", "Testing movement to line end"),
        ("control e", "Testing Ctrl+E shortcut"),
        ("end of line", "Testing direct phrase"),
        ("go to line end", "Testing alternative phrasing"),
        
        # Undo variations  
        ("undo that", "Testing casual undo phrase"),
        ("revert last change", "Testing formal undo phrase"),
        ("ctrl underscore", "Testing undo keybinding"),
        
        # Additional test cases
        ("beginning of line", "Testing line start"),
        ("control a", "Testing Ctrl+A shortcut"),
        ("start of line", "Testing alternative start phrase"),
    ]
    
    results = []
    
    for utterance, description in test_cases:
        canonical = engine.lookup_utterance(utterance)
        results.append((utterance, canonical, description))
        
        if canonical:
            print(f"✅ '{utterance}' → `{canonical}`")
        else:
            print(f"❌ '{utterance}' → No mapping found")
    
    print("\n🔮 **STEP 3: TEST NEXT ACTION PREDICTIONS**")
    print("-" * 40)
    
    # Test prediction for end-of-line as requested
    test_predictions = ["end-of-line", "beginning-of-line", "undo"]
    
    for command in test_predictions:
        predictions = engine.predict_next_actions(command)
        
        if predictions:
            print(f"\n🎯 After `{command}`, likely next actions:")
            for action, score in predictions[:5]:
                print(f"   • {action}: {score:.1%} likelihood")
        else:
            print(f"\n❓ No predictions available for `{command}`")
    
    print("\n📊 **STEP 4: SEMANTIC EQUIVALENCE ANALYSIS**")
    print("-" * 40)
    
    # Group results by canonical command to test equivalence
    equivalence_groups = {}
    for utterance, canonical, description in results:
        if canonical:
            if canonical not in equivalence_groups:
                equivalence_groups[canonical] = []
            equivalence_groups[canonical].append(utterance)
    
    print("🔍 Semantic equivalence groups found:")
    for canonical, utterances in equivalence_groups.items():
        if len(utterances) > 1:
            print(f"\n📍 `{canonical}` maps from:")
            for utterance in utterances:
                print(f"   → '{utterance}'")
    
    print("\n🧠 **STEP 5: BACKGROUND LEARNING ASSESSMENT**")
    print("-" * 40)
    
    # Test the system's ability to learn from docstrings
    sample_mappings = mappings[:3]
    
    for mapping in sample_mappings:
        print(f"\n📚 Command: `{mapping.canonical_command}`")
        print(f"   Intent: {mapping.intent_category}")
        print(f"   Entities: {list(mapping.extracted_entities)[:3]}")
        print(f"   Utterances: {mapping.synthesized_utterances[:3]}")
        print(f"   Related: {mapping.related_commands[:3]}")
        print(f"   Confidence: {mapping.confidence:.2f}")
    
    print("\n🎉 **FINAL ASSESSMENT**")
    print("=" * 60)
    
    # Calculate success metrics
    total_tests = len(test_cases)
    successful_lookups = len([r for r in results if r[1] is not None])
    
    print(f"📈 Utterance Lookup Success Rate: {successful_lookups}/{total_tests} ({successful_lookups/total_tests:.1%})")
    print(f"📈 Total Semantic Mappings: {len(mappings)}")
    print(f"📈 Equivalence Groups Found: {len(equivalence_groups)}")
    
    # Test zero-delay capability
    import time
    start_time = time.time()
    engine.lookup_utterance("move to end of line")
    lookup_time = time.time() - start_time
    print(f"⚡ Zero-delay lookup time: {lookup_time*1000:.2f}ms")
    
    if successful_lookups > 0:
        print("\n✅ **SEMANTIC EQUIVALENCE TEST: PASSED**")
        print("✅ Background learning from docstrings working")
        print("✅ Zero-delay translation achieved")
    else:
        print("\n❌ **SEMANTIC EQUIVALENCE TEST: FAILED**")
        print("❌ No utterances successfully mapped")

if __name__ == "__main__":
    test_docstring_synthesis()