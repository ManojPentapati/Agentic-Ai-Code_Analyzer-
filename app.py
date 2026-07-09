"""
Streamlit UI for the Agentic AI Code Analyzer.

Premium, tabbed interface with sidebar configuration, analysis metrics,
and exportable reports.
"""

import time
import re
import streamlit as st

from config import AppConfig, AVAILABLE_MODELS, DEFAULT_MODEL, logger
from state import create_initial_state
from graph import build_workflow
from tools import scan_security_patterns, calculate_complexity, detect_language, check_code_patterns

# ──────────────────────────────────────────────
# Page Configuration
# ──────────────────────────────────────────────

st.set_page_config(
    page_title="Agentic AI Code Analyzer",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────
# CSS Styles & Animations (Glassmorphism & Neon)
# ──────────────────────────────────────────────

st.markdown("""
<style>
    /* ── Global Styles & Custom Fonts ──────────────────────── */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;700&display=swap');

    .stApp {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
        background-color: #0d0e15;
        color: #f1f3f9;
    }

    /* ── Glassmorphism Panels ──────────────────────── */
    .glass-card {
        background: rgba(22, 24, 37, 0.7);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
    }

    .main-header {
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 50%, #db2777 100%);
        padding: 2.5rem;
        border-radius: 20px;
        margin-bottom: 2rem;
        color: white;
        box-shadow: 0 12px 40px rgba(79, 70, 229, 0.3);
        position: relative;
        overflow: hidden;
    }

    .main-header::after {
        content: '';
        position: absolute;
        top: 0; right: 0; bottom: 0; left: 0;
        background: radial-gradient(circle at 80% 20%, rgba(255,255,255,0.1) 0%, transparent 50%);
    }

    .main-header h1 {
        margin: 0;
        font-size: 2.5rem;
        font-weight: 800;
        letter-spacing: -1px;
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    .main-header p {
        margin: 0.75rem 0 0;
        opacity: 0.9;
        font-size: 1.15rem;
        font-weight: 300;
        max-width: 800px;
    }

    /* ── Dashboard Stats ──────────────────────── */
    .dashboard-stat-card {
        background: rgba(30, 32, 50, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.03);
        border-radius: 12px;
        padding: 1.25rem;
        text-align: center;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
    }

    .dashboard-stat-card:hover {
        transform: translateY(-4px);
        border-color: rgba(124, 58, 237, 0.3);
        box-shadow: 0 10px 25px rgba(124, 58, 237, 0.15);
    }

    .dashboard-stat-value {
        font-size: 2rem;
        font-weight: 800;
        margin: 0.25rem 0;
        background: linear-gradient(135deg, #a78bfa 0%, #ec4899 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .dashboard-stat-label {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        color: #9ca3af;
        font-weight: 600;
    }

    /* ── Dynamic Pipeline Flow ──────────────────────── */
    .pipeline-wrapper {
        display: flex;
        align-items: center;
        justify-content: center;
        flex-wrap: wrap;
        gap: 0.75rem;
        margin: 1.5rem 0;
        padding: 1rem;
        background: rgba(17, 19, 31, 0.5);
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.02);
    }

    .pipeline-node {
        padding: 0.5rem 1.25rem;
        border-radius: 30px;
        font-size: 0.85rem;
        font-weight: 600;
        transition: all 0.3s ease;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .node-completed {
        background: rgba(16, 185, 129, 0.1);
        color: #34d399;
        border: 1px solid rgba(16, 185, 129, 0.3);
    }

    .node-active {
        background: rgba(124, 58, 237, 0.2);
        color: #c084fc;
        border: 1px solid rgba(124, 58, 237, 0.6);
        box-shadow: 0 0 15px rgba(124, 58, 237, 0.3);
        animation: pulse-glow 2s infinite alternate;
    }

    .node-skipped {
        background: rgba(55, 65, 81, 0.2);
        color: #6b7280;
        border: 1px dashed rgba(55, 65, 81, 0.4);
    }

    @keyframes pulse-glow {
        from { box-shadow: 0 0 5px rgba(124, 58, 237, 0.2); }
        to { box-shadow: 0 0 20px rgba(124, 58, 237, 0.5); }
    }

    /* ── Progress Indicators & Scorecard ──────────────────────── */
    .progress-bar-container {
        margin-bottom: 1.25rem;
    }

    .progress-bar-header {
        display: flex;
        justify-content: space-between;
        font-size: 0.85rem;
        margin-bottom: 0.4rem;
        font-weight: 500;
    }

    .progress-bar-track {
        height: 8px;
        background: rgba(255, 255, 255, 0.05);
        border-radius: 4px;
        overflow: hidden;
    }

    .progress-bar-fill {
        height: 100%;
        border-radius: 4px;
        transition: width 1s cubic-bezier(0.4, 0, 0.2, 1);
    }

    /* ── Security Risk Cards ──────────────────────── */
    .risk-card {
        border-left: 4px solid;
        border-radius: 6px;
        padding: 1rem;
        margin-bottom: 0.75rem;
        background: rgba(255, 255, 255, 0.02);
        transition: all 0.2s ease;
    }

    .risk-card:hover {
        background: rgba(255, 255, 255, 0.04);
        transform: translateX(4px);
    }

    .risk-critical { border-left-color: #ef4444; background: rgba(239, 68, 68, 0.03); }
    .risk-high { border-left-color: #f97316; background: rgba(249, 115, 22, 0.03); }
    .risk-medium { border-left-color: #eab308; background: rgba(234, 179, 8, 0.03); }
    .risk-low { border-left-color: #3b82f6; background: rgba(59, 130, 246, 0.03); }
    .risk-info { border-left-color: #9ca3af; background: rgba(156, 163, 175, 0.03); }

    .risk-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.25rem;
    }

    .risk-badge {
        font-size: 0.7rem;
        text-transform: uppercase;
        font-weight: 700;
        padding: 0.2rem 0.5rem;
        border-radius: 4px;
    }

    .badge-critical { background: #ef4444; color: white; }
    .badge-high { background: #f97316; color: white; }
    .badge-medium { background: #eab308; color: black; }
    .badge-low { background: #3b82f6; color: white; }
    .badge-info { background: #6b7280; color: white; }

    /* ── Sidebar Style Overrides ──────────────────────── */
    section[data-testid="stSidebar"] {
        background: #090a0f !important;
        border-right: 1px solid rgba(255,255,255,0.03);
    }

    .sidebar-title {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-weight: 700;
        color: #f1f3f9;
        margin-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# Preset Templates (Demonstrating Pathways)
# ──────────────────────────────────────────────

TEMPLATES = {
    "Select Template...": "",
    "⚡ Quick Path: Basic Addition": """def add_values(x, y):
    # Simply sum two inputs
    return x + y
""",
    "🔬 Deep Path: Suboptimal Recursive Loop": """def recursive_fibonacci(limit):
    if limit <= 0:
        return 0
    elif limit == 1:
        return 1
    else:
        # High complexity recursion without memoization
        return recursive_fibonacci(limit - 1) + recursive_fibonacci(limit - 2)
""",
    "🔒 Security Path: SQL Injection & Secret": """import os
import sqlite3

def lookup_user(username, database_path):
    # Hardcoded credential pattern
    private_token = "gsk_vU81pZ5x9Ea0q2S3dT4fY5g6h7j8k9l0"
    
    connection = sqlite3.connect(database_path)
    cursor = connection.cursor()
    
    # Highly vulnerable dynamic SQL query compilation
    unsafe_query = f"SELECT * FROM members WHERE user = '{username}' AND api_key = '{private_token}'"
    cursor.execute(unsafe_query)
    
    return cursor.fetchall()
"""
}

# ──────────────────────────────────────────────
# Sidebar Configuration
# ──────────────────────────────────────────────

with st.sidebar:
    st.markdown("<h2 class='sidebar-title'>⚙️ Engine Setup</h2>", unsafe_allow_html=True)
    st.markdown("---")

    selected_model = st.selectbox(
        "🤖 Model Select",
        options=list(AVAILABLE_MODELS.keys()),
        format_func=lambda x: AVAILABLE_MODELS[x],
        index=list(AVAILABLE_MODELS.keys()).index(DEFAULT_MODEL),
        help="Select the LLM model for analysis.",
    )

    temperature = st.slider(
        "🌡️ Temperature",
        min_value=0.0,
        max_value=1.0,
        value=0.0,
        step=0.1,
        help="Lower = more deterministic. Higher = more creative.",
    )

    max_tokens = st.select_slider(
        "📏 Response Size Limit",
        options=[1024, 2048, 4096, 8192],
        value=4096,
        help="Maximum response tokens.",
    )

    st.markdown("---")
    st.markdown("<h3 class='sidebar-title'>📂 Code Upload</h3>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader(
        "Upload code file to analyze",
        type=["py", "js", "ts", "rs", "go", "cpp", "c", "java", "sql", "html", "css"],
        help="Loads code directly into the workspace."
    )

    st.markdown("---")
    st.markdown("<h3 class='sidebar-title'>📊 Engine Stats</h3>", unsafe_allow_html=True)
    total_analyses = len(st.session_state.get("history", []))
    st.metric("Workspace Analyses", total_analyses)
    
    st.markdown("---")
    st.markdown(
        "<div style='text-align:center; opacity:0.4; font-size:0.75rem; font-family:monospace;'>"
        "LangGraph Engine v1.2<br>Groq Hyper-Inference"
        "</div>",
        unsafe_allow_html=True,
    )

# ──────────────────────────────────────────────
# Header Display
# ──────────────────────────────────────────────

st.markdown(
    """
    <div class="main-header">
        <h1>🧠 Agentic AI Developer Workspace</h1>
        <p>A multi-agent development dashboard utilizing cooperative specialist agents for static analysis, security validation, and performance profiling.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ──────────────────────────────────────────────
# State Initialization
# ──────────────────────────────────────────────

if "history" not in st.session_state:
    st.session_state.history = []

if "current_result" not in st.session_state:
    st.session_state.current_result = None

# Determine initial text based on templates or file uploads
initial_code = ""

# Prioritize file upload
if uploaded_file is not None:
    try:
        initial_code = uploaded_file.read().decode("utf-8")
    except Exception as err:
        st.sidebar.error(f"Error reading file: {str(err)}")

# ──────────────────────────────────────────────
# Layout & Code Editor
# ──────────────────────────────────────────────

col_editor, col_presets = st.columns([3, 1])

with col_presets:
    st.markdown("##### 💡 Load Preset Samples")
    selected_template = st.selectbox(
        "Select sample code",
        options=list(TEMPLATES.keys()),
        label_visibility="collapsed"
    )
    if selected_template != "Select Template...":
        initial_code = TEMPLATES[selected_template]

with col_editor:
    st.markdown("##### 💻 Code Workspace")
    user_code = st.text_area(
        "Source Code input",
        value=initial_code,
        height=280,
        placeholder="Paste your source code or load a preset sample...",
        label_visibility="collapsed"
    )

col_run_btn, col_run_info = st.columns([1, 3])

with col_run_btn:
    analyze_clicked = st.button(
        "⚡ Analyze Workspace",
        type="primary",
        use_container_width=True,
    )

with col_run_info:
    st.markdown(
        f"<div style='padding-top: 0.5rem; opacity:0.7; font-size:0.85rem;'>"
        f"Selected Model: <b>{AVAILABLE_MODELS[selected_model]}</b> &nbsp;|&nbsp; "
        f"Lines: <b>{len(user_code.splitlines()) if user_code else 0}</b>"
        f"</div>",
        unsafe_allow_html=True
    )

# ──────────────────────────────────────────────
# Pipeline Executor
# ──────────────────────────────────────────────

if analyze_clicked:
    if not user_code.strip():
        st.warning("⚠️ Workspace is empty. Please enter code first.")
    else:
        config = AppConfig(
            model_name=selected_model,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        is_valid, error = config.validate()
        if not is_valid:
            st.error(f"❌ Config Error: {error}")
        else:
            workflow = build_workflow()
            initial_state = create_initial_state(user_code)
            initial_state["_config"] = config

            progress_bar = st.progress(0, text="🔄 Preparing analysis workspace...")
            start_time = time.time()

            try:
                # Custom steps for granular visual progress updates
                steps = [
                    (15, "🔧 Running static analysis and language detector..."),
                    (30, "🔀 Router: Evaluating routing pathway..."),
                    (55, "🔬 Invoking Code Review specialist..."),
                    (75, "🛡️ Running security scanner & performance profiling..."),
                    (90, "📊 Aggregator: Constructing quality matrix..."),
                ]

                step_idx = 0
                result = None

                for chunk in workflow.stream(initial_state):
                    if step_idx < len(steps):
                        pct, msg = steps[step_idx]
                        progress_bar.progress(pct, text=msg)
                        step_idx += 1

                    for node_name, node_output in chunk.items():
                        if "final_report" in node_output:
                            result = node_output
                        if result is None:
                            result = {}
                        result.update(node_output)

                elapsed_time = time.time() - start_time
                progress_bar.progress(100, text=f"✨ Workspace evaluated in {elapsed_time:.1f}s")
                time.sleep(0.3)
                progress_bar.empty()

                if result:
                    st.session_state.current_result = {
                        "code": user_code,
                        "result": result,
                        "elapsed": elapsed_time,
                        "model": selected_model,
                    }
                    st.session_state.history.append(st.session_state.current_result)

            except Exception as e:
                progress_bar.empty()
                logger.exception("Analysis graph invocation error")
                st.error(f"❌ Analysis failed: {str(e)}")

# ──────────────────────────────────────────────
# Parser Helpers
# ──────────────────────────────────────────────

def parse_scorecard(report_text: str) -> dict:
    """Parse category scorecard ratings from aggregator report markdown table."""
    scores = {"Correctness": 80, "Security": 90, "Performance": 85, "Readability": 80, "Best Practices": 80}
    if not report_text:
        return scores

    # Regex matches | Category | ⭐⭐⭐ |
    matches = re.findall(r"\|\s*([A-Za-z ]+)\s*\|\s*([⭐]+)\s*\|", report_text)
    for category, stars in matches:
        cat_name = category.strip()
        star_count = len(stars)
        if cat_name in scores:
            scores[cat_name] = star_count * 20  # Map to 0-100% scale
    return scores

def parse_vulnerabilities(sec_report: str) -> list:
    """Parse security vulnerabilities list from tool findings."""
    vulns = []
    if not sec_report:
        return vulns

    # Parse lines starting with "  - [SEVERITY]"
    pattern = r"-\s*\[(CRITICAL|HIGH|MEDIUM|LOW|INFO)\]\s*Line\s*(\d+):\s*(.*)"
    matches = re.findall(pattern, sec_report, re.IGNORECASE)
    for severity, line, desc in matches:
        vulns.append({
            "severity": severity.upper(),
            "line": line,
            "description": desc.strip()
        })
    return vulns

def parse_refactored_code(report_text: str) -> str:
    """Extract code block under refactored sections."""
    if not report_text:
        return ""
    # Find all code blocks
    code_blocks = re.findall(r"```[a-zA-Z0-9\+\-\#]*\n(.*?)\n```", report_text, re.DOTALL)
    if not code_blocks:
        return ""
    # Return the largest block (usually containing the refactored solution)
    return max(code_blocks, key=len)

# ──────────────────────────────────────────────
# Dashboard Output Rendering
# ──────────────────────────────────────────────

if st.session_state.current_result:
    res_data = st.session_state.current_result
    res_graph = res_data["result"]
    dur = res_data["elapsed"]

    language = res_graph.get("language", "unknown")
    complexity = res_graph.get("complexity_score", 0)
    analysis_type = res_graph.get("analysis_type", "quick")
    final_report = res_graph.get("final_report", "")

    # Scorecard & Metrics calculation
    scorecard_scores = parse_scorecard(final_report)
    health_index = int(sum(scorecard_scores.values()) / len(scorecard_scores))

    # Path badge styling
    badge_style = {
        "quick": ("badge-quick", "⚡ Quick Scan"),
        "deep": ("badge-deep", "🔬 Deep Analysis"),
        "security_focused": ("badge-security", "🔒 Security Focused")
    }.get(analysis_type, ("badge-quick", "⚡ Quick Scan"))

    st.markdown("<div class='custom-divider'></div>", unsafe_allow_html=True)

    # ── Row 1: KPI Dashboard Cards ────────────────────────
    kpi_col1, kpi_col2, kpi_col3, kpi_col4, kpi_col5 = st.columns(5)

    with kpi_col1:
        st.markdown(
            f"""<div class="dashboard-stat-card">
                <div class="dashboard-stat-label">Health Index</div>
                <div class="dashboard-stat-value">{health_index}%</div>
            </div>""",
            unsafe_allow_html=True
        )
    with kpi_col2:
        st.markdown(
            f"""<div class="dashboard-stat-card">
                <div class="dashboard-stat-label">Complexity</div>
                <div class="dashboard-stat-value">{complexity}/100</div>
            </div>""",
            unsafe_allow_html=True
        )
    with kpi_col3:
        st.markdown(
            f"""<div class="dashboard-stat-card">
                <div class="dashboard-stat-label">Detected Language</div>
                <div class="dashboard-stat-value" style="font-size:1.6rem; padding-top:0.35rem;">{language.upper()}</div>
            </div>""",
            unsafe_allow_html=True
        )
    with kpi_col4:
        st.markdown(
            f"""<div class="dashboard-stat-card">
                <div class="dashboard-stat-label">Analysis Route</div>
                <div style="margin-top:0.6rem;"><span class="status-badge {badge_style[0]}">{badge_style[1]}</span></div>
            </div>""",
            unsafe_allow_html=True
        )
    with kpi_col5:
        st.markdown(
            f"""<div class="dashboard-stat-card">
                <div class="dashboard-stat-label">Response Time</div>
                <div class="dashboard-stat-value">{dur:.1f}s</div>
            </div>""",
            unsafe_allow_html=True
        )

    # ── Row 2: Live Agent Visualization Diagram ────────────────────────
    pipeline_steps = [
        ("Preprocess", True),
        ("Router", True),
        ("Code Review", True),
        ("Security", analysis_type == "security_focused"),
        ("Optimization", analysis_type in ["deep", "security_focused"]),
        ("Aggregator", True)
    ]

    pipeline_nodes_html = ""
    for name, is_active in pipeline_steps:
        status_cls = "node-completed" if is_active else "node-skipped"
        if name == "Aggregator" and is_active:
            status_cls = "node-active"
        pipeline_nodes_html += f'<div class="pipeline-node {status_cls}">{name}</div>'
        if name != "Aggregator":
            pipeline_nodes_html += '<span style="color:rgba(255,255,255,0.15)">➔</span>'

    st.markdown(
        f"""
        <div class="glass-card" style="padding: 1rem 1.5rem; display: flex; flex-direction: column; align-items: center;">
            <div style="font-size: 0.75rem; text-transform: uppercase; letter-spacing: 1px; color:#9ca3af; margin-bottom: 0.75rem; font-weight:600;">Active Agent Workflow Pathway</div>
            <div class="pipeline-wrapper" style="margin: 0; width: 100%;">{pipeline_nodes_html}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # ── Row 3: Tabbed Workspace Results ────────────────────────
    workspace_tabs = st.tabs([
        "📋 Full Analysis Report",
        "🚀 Code Refactoring / Compare",
        "🛡️ Vulnerability Matrix",
        "⚡ Performance Metrics",
        "🎨 Scorecard Visualization"
    ])

    with workspace_tabs[0]:
        st.markdown(final_report)
        st.markdown("---")
        st.download_button(
            label="📥 Download Full Markdown Report",
            data=final_report,
            file_name="agentic_analysis_report.md",
            mime="text/markdown",
            use_container_width=True
        )

    with workspace_tabs[1]:
        col_orig, col_ref = st.columns(2)
        refactored_code = parse_refactored_code(res_graph.get("code_review", ""))
        if not refactored_code:
            refactored_code = parse_refactored_code(res_graph.get("optimization_report", ""))

        with col_orig:
            st.markdown("##### 📁 Original Workspace Code")
            st.code(res_data["code"], language=language if language != "unknown" else "python")

        with col_ref:
            st.markdown("##### ✨ Recommended Refactored Version")
            if refactored_code:
                st.code(refactored_code, language=language if language != "unknown" else "python")
            else:
                st.info("No refactored solution was output by the review agent. Check the Full Analysis Report for general improvement tips.")

    with workspace_tabs[2]:
        st.markdown("##### 🛡️ Automated Security Findings")
        security_text = res_graph.get("security_report", "")
        vuln_list = parse_vulnerabilities(res_graph.get("messages", [None])[0].content if res_graph.get("messages") else "")
        
        if not vuln_list:
            st.success("✅ Static scanners detected zero security issues in the workspace.")
        else:
            for item in vuln_list:
                sev = item["severity"]
                cls = {
                    "CRITICAL": "risk-critical",
                    "HIGH": "risk-high",
                    "MEDIUM": "risk-medium",
                    "LOW": "risk-low",
                    "INFO": "risk-info"
                }.get(sev, "risk-info")

                badge_cls = {
                    "CRITICAL": "badge-critical",
                    "HIGH": "badge-high",
                    "MEDIUM": "badge-medium",
                    "LOW": "badge-low",
                    "INFO": "badge-info"
                }.get(sev, "badge-info")

                st.markdown(
                    f"""<div class="risk-card {cls}">
                        <div class="risk-header">
                            <span style="font-weight:700; color:#f1f3f9;">{item['description']}</span>
                            <span class="risk-badge {badge_cls}">{sev}</span>
                        </div>
                        <div style="font-size:0.8rem; color:#9ca3af; margin-top:0.25rem;">Detected at line: <b>{item['line']}</b></div>
                    </div>""",
                    unsafe_allow_html=True
                )
        
        if security_text:
            st.markdown("---")
            st.markdown("##### 🔒 Detailed Security Recommendations")
            st.markdown(security_text)

    with workspace_tabs[3]:
        opt_report = res_graph.get("optimization_report", "")
        if opt_report:
            st.markdown(opt_report)
        else:
            st.info("Performance Profiler was not invoked. It runs during 'deep' or 'security_focused' evaluation runs.")

    with workspace_tabs[4]:
        st.markdown("##### 📊 Workspace Scorecard Metrics")
        
        score_colors = {
            "Correctness": "#4f46e5",
            "Security": "#10b981",
            "Performance": "#f59e0b",
            "Readability": "#3b82f6",
            "Best Practices": "#ec4899"
        }

        for cat, score in scorecard_scores.items():
            color = score_colors.get(cat, "#7c3aed")
            st.markdown(
                f"""
                <div class="progress-bar-container">
                    <div class="progress-bar-header">
                        <span style="font-weight:600;">{cat}</span>
                        <span style="font-weight:700; color:{color};">{score}%</span>
                    </div>
                    <div class="progress-bar-track">
                        <div class="progress-bar-fill" style="width: {score}%; background: {color};"></div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

# ──────────────────────────────────────────────
# History Panel
# ──────────────────────────────────────────────

if len(st.session_state.history) > 1:
    st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
    st.markdown("### 📜 Workspace Evaluation History")

    for i, entry in enumerate(reversed(st.session_state.history[:-1])):
        hist_lang = entry["result"].get("language", "unknown")
        hist_type = entry["result"].get("analysis_type", "quick")
        hist_elapsed = entry["elapsed"]
        hist_idx = len(st.session_state.history) - 1 - i

        with st.expander(
            f"Run #{hist_idx} — "
            f"Language: {hist_lang.upper()} | Type: {hist_type.title()} | Time: {hist_elapsed:.1f}s"
        ):
            hist_report = entry["result"].get("final_report", "")
            if hist_report:
                st.markdown(hist_report)
            st.code(entry["code"], language=hist_lang if hist_lang != "unknown" else "python")
