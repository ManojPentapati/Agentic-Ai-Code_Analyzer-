"""
LangGraph workflow for the Agentic AI Code Analyzer.

Builds a multi-agent graph with conditional routing:

    START
      → preprocess (detect language, compute complexity, scan security)
      → router (decide analysis path)
      → CONDITIONAL:
          ├── "quick"            → code_review → aggregate → END
          ├── "deep"             → code_review → optimize  → aggregate → END
          └── "security_focused" → code_review → security  → optimize  → aggregate → END
      → END
"""

import time
import logging
from datetime import datetime, timezone

from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, START, END

from state import AnalyzerState
from tools import detect_language, calculate_complexity, scan_security_patterns, check_code_patterns
from agents import (
    create_router_chain,
    create_code_review_chain,
    create_security_chain,
    create_optimization_chain,
    create_aggregator_chain,
)
from config import get_llm, AppConfig, logger


# ──────────────────────────────────────────────
# Node Functions
# ──────────────────────────────────────────────

def preprocess_node(state: AnalyzerState) -> dict:
    """
    Preprocessing node: runs all tools to gather structured data
    about the code before sending it to LLM agents.
    """
    logger.info("📥 Preprocessing: running analysis tools")
    code = state["query"]

    # Run tools
    language = detect_language.invoke({"code": code})
    complexity = calculate_complexity.invoke({"code": code})
    security = scan_security_patterns.invoke({"code": code})
    patterns = check_code_patterns.invoke({"code": code})

    # Extract complexity score from the tool output
    score = 0
    for line in complexity.split("\n"):
        if line.startswith("Complexity Score:"):
            try:
                score = int(line.split(":")[1].strip().split("/")[0])
            except (ValueError, IndexError):
                score = 0
            break

    # Build context message for downstream agents
    context = (
        f"## Tool Analysis Results\n\n"
        f"**Language Detected:** {language}\n\n"
        f"### Complexity Report\n```\n{complexity}\n```\n\n"
        f"### Security Scan\n{security}\n\n"
        f"### Code Patterns\n{patterns}\n\n"
        f"---\n\n"
        f"**Code to analyze:**\n```{language}\n{code}\n```"
    )

    return {
        "language": language,
        "complexity_score": score,
        "messages": [HumanMessage(content=context)],
        "metadata": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    }


def router_node(state: AnalyzerState) -> dict:
    """
    Router node: uses the LLM to decide which analysis path to take
    based on the preprocessed data.
    """
    logger.info("🔀 Router: deciding analysis path")

    config = state.get("_config", AppConfig())
    llm = get_llm(config)
    router_chain = create_router_chain(llm)

    response = router_chain.invoke({"messages": state["messages"]})
    decision = response.content.strip().lower()

    # Validate the decision
    valid_types = {"quick", "deep", "security_focused"}
    if decision not in valid_types:
        # Fallback heuristic
        security_text = ""
        for msg in state["messages"]:
            if hasattr(msg, "content"):
                security_text += msg.content

        if "CRITICAL" in security_text or "HIGH" in security_text:
            decision = "security_focused"
        elif state.get("complexity_score", 0) >= 40:
            decision = "deep"
        else:
            decision = "quick"

    logger.info("🔀 Router decision: %s", decision)

    return {
        "analysis_type": decision,
    }


def code_review_node(state: AnalyzerState) -> dict:
    """Code Review agent: performs thorough code review."""
    logger.info("🔍 Code Review Agent: analyzing code")

    config = state.get("_config", AppConfig())
    llm = get_llm(config)
    chain = create_code_review_chain(llm)

    response = chain.invoke({"messages": state["messages"]})
    review = response.content

    logger.info("🔍 Code Review Agent: complete (%d chars)", len(review))

    return {
        "code_review": review,
        "messages": [AIMessage(content=f"[Code Review]\n{review}")],
    }


def security_node(state: AnalyzerState) -> dict:
    """Security agent: analyzes code for vulnerabilities."""
    logger.info("🔒 Security Agent: scanning for vulnerabilities")

    config = state.get("_config", AppConfig())
    llm = get_llm(config)
    chain = create_security_chain(llm)

    # Include the code review context for the security agent
    messages = state["messages"]
    response = chain.invoke({"messages": messages})
    report = response.content

    logger.info("🔒 Security Agent: complete (%d chars)", len(report))

    return {
        "security_report": report,
        "messages": [AIMessage(content=f"[Security Analysis]\n{report}")],
    }


