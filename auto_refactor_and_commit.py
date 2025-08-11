#!/usr/bin/env python3
"""
Auto Refactor and Commit - Actually execute intelligent refactoring

This will automatically refactor the codebase and commit changes.
"""

from intelligent_refactoring_agent import IntelligentRefactoringAgent
import redis


def auto_refactor_codebase():
    """Automatically refactor codebase and commit"""

    print("🤖 AUTO REFACTORING AGENT")
    print("=" * 40)
    print("Executing intelligent refactoring automatically...")
    print()

    # Initialize agent
    redis_client = redis.Redis(host="localhost", port=6379, decode_responses=True)
    agent = IntelligentRefactoringAgent(redis_client)

    # Analyze codebase
    opportunities = agent.analyze_codebase_for_refactoring()

    if not opportunities:
        print("✅ No refactoring opportunities found")
        return

    print(f"🎯 Found {len(opportunities)} refactoring opportunities")

    # Filter to safer opportunities only for automatic execution
    safe_opportunities = []
    for opp in opportunities:
        if opp.opportunity_type == "unused_import" and opp.confidence > 0.8:
            safe_opportunities.append(opp)
        elif (
            opp.opportunity_type == "dead_code"
            and opp.confidence > 0.7
            and opp.estimated_savings < 20
        ):
            safe_opportunities.append(opp)

    print(
        f"🛡️  Selected {len(safe_opportunities)} safe opportunities for automatic refactoring"
    )

    if not safe_opportunities:
        print("⚠️  No safe opportunities found for automatic execution")
        return

    # Show what will be changed
    by_type = {}
    for opp in safe_opportunities:
        if opp.opportunity_type not in by_type:
            by_type[opp.opportunity_type] = []
        by_type[opp.opportunity_type].append(opp)

    for opp_type, opps in by_type.items():
        print(f"\n{opp_type.replace('_', ' ').title()}: {len(opps)} changes")
        for opp in opps[:3]:  # Show first 3
            print(f"   • {opp.description}")

    # Execute refactoring
    print(f"\n🔧 Executing {len(safe_opportunities)} safe refactoring changes...")
    results = agent.execute_refactoring(safe_opportunities)

    if not results["success"]:
        print("❌ Refactoring failed:")
        for error in results["errors"]:
            print(f"   • {error}")
        return

    if not results["changes_made"]:
        print("ℹ️  No changes were made")
        return

    # Show results
    print("\n✅ REFACTORING COMPLETED:")
    print(f"   📁 Files modified: {len(results['files_modified'])}")
    print(f"   📝 Changes made: {len(results['changes_made'])}")
    print(f"   🗑️  Lines removed: {results['lines_removed']}")

    # Commit changes
    print("\n📤 Committing changes to git...")
    commit_success = agent.commit_refactoring_changes(results)

    if commit_success:
        print("🎉 Intelligent refactoring completed and committed!")
        print("\n📋 Changes committed:")
        for change in results["changes_made"]:
            print(f"   • {change}")

        return True
    else:
        print("⚠️  Refactoring completed but not committed")
        return False


if __name__ == "__main__":
    success = auto_refactor_codebase()
    if success:
        print("\n🚀 The AI agent successfully refactored and committed changes!")
    else:
        print("\n❌ Refactoring was not completed")
