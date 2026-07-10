"""Streamlit UI for the Agentic AI Code Analyzer."""

import pathlib
import time
import re
import streamlit as st

from config import AppConfig, AVAILABLE_MODELS, DEFAULT_MODEL, logger
from state import create_initial_state
from graph import build_workflow
from pdf_generator import generate_analysis_pdf

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
    st.caption("Multi-agent code review, security analysis & performance optimization")
with top_right:
    st.metric("Total Runs", len(st.session_state.history))

st.divider()

# --- Settings Row ---

cloned_dir = None
selected_git_file = None
git_url = ""

with st.expander(":material/settings: Settings & Configuration"):
    c1, c2, c3 = st.columns(3)
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

    st.divider()

    c4, c5 = st.columns(2)
    with c4:
        uploaded_file = st.file_uploader(
            "Upload code file",
            type=["py", "js", "ts", "rs", "go", "cpp", "c", "java", "sql", "html", "css"],
        )
    with c5:
        git_url = st.text_input(
            "Clone public Git Repository URL",
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
    st.markdown("**Load a template**")
    tpl = st.selectbox(
        "template_select",
        list(TEMPLATES.keys()),
        label_visibility="collapsed",
    )
    if tpl != "-- Select a template --":
        initial_code = TEMPLATES[tpl]

    st.markdown("---")
    st.markdown(f"**Model:** {AVAILABLE_MODELS[selected_model]}")
    st.markdown(f"**Temp:** {temperature}  |  **Tokens:** {max_tokens}")

with col_code:
    user_code = st.text_area(
        "Paste your code here",
        value=initial_code,
        height=260,
        placeholder="Paste code here, or pick a template from the right panel",
    )

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

            bar = st.progress(0, text="Preparing...")
            t0 = time.time()

            try:
                steps = [
                    (15, "Running static analysis tools..."),
                    (30, "Routing to specialists..."),
                    (55, "Code review in progress..."),
                    (75, "Security and performance scan..."),
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

# --- Helpers ---


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

    # Metrics Row (native st.metric)
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Health Index", f"{health}%")
    m2.metric("Complexity", f"{cpx}/100")
    m3.metric("Language", lang.upper())
    m4.metric("Route", route_label)
    m5.metric("Time", f"{dur:.1f}s")

    # Pipeline (native st.columns)
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

    # Tabbed Results
    tab_report, tab_compare, tab_vulns, tab_linter, tab_perf, tab_scores = st.tabs(
        [
            ":material/description: Report",
            ":material/compare: Compare",
            ":material/security: Vulnerabilities",
            ":material/bug_report: Linter (Ruff)",
            ":material/speed: Performance",
            ":material/star: Scores",
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
            layout = st.radio(
                "Comparison Layout",
                ["Side-by-side", "Unified Diff"],
                horizontal=True,
                key="diff_layout_select",
            )

            if layout == "Side-by-side":
                lc, rc = st.columns(2)
                with lc:
                    st.markdown("**Original Code**")
                    st.code(rd["code"], language=lang if lang != "unknown" else "python")
                with rc:
                    st.markdown("**Refactored Code**")
                    st.code(ref, language=lang if lang != "unknown" else "python")
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

                st.markdown("**Unified Diff**")
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
            st.markdown("**Detailed Security Report**")
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
        st.markdown("**Quality Scorecard**")
        for cat, sc in scores.items():
            st.progress(sc / 100, text=f"{cat}: {sc}%")

# --- History ---

hist = st.session_state.get("history", [])
if len(hist) > 1:
    st.divider()
    st.markdown("#### Previous Runs")
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