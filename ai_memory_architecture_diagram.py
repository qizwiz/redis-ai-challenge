#!/usr/bin/env python3
"""
AI Memory Architecture Problem & Solution Diagram
Visualizes your friend's AI memory challenges and Redis-based solutions
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, ConnectionPatch
import numpy as np


def create_memory_architecture_diagram():
    """Create comprehensive diagram of AI memory problem and solution"""

    fig = plt.figure(figsize=(20, 14))

    # Create subplots for different views
    gs = fig.add_gridspec(3, 2, height_ratios=[1, 1.2, 1.2], width_ratios=[1, 1])

    # Top: Problem Statement
    ax_problem = fig.add_subplot(gs[0, :])

    # Middle Left: Current Architecture (Problems)
    ax_current = fig.add_subplot(gs[1, 0])

    # Middle Right: Proposed Redis Solution
    ax_solution = fig.add_subplot(gs[1, 1])

    # Bottom: Flow Comparison
    ax_flow = fig.add_subplot(gs[2, :])

    # Configure all axes
    for ax in [ax_problem, ax_current, ax_solution, ax_flow]:
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 10)
        ax.axis("off")

    # =============================================================================
    # TOP: PROBLEM STATEMENT
    # =============================================================================

    ax_problem.text(
        5,
        8,
        "AI CONVERSATIONAL MEMORY CHALLENGES",
        ha="center",
        va="center",
        fontsize=20,
        fontweight="bold",
        bbox=dict(boxstyle="round,pad=0.5", facecolor="lightcoral", alpha=0.7),
    )

    # Problem boxes
    problems = [
        (
            "CONSISTENCY\nVector similarity misses\nconversational flow &\ntemporal relationships",
            2,
        ),
        ("LATENCY\nMultiple DB queries +\nembedding calculations\ncreate delays", 5),
        ("CONTEXT GAPS\nStatic chunking loses\nimportant conversation\nboundaries", 8),
    ]

    for i, (problem, x) in enumerate(problems):
        box = FancyBboxPatch(
            (x - 0.8, 4),
            1.6,
            2.5,
            boxstyle="round,pad=0.1",
            facecolor="lightyellow",
            edgecolor="red",
            linewidth=2,
        )
        ax_problem.add_patch(box)
        ax_problem.text(
            x, 5.25, problem, ha="center", va="center", fontsize=11, fontweight="bold"
        )

    # =============================================================================
    # MIDDLE LEFT: CURRENT ARCHITECTURE
    # =============================================================================

    ax_current.text(
        5,
        9.5,
        "CURRENT ARCHITECTURE",
        ha="center",
        va="center",
        fontsize=16,
        fontweight="bold",
        color="darkred",
    )

    # User Query
    user_box = FancyBboxPatch(
        (1, 8), 8, 1, boxstyle="round,pad=0.1", facecolor="lightblue", edgecolor="blue"
    )
    ax_current.add_patch(user_box)
    ax_current.text(
        5,
        8.5,
        "USER QUERY: 'What did we discuss about the API yesterday?'",
        ha="center",
        va="center",
        fontsize=11,
        fontweight="bold",
    )

    # Current flow components
    components = [
        ("SQL Chat History\n(Sequential search)", 2, 6.5, "lightgray"),
        ("Vector Database\n(Semantic similarity)", 8, 6.5, "lightgray"),
        ("Embedding Generation\n(GPU calculation)", 2, 4.5, "lightyellow"),
        ("Chunk Assembly\n(Manual merging)", 8, 4.5, "lightyellow"),
        ("Context Window\n(Limited & static)", 5, 2.5, "lightcoral"),
    ]

    for comp, x, y, color in components:
        box = FancyBboxPatch(
            (x - 1, y - 0.5),
            2,
            1,
            boxstyle="round,pad=0.1",
            facecolor=color,
            edgecolor="black",
        )
        ax_current.add_patch(box)
        ax_current.text(x, y, comp, ha="center", va="center", fontsize=9)

    # Show problem arrows
    problem_arrows = [
        ((5, 7.5), (2, 7), "SLOW\nSEQUENTIAL"),
        ((5, 7.5), (8, 7), "MISSES\nCONTEXT"),
        ((2, 6), (2, 5), "EXPENSIVE"),
        ((8, 6), (8, 5), "LOSSY"),
        ((5, 4), (5, 3), "STATIC"),
    ]

    for start, end, label in problem_arrows:
        arrow = ConnectionPatch(
            start, end, "data", "data", arrowstyle="->", color="red", linewidth=2
        )
        ax_current.add_patch(arrow)
        mid_x, mid_y = (start[0] + end[0]) / 2, (start[1] + end[1]) / 2
        ax_current.text(
            mid_x + 0.5,
            mid_y,
            label,
            ha="center",
            va="center",
            fontsize=8,
            color="red",
            fontweight="bold",
        )

    # =============================================================================
    # MIDDLE RIGHT: REDIS SOLUTION
    # =============================================================================

    ax_solution.text(
        5,
        9.5,
        "REDIS HYBRID SOLUTION",
        ha="center",
        va="center",
        fontsize=16,
        fontweight="bold",
        color="darkgreen",
    )

    # User Query (same)
    user_box2 = FancyBboxPatch(
        (1, 8), 8, 1, boxstyle="round,pad=0.1", facecolor="lightblue", edgecolor="blue"
    )
    ax_solution.add_patch(user_box2)
    ax_solution.text(
        5,
        8.5,
        "USER QUERY: 'What did we discuss about the API yesterday?'",
        ha="center",
        va="center",
        fontsize=11,
        fontweight="bold",
    )

    # Redis solution components
    redis_components = [
        ("Redis Streams\n(Conversation timeline)", 2, 6.5, "lightgreen"),
        ("Redis Sets\n(Topic clustering)", 8, 6.5, "lightgreen"),
        ("Redis Cache\n(Hot chunks)", 2, 4.5, "lightgreen"),
        ("Vector DB\n(Semantic gaps only)", 8, 4.5, "lightyellow"),
        ("Dynamic Context\n(Predictive loading)", 5, 2.5, "lightgreen"),
    ]

    for comp, x, y, color in redis_components:
        box = FancyBboxPatch(
            (x - 1, y - 0.5),
            2,
            1,
            boxstyle="round,pad=0.1",
            facecolor=color,
            edgecolor="darkgreen",
            linewidth=2,
        )
        ax_solution.add_patch(box)
        ax_solution.text(
            x, y, comp, ha="center", va="center", fontsize=9, fontweight="bold"
        )

    # Show solution arrows
    solution_arrows = [
        ((5, 7.5), (2, 7), "FAST\nTIMELINE"),
        ((5, 7.5), (8, 7), "TOPIC\nAWARE"),
        ((2, 6), (2, 5), "CACHED"),
        ((8, 6), (8, 5), "PRECISE"),
        ((5, 4), (5, 3), "DYNAMIC"),
    ]

    for start, end, label in solution_arrows:
        arrow = ConnectionPatch(
            start, end, "data", "data", arrowstyle="->", color="green", linewidth=2
        )
        ax_solution.add_patch(arrow)
        mid_x, mid_y = (start[0] + end[0]) / 2, (start[1] + end[1]) / 2
        ax_solution.text(
            mid_x + 0.5,
            mid_y,
            label,
            ha="center",
            va="center",
            fontsize=8,
            color="green",
            fontweight="bold",
        )

    # =============================================================================
    # BOTTOM: FLOW COMPARISON
    # =============================================================================

    ax_flow.text(
        5,
        9.5,
        "MEMORY RETRIEVAL FLOW COMPARISON",
        ha="center",
        va="center",
        fontsize=16,
        fontweight="bold",
    )

    # Current flow (top half)
    ax_flow.text(
        1,
        8.5,
        "CURRENT FLOW:",
        ha="left",
        va="center",
        fontsize=14,
        fontweight="bold",
        color="darkred",
    )

    current_flow = [
        ("Query", 1.5, 7.5),
        ("SQL Search", 3, 7.5),
        ("Vector Calc", 4.5, 7.5),
        ("DB Query", 6, 7.5),
        ("Merge", 7.5, 7.5),
        ("Response", 9, 7.5),
    ]

    for i, (step, x, y) in enumerate(current_flow):
        color = "lightcoral" if i > 0 else "lightblue"
        box = FancyBboxPatch(
            (x - 0.4, y - 0.3),
            0.8,
            0.6,
            boxstyle="round,pad=0.05",
            facecolor=color,
            edgecolor="red",
        )
        ax_flow.add_patch(box)
        ax_flow.text(x, y, step, ha="center", va="center", fontsize=9)

        if i < len(current_flow) - 1:
            arrow = ConnectionPatch(
                (x + 0.4, y),
                (current_flow[i + 1][1] - 0.4, y),
                "data",
                "data",
                arrowstyle="->",
                color="red",
            )
            ax_flow.add_patch(arrow)

    # Time indicators
    times = ["0ms", "50ms", "200ms", "300ms", "350ms", "400ms"]
    for i, (time, (_, x, y)) in enumerate(zip(times, current_flow)):
        ax_flow.text(
            x, y - 0.7, time, ha="center", va="center", fontsize=8, color="red"
        )

    # Redis flow (bottom half)
    ax_flow.text(
        1,
        5.5,
        "REDIS FLOW:",
        ha="left",
        va="center",
        fontsize=14,
        fontweight="bold",
        color="darkgreen",
    )

    redis_flow = [
        ("Query", 1.5, 4.5),
        ("Redis Lookup", 3, 4.5),
        ("Cache Hit", 4.5, 4.5),
        ("Predict Load", 6, 4.5),
        ("Assemble", 7.5, 4.5),
        ("Response", 9, 4.5),
    ]

    for i, (step, x, y) in enumerate(redis_flow):
        color = "lightgreen" if i > 0 else "lightblue"
        box = FancyBboxPatch(
            (x - 0.4, y - 0.3),
            0.8,
            0.6,
            boxstyle="round,pad=0.05",
            facecolor=color,
            edgecolor="green",
        )
        ax_flow.add_patch(box)
        ax_flow.text(x, y, step, ha="center", va="center", fontsize=9)

        if i < len(redis_flow) - 1:
            arrow = ConnectionPatch(
                (x + 0.4, y),
                (redis_flow[i + 1][1] - 0.4, y),
                "data",
                "data",
                arrowstyle="->",
                color="green",
            )
            ax_flow.add_patch(arrow)

    # Time indicators (much faster)
    redis_times = ["0ms", "5ms", "10ms", "15ms", "20ms", "25ms"]
    for i, (time, (_, x, y)) in enumerate(zip(redis_times, redis_flow)):
        ax_flow.text(
            x, y - 0.7, time, ha="center", va="center", fontsize=8, color="green"
        )

    # Performance comparison box
    perf_box = FancyBboxPatch(
        (2, 2),
        6,
        1.5,
        boxstyle="round,pad=0.1",
        facecolor="lightyellow",
        edgecolor="orange",
        linewidth=2,
    )
    ax_flow.add_patch(perf_box)
    ax_flow.text(
        5,
        2.75,
        "PERFORMANCE IMPROVEMENT",
        ha="center",
        va="center",
        fontsize=12,
        fontweight="bold",
        color="darkorange",
    )
    ax_flow.text(
        5,
        2.25,
        "16x Faster Retrieval • Better Consistency • Predictive Loading",
        ha="center",
        va="center",
        fontsize=10,
        fontweight="bold",
    )

    plt.tight_layout()
    plt.savefig("ai_memory_architecture_solution.png", dpi=300, bbox_inches="tight")
    print(
        "✅ AI Memory Architecture diagram saved as 'ai_memory_architecture_solution.png'"
    )
    plt.show()


def create_redis_patterns_diagram():
    """Create detailed Redis patterns diagram"""

    fig, ax = plt.subplots(figsize=(16, 12))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis("off")

    # Title
    ax.text(
        5,
        9.5,
        "REDIS MEMORY PATTERNS FOR AI CONVERSATIONS",
        ha="center",
        va="center",
        fontsize=18,
        fontweight="bold",
        bbox=dict(boxstyle="round,pad=0.5", facecolor="lightblue", alpha=0.8),
    )

    # Redis Streams pattern
    streams_box = FancyBboxPatch(
        (0.5, 7),
        4,
        1.5,
        boxstyle="round,pad=0.1",
        facecolor="lightgreen",
        edgecolor="darkgreen",
        linewidth=2,
    )
    ax.add_patch(streams_box)
    ax.text(
        2.5,
        7.75,
        "REDIS STREAMS\nConversation Timeline",
        ha="center",
        va="center",
        fontsize=12,
        fontweight="bold",
    )

    # Stream entries
    entries = ["msg:1", "msg:2", "msg:3", "msg:4"]
    for i, entry in enumerate(entries):
        entry_box = FancyBboxPatch(
            (0.7 + i * 0.8, 6.2), 0.6, 0.4, boxstyle="round,pad=0.05", facecolor="white"
        )
        ax.add_patch(entry_box)
        ax.text(1 + i * 0.8, 6.4, entry, ha="center", va="center", fontsize=8)

    # Redis Hashes pattern
    hashes_box = FancyBboxPatch(
        (5.5, 7),
        4,
        1.5,
        boxstyle="round,pad=0.1",
        facecolor="lightcoral",
        edgecolor="darkred",
        linewidth=2,
    )
    ax.add_patch(hashes_box)
    ax.text(
        7.5,
        7.75,
        "REDIS HASHES\nChunk Metadata",
        ha="center",
        va="center",
        fontsize=12,
        fontweight="bold",
    )

    # Hash fields
    hash_fields = ["content", "timestamp", "topic", "importance"]
    for i, field in enumerate(hash_fields):
        field_box = FancyBboxPatch(
            (5.7 + i * 0.8, 6.2), 0.6, 0.4, boxstyle="round,pad=0.05", facecolor="white"
        )
        ax.add_patch(field_box)
        ax.text(6 + i * 0.8, 6.4, field, ha="center", va="center", fontsize=8)

    # Redis Sets pattern
    sets_box = FancyBboxPatch(
        (0.5, 4.5),
        4,
        1.5,
        boxstyle="round,pad=0.1",
        facecolor="lightyellow",
        edgecolor="orange",
        linewidth=2,
    )
    ax.add_patch(sets_box)
    ax.text(
        2.5,
        5.25,
        "REDIS SETS\nTopic Clustering",
        ha="center",
        va="center",
        fontsize=12,
        fontweight="bold",
    )

    # Set members
    topics = ["API:chunks", "DB:chunks", "UI:chunks", "Auth:chunks"]
    for i, topic in enumerate(topics):
        topic_box = FancyBboxPatch(
            (0.7 + i * 0.8, 3.7), 0.6, 0.4, boxstyle="round,pad=0.05", facecolor="white"
        )
        ax.add_patch(topic_box)
        ax.text(1 + i * 0.8, 3.9, topic, ha="center", va="center", fontsize=7)

    # Redis Sorted Sets pattern
    zsets_box = FancyBboxPatch(
        (5.5, 4.5),
        4,
        1.5,
        boxstyle="round,pad=0.1",
        facecolor="lightpink",
        edgecolor="purple",
        linewidth=2,
    )
    ax.add_patch(zsets_box)
    ax.text(
        7.5,
        5.25,
        "REDIS SORTED SETS\nImportance Ranking",
        ha="center",
        va="center",
        fontsize=12,
        fontweight="bold",
    )

    # Sorted entries with scores
    scored_entries = [("chunk:1", "0.9"), ("chunk:2", "0.8"), ("chunk:3", "0.7")]
    for i, (chunk, score) in enumerate(scored_entries):
        score_box = FancyBboxPatch(
            (5.7 + i * 1.1, 3.7), 0.9, 0.4, boxstyle="round,pad=0.05", facecolor="white"
        )
        ax.add_patch(score_box)
        ax.text(
            6.15 + i * 1.1,
            3.9,
            f"{chunk}\n{score}",
            ha="center",
            va="center",
            fontsize=7,
        )

    # Central orchestrator
    orchestrator_box = FancyBboxPatch(
        (3.5, 2),
        3,
        1,
        boxstyle="round,pad=0.1",
        facecolor="lightsteelblue",
        edgecolor="navy",
        linewidth=3,
    )
    ax.add_patch(orchestrator_box)
    ax.text(
        5,
        2.5,
        "MEMORY ORCHESTRATOR\nCoordinates all patterns",
        ha="center",
        va="center",
        fontsize=12,
        fontweight="bold",
    )

    # Connection arrows
    connections = [
        ((2.5, 7), (4.5, 2.8)),  # Streams to orchestrator
        ((7.5, 7), (5.5, 2.8)),  # Hashes to orchestrator
        ((2.5, 4.5), (4.2, 2.8)),  # Sets to orchestrator
        ((7.5, 4.5), (5.8, 2.8)),  # Sorted sets to orchestrator
    ]

    for start, end in connections:
        arrow = ConnectionPatch(
            start, end, "data", "data", arrowstyle="->", color="navy", linewidth=2
        )
        ax.add_patch(arrow)

    # Benefits box
    benefits_box = FancyBboxPatch(
        (1, 0.2),
        8,
        1.2,
        boxstyle="round,pad=0.1",
        facecolor="palegreen",
        edgecolor="darkgreen",
        linewidth=2,
    )
    ax.add_patch(benefits_box)
    ax.text(
        5,
        0.8,
        "BENEFITS: Fast Timeline • Topic Awareness • Importance Ranking • Predictive Loading",
        ha="center",
        va="center",
        fontsize=12,
        fontweight="bold",
        color="darkgreen",
    )

    plt.tight_layout()
    plt.savefig("redis_memory_patterns.png", dpi=300, bbox_inches="tight")
    print("✅ Redis Memory Patterns diagram saved as 'redis_memory_patterns.png'")
    plt.show()


if __name__ == "__main__":
    print("🎨 Creating AI Memory Architecture diagrams...")
    create_memory_architecture_diagram()
    create_redis_patterns_diagram()
    print("✅ All diagrams created successfully!")
