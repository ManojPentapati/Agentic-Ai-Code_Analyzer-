"""Streamlit UI for the Agentic AI Code Analyzer."""

import pathlib
import time
import re
import streamlit as st

from config import AppConfig, AVAILABLE_MODELS, DEFAULT_MODEL, logger
from state import create_initial_state
from graph import build_workflow
from pdf_generator import generate_analysis_pdf


def _parse_scores(text: str) -> dict:
    """Parse star-rating scorecard from report text."""
    scores = {
        "Correctness": 80,
        "Security": 90,
        "Performance": 85,
        "Readability": 80,
        "Best Practices": 80,
    }
    if not text:
        return scores
    for cat, stars in re.findall(r"\|\s*([A-Za-z ]+)\s*\|\s*([*]+)\s*\|", text):
        c = cat.strip()
        if c in scores:
            scores[c] = len(stars) * 20
    return scores


# --- Page Config ---

st.set_page_config(
    page_title="Code Analyzer",
    page_icon="⬡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Load CSS from external file
_css_path = pathlib.Path(__file__).parent / "style.css"
if _css_path.exists():
    st.markdown(f"<style>{_css_path.read_text()}</style>", unsafe_allow_html=True)

# --- Session State ---

if "history" not in st.session_state:
    st.session_state.history = []
if "current_result" not in st.session_state:
    st.session_state.current_result = None
if "score_history" not in st.session_state:
    st.session_state.score_history = []


def clone_repo(repo_url: str) -> str | None:
    """Clones a git repository into .temp_cloned_repos/ and returns the local directory path."""
    import subprocess
    import shutil
    import urllib.parse

    try:
        parsed_url = urllib.parse.urlparse(repo_url)
        path_parts = parsed_url.path.strip("/").split("/")
        if not path_parts or path_parts[-1] == "":
            return None
        repo_name = path_parts[-1]
        if repo_name.endswith(".git"):
            repo_name = repo_name[:-4]
    except Exception:
        return None

    base_dir = pathlib.Path(__file__).parent / ".temp_cloned_repos"
    target_dir = base_dir / repo_name

    # If it already exists and is a valid git repo, we can reuse it
    if target_dir.exists() and (target_dir / ".git").exists():
        return str(target_dir)

    # Otherwise clean and clone
    if target_dir.exists():
        shutil.rmtree(target_dir, ignore_errors=True)

    target_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Run clone with depth 1
        subprocess.run(
            ["git", "clone", "--depth", "1", repo_url, str(target_dir)],
            capture_output=True,
            text=True,
            check=True,
        )
        return str(target_dir)
    except Exception as e:
        st.error(f"Failed to clone repository: {e}")
        if target_dir.exists():
            shutil.rmtree(target_dir, ignore_errors=True)
        return None


def list_code_files(dir_path: str) -> list[str]:
    """List code files recursively in the directory matching key extensions."""
    supported_exts = {
        ".py",
        ".js",
        ".ts",
        ".rs",
        ".go",
        ".cpp",
        ".c",
        ".java",
        ".sql",
        ".html",
        ".css",
    }
    base_path = pathlib.Path(dir_path)
    file_list = []

    for p in base_path.rglob("*"):
        if p.is_file() and p.suffix.lower() in supported_exts:
            # Skip hidden files/directories (like .git)
            parts = p.relative_to(base_path).parts
            if any(part.startswith(".") for part in parts):
                continue
            file_list.append(str(p.relative_to(base_path)))

    return sorted(file_list)

# --- Top Bar (using native columns) ---

top_left, top_right = st.columns([3, 1])
with top_left:
    st.markdown("## :material/analytics: Code Analyzer")
    st.caption(":material/hub: Multi-agent code review, security analysis & performance optimization")
with top_right:
    st.metric("Total Runs", len(st.session_state.history))

st.divider()

# --- Settings Row ---

cloned_dir = None
selected_git_file = None
git_url = ""

# Model selector row — always visible
cfg1, cfg2, cfg3 = st.columns(3)
with cfg1:
    selected_model = st.selectbox(
        ":material/model_training: Model",
        list(AVAILABLE_MODELS.keys()),
        format_func=lambda x: AVAILABLE_MODELS[x],
        index=list(AVAILABLE_MODELS.keys()).index(DEFAULT_MODEL),
    )
with cfg2:
    temperature = st.slider(":material/thermostat: Temperature", 0.0, 1.0, 0.0, 0.1)
with cfg3:
    max_tokens = st.select_slider(":material/token: Max Tokens", [1024, 2048, 4096, 8192], 4096)

with st.expander(":material/settings: Advanced Settings"):
    c4, c5 = st.columns(2)
    with c4:
        uploaded_file = st.file_uploader(
            ":material/upload_file: Upload code file",
            type=["py", "js", "ts", "rs", "go", "cpp", "c", "java", "sql", "html", "css"],
        )
    with c5:
        git_url = st.text_input(
            ":material/link: Clone public Git Repository URL",
            placeholder="https://github.com/username/repo",
            help="Provide a public git repository URL to index and analyze its source files."
        )

    # If Git URL is provided, clone and let user pick a file
    if git_url:
        cloned_dir = clone_repo(git_url)
        if cloned_dir:
            git_files = list_code_files(cloned_dir)
            if git_files:
                selected_git_file = st.selectbox(
                    "Select file from repository to analyze",
                    ["-- Choose a file --"] + git_files
                )

# --- Templates ---

TEMPLATES = {
    "-- Select a template --": "",
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

# --- Code Input ---

col_code, col_opts = st.columns([3, 1])

initial_code = ""
if uploaded_file:
    try:
        initial_code = uploaded_file.read().decode("utf-8")
    except Exception:
        pass

if git_url and selected_git_file and selected_git_file != "-- Choose a file --" and cloned_dir:
    try:
        file_path = pathlib.Path(cloned_dir) / selected_git_file
        initial_code = file_path.read_text(encoding="utf-8")
    except Exception as e:
        st.error(f"Failed to read file: {e}")

with col_opts:
    st.markdown(":material/library_books: **Load a template**")
    tpl = st.selectbox(
        "template_select",
        list(TEMPLATES.keys()),
        label_visibility="collapsed",
    )
    if tpl != "-- Select a template --":
        initial_code = TEMPLATES[tpl]

    st.markdown("---")
    st.markdown(f":material/model_training: **Model:** {AVAILABLE_MODELS[selected_model]}")
    st.markdown(f":material/thermostat: **Temp:** {temperature}  |  :material/token: **Tokens:** {max_tokens}")

with col_code:
    user_code = st.text_area(
        ":material/code: Paste your code here",
        value=initial_code,
        height=260,
        placeholder="Paste code here, or pick a template from the right panel",
    )

_btn_pad_l, _btn_center, _btn_pad_r = st.columns([2, 1, 2])
with _btn_center:
    analyze = st.button("Run Analysis", type="primary", icon=":material/play_arrow:", use_container_width=True)

# --- Execution ---

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

            t0 = time.time()
            result = None

            try:
                with st.status("Analyzing code...", expanded=True) as status:
                    st.write("🔧 **Initializing workflow...**")
                    for chunk in wf.stream(state):
                        for node_name, out in chunk.items():
                            if result is None:
                                result = {}
                            result.update(out)

                            if node_name == "preprocess":
                                lang_label = out.get("language", "unknown").upper()
                                comp_val = out.get("complexity_score", 0)
                                st.write(f"📥 **Preprocessing complete** · Detected: `{lang_label}` (Complexity: `{comp_val}/100`)")
                            elif node_name == "router":
                                route_label = out.get("analysis_type", "quick").upper()
                                st.write(f"🔀 **Router complete** · Routing to: `{route_label}` depth")
                            elif node_name == "code_review":
                                st.write("🔍 **Senior Reviewer complete** · Code standards and readability assessed")
                            elif node_name == "security":
                                st.write("🔒 **Security Expert complete** · Vulnerability vulnerabilities audited")
                            elif node_name == "optimize":
                                st.write("⚡ **Performance Engineer complete** · Runtime complexity optimized")
                            elif node_name == "aggregate":
                                st.write("📊 **Aggregator complete** · Compiling executive quality scorecard")

                    elapsed = time.time() - t0
                    status.update(label=f"Analysis complete in {elapsed:.1f}s!", state="complete", expanded=False)
                    time.sleep(1.0)

                if result:
                    # Calculate health index score from aggregator report
                    report = result.get("final_report", "")
                    scores = _parse_scores(report)
                    health = int(sum(scores.values()) / len(scores)) if scores else 0
                    st.session_state.score_history.append(health)

                    st.session_state.current_result = {
                        "code": user_code,
                        "result": result,
                        "elapsed": elapsed,
                        "model": selected_model,
                    }
                    st.session_state.history.append(st.session_state.current_result)
                    st.rerun()

            except Exception as e:
                # Update status to error state instead of leaving it spinning/stuck
                if 'status' in locals():
                    status.update(label="Analysis failed!", state="error", expanded=True)
                logger.exception("Analysis failed")
                st.error(f"Analysis failed: {e}")

# --- Helpers ---


def _parse_vulns(text: str) -> list:
    """Extract vulnerability entries from tool output."""
    if not text:
        return []
    return [
        {"sev": s.upper(), "line": ln, "desc": d.strip()}
        for s, ln, d in re.findall(
            r"-\s*\[(CRITICAL|HIGH|MEDIUM|LOW|INFO)\]\s*Line\s*(\d+):\s*(.*)",
            text,
            re.I,
        )
    ]


def _parse_code_block(text: str) -> str:
    """Extract the largest fenced code block from markdown text."""
    if not text:
        return ""
    blocks = re.findall(r"```[a-zA-Z0-9+\-#]*\n(.*?)\n```", text, re.DOTALL)
    return max(blocks, key=len) if blocks else ""


# --- Results Display ---

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

    route_label = {
        "quick": "Quick",
        "deep": "Deep",
        "security_focused": "Security",
    }.get(atype, "Quick")

    st.divider()

    # Determine complexity category and label for color-coding
    if cpx <= 30:
        cpx_lbl = "Low"
        cpx_delta = "- Good"
    elif cpx <= 60:
        cpx_lbl = "Medium"
        cpx_delta = "Moderate"
    else:
        cpx_lbl = "High"
        cpx_delta = "+ Alert"

    # Metrics Row (native st.metric)
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Health Index", f"{health}%")
    m2.metric("Complexity", f"{cpx}/100 ({cpx_lbl})", delta=cpx_delta, delta_color="inverse")
    m3.metric("Language", lang.upper())
    m4.metric("Route", route_label)
    m5.metric("Time", f"{dur:.1f}s")

    # Pipeline (native st.columns)
    st.markdown(":material/route: **Agent Pipeline:**")
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

    # Tabbed Results
    tab_report, tab_compare, tab_vulns, tab_linter, tab_perf, tab_scores, tab_arch = st.tabs(
        [
            ":material/description: Report",
            ":material/compare: Compare",
            ":material/security: Vulnerabilities",
            ":material/bug_report: Linter (Ruff)",
            ":material/speed: Performance",
            ":material/star: Scores",
            ":material/schema: Architecture",
        ]
    )

    with tab_report:
        if report:
            st.markdown(report)
        else:
            st.info("No report generated.")
        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                "Download Markdown Report",
                report or "",
                "analysis_report.md",
                "text/markdown",
                icon=":material/download:",
                use_container_width=True,
            )
        with col2:
            try:
                pdf_bytes = generate_analysis_pdf(rd)
                st.download_button(
                    "Download PDF Report",
                    pdf_bytes,
                    "analysis_report.pdf",
                    "application/pdf",
                    icon=":material/download:",
                    use_container_width=True,
                )
            except Exception as e:
                st.error(f"Failed to generate PDF: {e}")

    with tab_compare:
        ref = _parse_code_block(
            r.get("code_review", "")
        ) or _parse_code_block(r.get("optimization_report", ""))

        if not ref:
            st.info("No refactored code was returned by the agents.")
        else:
            col_lay, col_num = st.columns([2, 1])
            with col_lay:
                layout = st.radio(
                    ":material/view_column: Comparison Layout",
                    ["Side-by-side", "Unified Diff"],
                    horizontal=True,
                    key="diff_layout_select",
                )
            with col_num:
                show_lines = st.toggle(":material/format_list_numbered: Show line numbers", value=False)

            def _add_line_numbers(text_code: str) -> str:
                lines_list = text_code.splitlines()
                if not lines_list:
                    return ""
                max_w = len(str(len(lines_list)))
                return "\n".join(f"{i+1:>{max_w}} | {line}" for i, line in enumerate(lines_list))

            orig_disp = _add_line_numbers(rd["code"]) if show_lines else rd["code"]
            ref_disp = _add_line_numbers(ref) if show_lines else ref

            if layout == "Side-by-side":
                lc, rc = st.columns(2)
                with lc:
                    st.markdown(":material/edit_document: **Original Code**")
                    st.code(orig_disp, language=lang if lang != "unknown" and not show_lines else "text")
                with rc:
                    st.markdown(":material/auto_fix_high: **Refactored Code**")
                    st.code(ref_disp, language=lang if lang != "unknown" and not show_lines else "text")
            else:
                import difflib
                diff = difflib.unified_diff(
                    rd["code"].splitlines(),
                    ref.splitlines(),
                    fromfile="Original",
                    tofile="Refactored",
                    lineterm="",
                )
                diff_list = list(diff)
                if len(diff_list) >= 2:
                    diff_text = "\n".join(diff_list[2:])
                else:
                    diff_text = "\n".join(diff_list)

                st.markdown(":material/difference: **Unified Diff**")
                st.code(diff_text, language="diff")

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
                icon = {
                    "CRITICAL": ":material/dangerous:",
                    "HIGH": ":material/warning:",
                    "MEDIUM": ":material/report:",
                    "LOW": ":material/info:",
                    "INFO": ":material/help:",
                }.get(sev, ":material/help:")
                with st.container(border=True):
                    vc1, vc2 = st.columns([4, 1])
                    vc1.markdown(f"{icon} **{v['desc']}**")
                    vc1.caption(f"Line {v['line']}")
                    vc2.markdown(f"**{sev}**")

        if sec_text:
            st.divider()
            st.markdown(":material/shield: **Detailed Security Report**")
            st.markdown(sec_text)

    with tab_linter:
        lint_report = r.get("lint_report", "")
        if not lint_report:
            st.info("No linter report available.")
        elif "[PASS]" in lint_report:
            st.success("Ruff Linter: No issues or styling violations detected!")
        elif "[ERROR]" in lint_report:
            st.error(lint_report)
        else:
            st.warning("Ruff Linter: Styling/Bug issues found")
            for line in lint_report.split("\n"):
                if line.strip().startswith("- "):
                    st.markdown(line)
                else:
                    st.caption(line)

    with tab_perf:
        opt = r.get("optimization_report", "")
        if opt:
            st.markdown(opt)
        else:
            st.info(
                "Optimization runs only on deep or security-focused analysis paths."
            )

    with tab_scores:
        st.markdown(":material/scoreboard: **Quality Scorecard**")
        for cat, sc in scores.items():
            st.progress(sc / 100, text=f"{cat}: {sc}%")

        if len(st.session_state.score_history) > 1:
            st.divider()
            st.markdown(":material/trending_up: **Quality Progress Trend**")
            st.line_chart(st.session_state.score_history)

    with tab_arch:
        st.markdown(":material/account_tree: **LangGraph Multi-Agent Architecture**")
        st.caption(":material/visibility: Visual representation of the compiled graph structure and dynamic agent routes:")
        
        # DOT language representation of graph
        graph_dot = """
        digraph G {
            fontname="Helvetica,Arial,sans-serif"
            bgcolor="transparent"
            node [fontname="Helvetica,Arial,sans-serif", shape=box, style="filled,rounded", color="#e5e7eb", fillcolor="#ffffff", penwidth=2]
            edge [fontname="Helvetica,Arial,sans-serif", color="#9ca3af", penwidth=2]
            
            START [shape=circle, fillcolor="#111827", fontcolor="#ffffff", color="#111827"]
            preprocess [label="🔧 Preprocessor\\n(Ruff / Complexity)", fillcolor="#eff6ff", color="#3b82f6"]
            router [label="🔀 Router Agent\\n(LLM Decision)", fillcolor="#f5f3ff", color="#8b5cf6"]
            code_review [label="🔍 Senior Reviewer\\n(Quality Audit)", fillcolor="#ecfdf5", color="#10b981"]
            security [label="🔒 Security Expert\\n(Vulnerabilities)", fillcolor="#fff5f5", color="#ef4444"]
            optimize [label="⚡ Performance Eng.\\n(Execution Speed)", fillcolor="#fffbeb", color="#f59e0b"]
            aggregate [label="📊 Aggregator\\n(Coherent Report)", fillcolor="#f0fdfa", color="#0d9488"]
            END [shape=doublecircle, fillcolor="#111827", fontcolor="#ffffff", color="#111827"]
            
            START -> preprocess
            preprocess -> router
            router -> code_review
            
            code_review -> aggregate [label="Quick Route"]
            code_review -> optimize [label="Deep Route"]
            code_review -> security [label="Security Route"]
            
            security -> optimize
            optimize -> aggregate
            aggregate -> END
        }
        """
        st.graphviz_chart(graph_dot)

# --- History ---

hist = st.session_state.get("history", [])
if len(hist) > 1:
    st.divider()
    st.markdown("#### :material/history: Previous Runs")
    for i, entry in enumerate(reversed(hist[:-1])):
        hl = entry["result"].get("language", "unknown")
        ht = entry["result"].get("analysis_type", "quick")
        he = entry["elapsed"]
        idx = len(hist) - 1 - i
        with st.expander(f"Run #{idx} - {hl.upper()} - {ht} - {he:.1f}s"):
            hr = entry["result"].get("final_report", "")
            if hr:
                st.markdown(hr)
            st.code(
                entry["code"],
                language=hl if hl != "unknown" else "python",
            )