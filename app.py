"""
Streamlit UI for the Agentic AI Code Analyzer.
Uses native Streamlit components for reliable visibility.
"""

import time
import re
import streamlit as st

from config import AppConfig, AVAILABLE_MODELS, DEFAULT_MODEL, logger
from state import create_initial_state
from graph import build_workflow

# ──────────────────────────────────────────────
# Page Config
# ──────────────────────────────────────────────

st.set_page_config(
    page_title="Code Analyzer",
    page_icon="⬡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Minimal CSS — only accent touches, no layout overrides
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    [data-testid="stSidebarCollapsedControl"] { display: none; }
    section[data-testid="stSidebar"] { display: none; }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# Session State
# ──────────────────────────────────────────────

if "history" not in st.session_state:
    st.session_state.history = []
if "current_result" not in st.session_state:
    st.session_state.current_result = None

# ──────────────────────────────────────────────
# Top Bar (using native columns)
# ──────────────────────────────────────────────

top_left, top_right = st.columns([3, 1])
with top_left:
    st.markdown("## ⬡ Code Analyzer")
    st.caption("Multi-agent code review, security analysis & performance optimization")
with top_right:
    st.metric("Total Runs", len(st.session_state.history))

st.divider()

# ──────────────────────────────────────────────
# Settings Row
# ──────────────────────────────────────────────

with st.expander("⚙️  Settings & Configuration"):
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        selected_model = st.selectbox(
            "Model",
            list(AVAILABLE_MODELS.keys()),
            format_func=lambda x: AVAILABLE_MODELS[x],
            index=list(AVAILABLE_MODELS.keys()).index(DEFAULT_MODEL),
        )
    with c2:
        temperature = st.slider("Temperature", 0.0, 1.0, 0.0, 0.1)
    with c3:
        max_tokens = st.select_slider("Max Tokens", [1024, 2048, 4096, 8192], 4096)
    with c4:
        uploaded_file = st.file_uploader(
            "Upload code file",
            type=["py", "js", "ts", "rs", "go", "cpp", "c", "java", "sql", "html", "css"],
        )

# ──────────────────────────────────────────────
# Templates
# ──────────────────────────────────────────────

TEMPLATES = {
    "— Select a template —": "",
    "Quick: Simple function": "def add(a, b):\n    return a + b\n",
    "Deep: Recursive Fibonacci": (
        "def fib(n):\n"
        "    if n <= 0:\n"
        "        return 0\n"
        "    elif n == 1:\n"
        "        return 1\n"
        "    return fib(n - 1) + fib(n - 2)\n"
    ),
    "Security: SQL injection + hardcoded secret": (
        "import sqlite3\n\n"
        "def get_user(user_id, db_path):\n"
        '    secret = "sk_live_abc123xyz789"\n'
        "    conn = sqlite3.connect(db_path)\n"
        '    query = f"SELECT * FROM users WHERE id = \'{user_id}\'"\n'
        "    return conn.execute(query).fetchall()\n"
    ),
}

# ──────────────────────────────────────────────
# Code Input
# ──────────────────────────────────────────────

col_code, col_opts = st.columns([3, 1])

initial_code = ""
if uploaded_file:
    try:
        initial_code = uploaded_file.read().decode("utf-8")
    except Exception:
        pass

with col_opts:
    st.markdown("**Load a template**")
    tpl = st.selectbox(
        "template_select",
        list(TEMPLATES.keys()),
        label_visibility="collapsed",
    )
    if tpl != "— Select a template —":
        initial_code = TEMPLATES[tpl]

    st.markdown("---")
    st.markdown(f"**Model:** {AVAILABLE_MODELS[selected_model]}")
    st.markdown(f"**Temp:** {temperature}  ·  **Tokens:** {max_tokens}")

with col_code:
    user_code = st.text_area(
        "Paste your code here",
        value=initial_code,
        height=260,
        placeholder="Paste code here, or pick a template from the right panel →",
    )

analyze = st.button("▶  Run Analysis", type="primary", use_container_width=True)

# ──────────────────────────────────────────────
# Execution
# ──────────────────────────────────────────────

if analyze:
    if not user_code.strip():
        st.warning("Please paste some code first.")
    else:
        config = AppConfig(
            model_name=selected_model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        ok, err = config.validate()
        if not ok:
            st.error(err)
        else:
            wf = build_workflow()
            state = create_initial_state(user_code)
            state["_config"] = config

            bar = st.progress(0, text="Preparing...")
            t0 = time.time()

            try:
                steps = [
                    (15, "Running static analysis tools..."),
                    (30, "Routing to specialists..."),
                    (55, "Code review in progress..."),
                    (75, "Security & performance scan..."),
                    (90, "Aggregating final report..."),
                ]
                si = 0
                result = None

                for chunk in wf.stream(state):
                    if si < len(steps):
                        bar.progress(steps[si][0], text=steps[si][1])
                        si += 1
                    for _, out in chunk.items():
                        if result is None:
                            result = {}
                        result.update(out)

                elapsed = time.time() - t0
                bar.progress(100, text=f"Done in {elapsed:.1f}s")
                time.sleep(0.4)
                bar.empty()

                if result:
                    st.session_state.current_result = {
                        "code": user_code,
                        "result": result,
                        "elapsed": elapsed,
                        "model": selected_model,
                    }
                    st.session_state.history.append(st.session_state.current_result)
                    st.rerun()

            except Exception as e:
                bar.empty()
                logger.exception("Analysis failed")
                st.error(f"Analysis failed: {e}")

# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def _parse_scores(text):
    scores = {"Correctness": 80, "Security": 90, "Performance": 85, "Readability": 80, "Best Practices": 80}
    if not text:
        return scores
    for cat, stars in re.findall(r"\|\s*([A-Za-z ]+)\s*\|\s*([⭐]+)\s*\|", text):
        c = cat.strip()
        if c in scores:
            scores[c] = len(stars) * 20
    return scores

def _parse_vulns(text):
    if not text:
        return []
    return [
        {"sev": s.upper(), "line": ln, "desc": d.strip()}
        for s, ln, d in re.findall(
            r"-\s*\[(CRITICAL|HIGH|MEDIUM|LOW|INFO)\]\s*Line\s*(\d+):\s*(.*)", text, re.I
        )
    ]

def _parse_code_block(text):
    if not text:
        return ""
    blocks = re.findall(r"```[a-zA-Z0-9+\-#]*\n(.*?)\n```", text, re.DOTALL)
    return max(blocks, key=len) if blocks else ""

# ──────────────────────────────────────────────
# Results Display
# ──────────────────────────────────────────────

if st.session_state.get("current_result"):
    rd = st.session_state.current_result
    r = rd["result"]
    dur = rd["elapsed"]

    lang = r.get("language", "unknown")
    cpx = r.get("complexity_score", 0)
    atype = r.get("analysis_type", "quick")
    report = r.get("final_report", "")

    scores = _parse_scores(report)
    health = int(sum(scores.values()) / len(scores))

    route_label = {"quick": "Quick", "deep": "Deep", "security_focused": "Security"}.get(atype, "Quick")

    st.divider()

    # ── Metrics Row (native st.metric) ─────────
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Health Index", f"{health}%")
    m2.metric("Complexity", f"{cpx}/100")
    m3.metric("Language", lang.upper())
    m4.metric("Route", route_label)
    m5.metric("Time", f"{dur:.1f}s")

    # ── Pipeline (native st.columns) ─────────
    st.markdown("**Agent Pipeline:**")
    all_nodes = [
        ("Preprocess", True),
        ("Router", True),
        ("Code Review", True),
        ("Security", atype == "security_focused"),
        ("Optimization", atype in ("deep", "security_focused")),
        ("Aggregator", True),
    ]

    pipe_cols = st.columns(len(all_nodes))
    for col, (name, active) in zip(pipe_cols, all_nodes):
        if active:
            col.success(name)
        else:
            col.markdown(f"~~{name}~~")

    st.divider()

    # ── Tabbed Results ─────────
    tab_report, tab_compare, tab_vulns, tab_perf, tab_scores = st.tabs(
        ["📋 Report", "🔄 Compare", "🛡️ Vulnerabilities", "⚡ Performance", "📊 Scores"]
    )

    with tab_report:
        if report:
            st.markdown(report)
        else:
            st.info("No report generated.")
        st.divider()
        st.download_button(
            "📥 Download Report",
            report or "",
            "analysis_report.md",
            "text/markdown",
            use_container_width=True,
        )

    with tab_compare:
        ref = _parse_code_block(r.get("code_review", "")) or _parse_code_block(
            r.get("optimization_report", "")
        )
        lc, rc = st.columns(2)
        with lc:
            st.markdown("**Original Code**")
            st.code(rd["code"], language=lang if lang != "unknown" else "python")
        with rc:
            st.markdown("**Refactored Code**")
            if ref:
                st.code(ref, language=lang if lang != "unknown" else "python")
            else:
                st.info("No refactored code was returned by the agents.")

    with tab_vulns:
        sec_text = r.get("security_report", "")
        first_msg = ""
        msgs_list = r.get("messages", [])
        if msgs_list and hasattr(msgs_list[0], "content"):
            first_msg = msgs_list[0].content
        vulns = _parse_vulns(first_msg)

        if not vulns:
            st.success("No security issues detected.")
        else:
            st.warning(f"Found {len(vulns)} issue(s)")
            for v in vulns:
                sev = v["sev"]
                icon = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🔵", "INFO": "⚪"}.get(sev, "⚪")
                with st.container(border=True):
                    vc1, vc2 = st.columns([4, 1])
                    vc1.markdown(f"{icon} **{v['desc']}**")
                    vc1.caption(f"Line {v['line']}")
                    vc2.markdown(f"**{sev}**")

        if sec_text:
            st.divider()
            st.markdown("**Detailed Security Report**")
            st.markdown(sec_text)

    with tab_perf:
        opt = r.get("optimization_report", "")
        if opt:
            st.markdown(opt)
        else:
            st.info("Optimization runs only on deep or security-focused analysis paths.")

    with tab_scores:
        st.markdown("**Quality Scorecard**")
        for cat, sc in scores.items():
            st.progress(sc / 100, text=f"{cat}: {sc}%")

# ──────────────────────────────────────────────
# History
# ──────────────────────────────────────────────

hist = st.session_state.get("history", [])
if len(hist) > 1:
    st.divider()
    st.markdown("#### Previous Runs")
    for i, entry in enumerate(reversed(hist[:-1])):
        hl = entry["result"].get("language", "unknown")
        ht = entry["result"].get("analysis_type", "quick")
        he = entry["elapsed"]
        idx = len(hist) - 1 - i
        with st.expander(f"Run #{idx}  ·  {hl.upper()}  ·  {ht}  ·  {he:.1f}s"):
            hr = entry["result"].get("final_report", "")
            if hr:
                st.markdown(hr)
            st.code(entry["code"], language=hl if hl != "unknown" else "python")