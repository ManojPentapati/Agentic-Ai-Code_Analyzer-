"""
State schema for the Agentic AI Code Analyzer.

Defines the rich state that flows through the LangGraph workflow,
carrying all analysis data between specialized agent nodes.
"""

from typing import TypedDict, Annotated, Literal
from operator import add
from langchain_core.messages import BaseMessage


class AnalysisMetadata(TypedDict, total=False):
    """Metadata collected during analysis."""

    timestamp: str
    model_name: str
    analysis_duration_sec: float
    total_nodes_executed: int


class AnalyzerState(TypedDict, total=False):
    """
    Rich state schema for the multi-agent code analyzer workflow.

    Flows through the LangGraph and gets progressively enriched
    by each agent node.
    """

    # ── Input ────────────────────────────────
    query: str                      # Original user code snippet
    language: str                   # Auto-detected programming language
    complexity_score: int           # Code complexity score (0–100)

    # ── Routing ──────────────────────────────
    analysis_type: Literal[
        "quick",                    # Simple code → fast review only
        "deep",                     # Complex code → review + optimization
        "security_focused",         # Risky code → review + security + optimization
    ]

    # ── Agent Outputs ────────────────────────
    code_review: str                # Output from the Code Review Agent
    security_report: str            # Output from the Security Agent
    optimization_report: str        # Output from the Optimization Agent
    lint_report: str                # Output from Ruff Linter (if python)
    final_report: str               # Aggregated final analysis

    # ── Message History ──────────────────────
    messages: Annotated[list[BaseMessage], add]

    # ── Metadata ─────────────────────────────
    metadata: AnalysisMetadata


# ── Default State Factory ────────────────────

def create_initial_state(query: str) -> AnalyzerState:
    """
    Create a fresh initial state for a new analysis run.

    Args:
        query: The user's code snippet to analyze.

    Returns:
        Initialized AnalyzerState with defaults.
    """
    return AnalyzerState(
        query=query,
        language="unknown",
        complexity_score=0,
        analysis_type="quick",
        code_review="",
        security_report="",
        optimization_report="",
        lint_report="",
        final_report="",
        messages=[],
        metadata=AnalysisMetadata(),
    )
