# 🧠 Agentic AI Code Analyzer

A production-grade, **multi-agent AI system** built with **LangGraph** that performs intelligent code analysis using specialized agents for code review, security scanning, and performance optimization.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.45+-FF4B4B?logo=streamlit&logoColor=white)
![LangGraph](https://img.shields.io/badge/LangGraph-Multi_Agent-green)
![Groq](https://img.shields.io/badge/Groq-LLaMA_3.3-orange)
![CI/CD](https://github.com/ManojPentapati/Agentic-Ai-Code_Analyzer-/actions/workflows/ci.yml/badge.svg)

---

## 🚀 Features

- **Multi-Agent Architecture** — Specialized agents for code review, security, and optimization.
- **Intelligent Routing** — Automatically selects analysis depth (Quick / Deep / Security-Focused).
- **5 Functional Tools** — Language detection, complexity scoring, security scanning, pattern checking, and Ruff linter.
- **📄 PDF Report Export** — Download styled code audits with scorecards and metrics tables.
- **🔍 Interactive Code Diff** — Compare original vs. refactored code line-by-line with red (-) and green (+) annotations.
- **🛡️ Dynamic Ruff Linting** — Run ruff check on python files to catch syntax and PEP 8 issues during preprocessing.
- **📦 Git Repository URL Support** — Clone public repositories and index their source files to select and analyze them.
- **⚡ Live Agentic Console (`st.status`)** — Dynamic execution logs detailing active node executions and results.
- **📊 Complexity Color-Coded Gauge** — Color-coded indicators showing Low, Medium, and High complexity levels.
- **📄 Code Panel Line Numbers** — Prepend toggleable line numbers to the comparison panel blocks.
- **🚀 CI/CD Pipeline** — GitHub Actions configuration running Ruff linter check on git pushes.
- **Rich State Management** — TypedDict state with metadata, scores, and per-agent outputs.
- **Premium Streamlit UI** — Modern, clean tabbed interface with metrics dashboard, diff views, and session history.
- **Multi-Model Support** — Switch between LLaMA 3.1 8B, LLaMA 3.3 70B, Gemma 2, and Mixtral.

---

## 🏗️ Architecture

```mermaid
graph TD
    A[START] --> B[🔧 Preprocess & Ruff Lint]
    B --> C[🔀 Router Agent]
    C --> B1[Linear transitions]
    B1 --> D[🔍 Code Review]
    D -->|quick| G[📊 Aggregator]
    D -->|deep| F[⚡ Optimization]
    D -->|security_focused| E[🔒 Security]
    E --> F
    F --> G
    G --> H[END]
```

### Agent Roles

| Agent | Role |
|---|---|
| **Preprocessor** | Runs tools: language detection, complexity scoring, security scanning, pattern checking, and Ruff linter |
| **Router** | Analyzes tool results and decides analysis path (quick / deep / security_focused) |
| **Code Review** | Deep code review: bugs, logic errors, readability, best practices, refactored code |
| **Security** | Vulnerability analysis: injection, secrets, OWASP Top 10, secure code rewrites |
| **Optimization** | Performance: time/space complexity, data structures, caching, async patterns |
| **Aggregator** | Combines all specialist reports into a scored, prioritized final report |

---

## 📦 Tech Stack

| Technology | Purpose |
|---|---|
| [LangGraph](https://github.com/langchain-ai/langgraph) | Multi-agent workflow orchestration with conditional routing |
| [LangChain](https://github.com/langchain-ai/langchain) | LLM framework, tools, and prompt management |
| [Groq](https://groq.com/) | Ultra-fast LLM inference (LLaMA 3.1, 3.3, Gemma 2, Mixtral) |
| [Streamlit](https://streamlit.io/) | Interactive web application with premium UI |
| [FPDF2](https://github.com/py-pdf/fpdf2) | PDF document generation |
| [Ruff](https://github.com/astral-sh/ruff) | Ultra-fast Python linter |
| [python-dotenv](https://github.com/theskumar/python-dotenv) | Environment variable management |

---

## 📁 Project Structure

```
Agentic-Ai-Code_Analyzer-/
├── .github/workflows/   
│   └── ci.yml           # GitHub Actions automated lint pipeline
├── .streamlit/
│   └── config.toml      # Forced light theme configurations
├── app.py               # Streamlit entry point — premium UI with tabs & metrics
├── pdf_generator.py     # PDF audit compiler using fpdf2
├── style.css            # Custom CSS style accents
├── config.py            # Configuration, LLM factory, logging, multi-model support
├── state.py             # Rich state schema (TypedDict) for the LangGraph workflow
├── tools.py             # 5 functional tools: language, complexity, security, patterns, ruff
├── agents.py            # 5 specialized agent chains with expert system prompts
├── graph.py             # LangGraph workflow builder with static/dynamic routing
├── requirements.txt     # Pinned dependencies
├── .env                 # API keys (not tracked)
├── .gitignore           # Git ignore rules
└── README.md            # This file
```

---

## ⚙️ Setup & Installation

### 1. Clone the repository

```bash
git clone https://github.com/ManojPentapati/Agentic-Ai-Code_Analyzer-.git
cd Agentic-Ai-Code_Analyzer-
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

**Activate it:**

- **Windows:** `.venv\Scripts\activate`
- **macOS / Linux:** `source .venv/bin/activate`

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up environment variables

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key_here
```

> 💡 Get your free API key from [Groq Console](https://console.groq.com/).

### 5. Run the application

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`.

---

## 🎯 How It Works

1. **Paste** your code or **select** a template, or **upload** a source file.
2. Alternatively, enter a **Git Repository URL**, clone it, and select a file directly from the repo.
3. **Configure** model, temperature, and max tokens in settings.
4. **Click** "Run Analysis"
5. The system automatically:
   - Detects the programming language
   - Calculates code complexity (0-100)
   - Runs a security scan and Python syntax/style checking via **Ruff** linter
   - Routes to the appropriate analysis depth
   - Runs specialized agents in sequence
   - Aggregates results into a scored final report
6. **Review** results across tabs: Report, Compare, Vulnerabilities, Linter (Ruff), Performance, Scores, and Architecture.
7. **Download** the report as a Markdown file or export it as a styled **PDF**.

---

## 🔀 Routing Logic

| Condition | Route | Agents Executed |
|---|---|---|
| Security scan finds HIGH/CRITICAL issues | `security_focused` | Code Review → Security → Optimization → Aggregator |
| Complexity ≥ 40 or 3+ functions | `deep` | Code Review → Optimization → Aggregator |
| Simple code | `quick` | Code Review → Aggregator |

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Commit your changes (`git commit -m 'Add new feature'`)
4. Push to the branch (`git push origin feature/new-feature`)
5. Open a Pull Request

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

---

## 👤 Author

**Manoj Pentapati**

- GitHub: [@ManojPentapati](https://github.com/ManojPentapati)

---

> ⭐ If you found this project helpful, give it a star on GitHub!