def optimization_node(state: AnalyzerState) -> dict:
    """Optimization agent: suggests performance improvements."""
    logger.info("⚡ Optimization Agent: analyzing performance")

    config = state.get("_config", AppConfig())
    llm = get_llm(config)
    chain = create_optimization_chain(llm)

    messages = state["messages"]
    response = chain.invoke({"messages": messages})
    report = response.content

    logger.info("⚡ Optimization Agent: complete (%d chars)", len(report))

    return {
        "optimization_report": report,
        "messages": [AIMessage(content=f"[Optimization Analysis]\n{report}")],
    }


def aggregate_node(state: AnalyzerState) -> dict:
    """
    Aggregator node: combines all specialist reports into a
    final comprehensive analysis report.
    """
    logger.info("📊 Aggregator: combining reports")

    config = state.get("_config", AppConfig())
    llm = get_llm(config)
    chain = create_aggregator_chain(llm)

    # Build aggregation prompt from available reports
    parts = []
    parts.append(f"**Language:** {state.get('language', 'unknown')}")
    parts.append(f"**Complexity Score:** {state.get('complexity_score', 0)}/100")
    parts.append(f"**Analysis Type:** {state.get('analysis_type', 'quick')}")
    parts.append("")

    if state.get("code_review"):
        parts.append("---\n### Code Review Report\n" + state["code_review"])
    if state.get("security_report"):
        parts.append("---\n### Security Report\n" + state["security_report"])
    if state.get("optimization_report"):
        parts.append("---\n### Optimization Report\n" + state["optimization_report"])

    aggregation_msg = HumanMessage(content="\n\n".join(parts))

    response = chain.invoke({"messages": [aggregation_msg]})
    final_report = response.content

    logger.info("📊 Aggregator: final report generated (%d chars)", len(final_report))

    return {
        "final_report": final_report,
        "messages": [AIMessage(content=final_report)],
    }


# ──────────────────────────────────────────────
# Routing Logic
# ──────────────────────────────────────────────

def route_analysis(state: AnalyzerState) -> str:
    """
    Conditional edge function: returns the next node name
    based on the router's decision.
    """
    analysis_type = state.get("analysis_type", "quick")

    routing_map = {
        "quick": "code_review",
        "deep": "code_review",
        "security_focused": "code_review",
    }

    return routing_map.get(analysis_type, "code_review")


def route_after_review(state: AnalyzerState) -> str:
    """
    After code review, decide whether to continue to
    security, optimization, or go straight to aggregation.
    """
    analysis_type = state.get("analysis_type", "quick")

    if analysis_type == "quick":
        return "aggregate"
    elif analysis_type == "deep":
        return "optimize"
    elif analysis_type == "security_focused":
        return "security"

    return "aggregate"


def route_after_security(state: AnalyzerState) -> str:
    """After security analysis, always proceed to optimization."""
    return "optimize"


def route_after_optimization(state: AnalyzerState) -> str:
    """After optimization, always proceed to aggregation."""
    return "aggregate"


# ──────────────────────────────────────────────
# Graph Builder
# ──────────────────────────────────────────────

def build_workflow():
    """
    Build and compile the multi-agent LangGraph workflow.

    Returns:
        Compiled LangGraph workflow.
    """
    logger.info("🏗️  Building multi-agent workflow graph")

    graph = StateGraph(AnalyzerState)

    # Add nodes
    graph.add_node("preprocess", preprocess_node)
    graph.add_node("router", router_node)
    graph.add_node("code_review", code_review_node)
    graph.add_node("security", security_node)
    graph.add_node("optimize", optimization_node)
    graph.add_node("aggregate", aggregate_node)

    # Linear edges: START → preprocess → router
    graph.add_edge(START, "preprocess")
    graph.add_edge("preprocess", "router")

    # Conditional: router → code_review (always, but sets up the path)
    graph.add_conditional_edges(
        "router",
        route_analysis,
        {
            "code_review": "code_review",
        },
    )

    # Conditional: code_review → aggregate | optimize | security
    graph.add_conditional_edges(
        "code_review",
        route_after_review,
        {
            "aggregate": "aggregate",
            "optimize": "optimize",
            "security": "security",
        },
    )

    # Conditional: security → optimize
    graph.add_conditional_edges(
        "security",
        route_after_security,
        {
            "optimize": "optimize",
        },
    )

    # Conditional: optimize → aggregate
    graph.add_conditional_edges(
        "optimize",
        route_after_optimization,
        {
            "aggregate": "aggregate",
        },
    )

    # Final edge: aggregate → END
    graph.add_edge("aggregate", END)

    workflow = graph.compile()
    logger.info("✅ Workflow graph compiled successfully")

    return workflow
