"""
Streamlit UI for the Agentic AI Code Analyzer.

Multi-theme interface offering Neo-Brutalism, Editorial Minimalist,
and Nordic Eco designs, moving away from AI-tech clichés.
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
# Sidebar Theme Selector & Configuration
# ──────────────────────────────────────────────

with st.sidebar:
    st.markdown("<h2 style='margin-top:0.5rem;'>🎨 Design Skin</h2>", unsafe_allow_html=True)
    
    selected_theme = st.selectbox(
        "Select Interface Look",
        options=["Neo-Brutalism", "Editorial Minimalist", "Nordic Eco"],
        index=2, # Default to Nordic Eco
        help="Instantly toggle the UI style skin."
    )
    
    st.markdown("---")
    st.markdown("## ⚙️ Engine Setup")

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
    st.markdown("### 📂 Code Upload")
    uploaded_file = st.file_uploader(
        "Upload code file to analyze",
        type=["py", "js", "ts", "rs", "go", "cpp", "c", "java", "sql", "html", "css"],
        help="Loads code directly into the workspace."
    )

    st.markdown("---")
    st.markdown("### 📊 Engine Stats")
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
# CSS Variable Definition Blocks based on Theme
# ──────────────────────────────────────────────

THEME_CSS = ""

if selected_theme == "Neo-Brutalism":
    THEME_CSS = """
    :root {
        /* App and Typography */
        --bg-app: #f3f4f6;
        --text-color: #000000;
        --font-headers: 'JetBrains Mono', monospace;
        --font-body: 'JetBrains Mono', monospace;
        
        /* Card Styles */
        --bg-card: #ffffff;
        --border-card: 3px solid #000000;
        --border-radius-card: 0px;
        --shadow-card: 6px 6px 0px #000000;
        
        /* Header Block */
        --bg-header: #f43f5e;
        --color-header-text: #ffffff;
        --color-header-p: #ffffff;
        --shadow-header: 6px 6px 0px #000000;
        --border-radius-header: 0px;
        --border-header: 3px solid #000000;
        
        /* Stats */
        --bg-stat: #ffffff;
        --border-stat: 3px solid #000000;
        --shadow-stat: 4px 4px 0px #000000;
        --border-radius-stat: 0px;
        --color-stat-val: #f43f5e;
        
        /* Route Badges */
        --badge-quick: #22c55e;
        --badge-deep: #eab308;
        --badge-security: #ef4444;
        --badge-border: 2px solid #000000;
        --badge-text-color: #000000;
        --badge-radius: 0px;
        
        /* Pipeline Flow nodes */
        --bg-node-completed: #22c55e;
        --border-node-completed: 2px solid #000000;
        --color-node-completed: #000000;
        
        --bg-node-active: #f43f5e;
        --border-node-active: 2px solid #000000;
        --color-node-active: #ffffff;
        
        --bg-node-skipped: #e5e7eb;
        --border-node-skipped: 2px dashed #9ca3af;
        --color-node-skipped: #9ca3af;
        
        /* General Accents */
        --accent-line: #000000;
        --input-border: 2px solid #000000;
    }
    
    /* Sidebar specific brutalist style overrides */
    section[data-testid="stSidebar"] {
        background-color: #f3f4f6 !important;
        border-right: 3px solid #000000 !important;
        color: #000000 !important;
    }
    section[data-testid="stSidebar"] * {
        color: #000000 !important;
    }
    """
elif selected_theme == "Editorial Minimalist":
    THEME_CSS = """
    :root {
        /* App and Typography */
        --bg-app: #faf9f6;
        --text-color: #1c1917;
        --font-headers: 'Playfair Display', Georgia, serif;
        --font-body: 'Lora', Georgia, serif;
        
        /* Card Styles */
        --bg-card: #ffffff;
        --border-card: 1px solid #d6d3d1;
        --border-radius-card: 2px;
        --shadow-card: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        
        /* Header Block */
        --bg-header: #1c1917;
        --color-header-text: #faf9f6;
        --color-header-p: #d6d3d1;
        --shadow-header: none;
        --border-radius-header: 2px;
        --border-header: 1px solid #1c1917;
        
        /* Stats */
        --bg-stat: #ffffff;
        --border-stat: 1px solid #e7e5e4;
        --shadow-stat: none;
        --border-radius-stat: 2px;
        --color-stat-val: #991b1b;
        
        /* Route Badges */
        --badge-quick: #f5f5f4;
        --badge-deep: #f5f5f4;
        --badge-security: #991b1b;
        --badge-border: 1px solid #d6d3d1;
        --badge-text-color: #1c1917;
        --badge-radius: 2px;
        
        /* Pipeline Flow nodes */
        --bg-node-completed: #f5f5f4;
        --border-node-completed: 1px solid #d6d3d1;
        --color-node-completed: #1c1917;
        
        --bg-node-active: #991b1b;
        --border-node-active: 1px solid #991b1b;
        --color-node-active: #faf9f6;
        
        --bg-node-skipped: transparent;
        --border-node-skipped: 1px dashed #d6d3d1;
        --color-node-skipped: #a8a29e;
        
        /* General Accents */
        --accent-line: #991b1b;
        --input-border: 1px solid #d6d3d1;
    }
    
    /* Sidebar specific editorial style overrides */
    section[data-testid="stSidebar"] {
        background-color: #f5f5f4 !important;
        border-right: 1px solid #d6d3d1 !important;
        color: #1c1917 !important;
    }
    section[data-testid="stSidebar"] * {
        color: #1c1917 !important;
    }
    """
else: # Nordic Eco Theme
    THEME_CSS = """
    :root {
        /* App and Typography */
        --bg-app: #f2efe9;
        --text-color: #2d3748;
        --font-headers: 'Plus Jakarta Sans', sans-serif;
        --font-body: 'Plus Jakarta Sans', sans-serif;
        
        /* Card Styles */
        --bg-card: #ffffff;
        --border-card: 1px solid rgba(0, 0, 0, 0.04);
        --border-radius-card: 24px;
        --shadow-card: 0 10px 25px -5px rgba(0,0,0,0.02), 0 8px 10px -6px rgba(0,0,0,0.02);
        
        /* Header Block */
        --bg-header: #3c4e43;
        --color-header-text: #f2efe9;
        --color-header-p: #c7d2c4;
        --shadow-header: 0 12px 30px rgba(60, 78, 67, 0.15);
        --border-radius-header: 24px;
        --border-header: 1px solid rgba(60, 78, 67, 0.2);
        
        /* Stats */
        --bg-stat: #ffffff;
        --border-stat: 1px solid rgba(0, 0, 0, 0.03);
        --shadow-stat: 0 4px 12px rgba(0,0,0,0.01);
        --border-radius-stat: 16px;
        --color-stat-val: #3c4e43;
        
        /* Route Badges */
        --badge-quick: #82957f;
        --badge-deep: #b3a492;
        --badge-security: #c88a75;
        --badge-border: none;
        --badge-text-color: #ffffff;
        --badge-radius: 12px;
        
        /* Pipeline Flow nodes */
        --bg-node-completed: rgba(130, 149, 127, 0.15);
        --border-node-completed: 1px solid #82957f;
        --color-node-completed: #3c4e43;
        
        --bg-node-active: #3c4e43;
        --border-node-active: 1px solid #3c4e43;
        --color-node-active: #f2efe9;
        
        --bg-node-skipped: rgba(0, 0, 0, 0.02);
        --border-node-skipped: 1px dashed rgba(0, 0, 0, 0.15);
        --color-node-skipped: #8d9096;
        
        /* General Accents */
        --accent-line: #82957f;
        --input-border: 1px solid rgba(0, 0, 0, 0.08);
    }
    
    /* Sidebar specific nordic style overrides */
    section[data-testid="stSidebar"] {
        background-color: #eae6dd !important;
        border-right: 1px solid rgba(0,0,0,0.05) !important;
        color: #2d3748 !important;
    }
    section[data-testid="stSidebar"] * {
        color: #2d3748 !important;
    }
    """

# ──────────────────────────────────────────────
# Style Block Injection
# ──────────────────────────────────────────────

st.markdown(f"""
<style>
    {THEME_CSS}
    
    /* ── Global Styles ──────────────────────── */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;700&family=Playfair+Display:ital,wght@0,400;0,700;1,400&family=Lora:ital,wght@0,400;0,500;1,400&display=swap');

    .stApp {{
        font-family: var(--font-body), sans-serif;
        background-color: var(--bg-app);
        color: var(--text-color);
        transition: background-color 0.3s ease, color 0.3s ease;
    }}

    h1, h2, h3, h4, h5, h6 {{
        font-family: var(--font-headers), sans-serif !important;
        color: var(--text-color) !important;
        font-weight: 700;
    }}

    /* ── Card Styling ──────────────────────── */
    .glass-card {{
        background-color: var(--bg-card);
        border: var(--border-card);
        border-radius: var(--border-radius-card);
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: var(--shadow-card);
        transition: all 0.3s ease;
    }}

    .main-header {{
        background: var(--bg-header);
        border: var(--border-header);
        padding: 2.5rem;
        border-radius: var(--border-radius-header);
        margin-bottom: 2rem;
        color: var(--color-header-text);
        box-shadow: var(--shadow-header);
        position: relative;
    }}

    .main-header h1 {{
        color: var(--color-header-text) !important;
        font-weight: 800;
        margin: 0;
    }}

    .main-header p {{
        color: var(--color-header-p) !important;
        margin: 0.75rem 0 0;
        font-size: 1.1rem;
        font-weight: 400;
    }}

    /* ── Stats Dashboard ──────────────────────── */
    .dashboard-stat-card {{
        background-color: var(--bg-stat);
        border: var(--border-stat);
        border-radius: var(--border-radius-stat);
        padding: 1.25rem;
        text-align: center;
        box-shadow: var(--shadow-stat);
        transition: transform 0.3s ease;
    }}

    .dashboard-stat-card:hover {{
        transform: translateY(-2px);
    }}

    .dashboard-stat-value {{
        font-size: 2rem;
        font-weight: 800;
        margin: 0.25rem 0;
        color: var(--color-stat-val);
        font-family: var(--font-headers), sans-serif;
    }}

    .dashboard-stat-label {{
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        color: var(--text-color);
        opacity: 0.6;
        font-weight: 600;
    }}

    /* ── Pipeline Flows ──────────────────────── */
    .pipeline-wrapper {{
        display: flex;
        align-items: center;
        justify-content: center;
        flex-wrap: wrap;
        gap: 0.75rem;
        margin: 1.5rem 0;
        padding: 1rem;
        background-color: rgba(0, 0, 0, 0.02);
        border-radius: var(--border-radius-card);
        border: var(--border-card);
    }}

    .pipeline-node {{
        padding: 0.5rem 1.25rem;
        border-radius: var(--badge-radius);
        font-size: 0.85rem;
        font-weight: 600;
        transition: all 0.3s ease;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }}

    .node-completed {{
        background-color: var(--bg-node-completed);
        color: var(--color-node-completed);
        border: var(--border-node-completed);
    }}

    .node-active {{
        background-color: var(--bg-node-active);
        color: var(--color-node-active);
        border: var(--border-node-active);
    }}

    .node-skipped {{
        background-color: var(--bg-node-skipped);
        color: var(--color-node-skipped);
        border: var(--border-node-skipped);
    }}

    /* ── Status Badges ──────────────────────── */
    .status-badge {{
        display: inline-block;
        padding: 0.3rem 0.9rem;
        border-radius: var(--badge-radius);
        border: var(--badge-border);
        font-size: 0.8rem;
        font-weight: 700;
        letter-spacing: 0.5px;
        color: var(--badge-text-color);
    }}

    .badge-quick {{ background-color: var(--badge-quick); }}
    .badge-deep {{ background-color: var(--badge-deep); }}
    .badge-security {{ background-color: var(--badge-security); }}

    /* ── Progress bars ──────────────────────── */
    .progress-bar-container {{
        margin-bottom: 1.25rem;
    }}

    .progress-bar-header {{
        display: flex;
        justify-content: space-between;
        font-size: 0.85rem;
        margin-bottom: 0.4rem;
        font-weight: 600;
    }}

    .progress-bar-track {{
        height: 10px;
        background-color: rgba(0, 0, 0, 0.05);
        border-radius: var(--badge-radius);
        border: var(--border-card);
        overflow: hidden;
    }}

    .progress-bar-fill {{
        height: 100%;
        transition: width 1s ease-in-out;
    }}

    /* ── Vulnerability Cards ──────────────────────── */
    .risk-card {{
        border: var(--border-card);
        border-left-width: 8px !important;
        border-radius: var(--border-radius-card);
        padding: 1rem;
        margin-bottom: 0.75rem;
        background-color: var(--bg-card);
        transition: transform 0.2s ease;
    }}

    .risk-card:hover {{
        transform: translateX(4px);
    }}

    .risk-critical {{ border-left-color: #ef4444 !important; }}
    .risk-high {{ border-left-color: #f97316 !important; }}
    .risk-medium {{ border-left-color: #eab308 !important; }}
    .risk-low {{ border-left-color: #3b82f6 !important; }}
    .risk-info {{ border-left-color: #9ca3af !important; }}

    .risk-header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.25rem;
    }}

    .risk-badge {{
        font-size: 0.7rem;
        text-transform: uppercase;
        font-weight: 700;
        padding: 0.25rem 0.6rem;
        border-radius: var(--badge-radius);
        border: var(--border-card);
    }}

    .badge-critical {{ background-color: #ef4444; color: white; }}
    .badge-high {{ background-color: #f97316; color: white; }}
    .badge-medium {{ background-color: #eab308; color: black; }}
    .badge-low {{ background-color: #3b82f6; color: white; }}
    .badge-info {{ background-color: #6b7280; color: white; }}

    /* ── Custom Dividers ──────────────────────── */
    .custom-divider {{
        height: 2px;
        background-color: var(--accent-line);
        margin: 1.5rem 0;
        opacity: 0.2;
    }}
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
        f"<div style='padding-top: 0.5rem; opacity:0.7; font-size:0.85rem; font-family:var(--font-headers);'>"
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

if st.session_state.get("current_result"):
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
                <div class="dashboard-stat-label">Language</div>
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
            pipeline_nodes_html += '<span style="color:var(--text-color); opacity:0.3;">➔</span>'

    st.markdown(
        f"""
        <div class="glass-card" style="padding: 1rem 1.5rem; display: flex; flex-direction: column; align-items: center;">
            <div style="font-size: 0.75rem; text-transform: uppercase; letter-spacing: 1px; color:var(--text-color); opacity:0.7; margin-bottom: 0.75rem; font-weight:600; font-family:var(--font-headers);">Active Agent Workflow Pathway</div>
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
                            <span style="font-weight:700; color:var(--text-color);">{item['description']}</span>
                            <span class="risk-badge {badge_cls}">{sev}</span>
                        </div>
                        <div style="font-size:0.8rem; color:var(--text-color); opacity:0.7; margin-top:0.25rem;">Detected at line: <b>{item['line']}</b></div>
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

        # Override colors if Brutalist or Editorial themes are selected
        if selected_theme == "Neo-Brutalism":
            score_colors = {k: "#000000" for k in score_colors}
        elif selected_theme == "Editorial Minimalist":
            score_colors = {k: "#991b1b" for k in score_colors}

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

if len(st.session_state.get("history", [])) > 1:
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