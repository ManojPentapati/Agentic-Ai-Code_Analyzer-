# 💻 Agentic AI Code Analyzer

An intelligent **Code Analyzer Chatbot** built with **LangGraph**, **LangChain**, and **Streamlit**. Paste any code snippet and get a detailed AI-powered analysis including bug detection, optimization suggestions, and best practice recommendations.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.x-FF4B4B?logo=streamlit&logoColor=white)
![LangGraph](https://img.shields.io/badge/LangGraph-Agentic_AI-green)
![Groq](https://img.shields.io/badge/Groq-LLaMA_3.1-orange)

---

## 🚀 Features

- **Code Explanation** — Understand what a code snippet does at a glance.
- **Syntax Error Detection** — Identify syntax issues in your code.
- **Logical Bug Finder** — Spot logical errors and edge cases.
- **Optimization Suggestions** — Get performance improvement tips.
- **Best Practices** — Receive coding standard recommendations.
- **Conversation History** — Review past analyses in the same session.

---

## 🏗️ Architecture

The application uses a **LangGraph** agentic workflow with a stateful graph:

```
START → create_prompt → generate_response → END
```

| Component | Description |
|---|---|
| **LLM** | Groq's `llama-3.1-8b-instant` model |
| **Agent** | LangChain agent with code analysis tools |
| **State Graph** | LangGraph `StateGraph` for agentic workflow |
| **Frontend** | Streamlit interactive web UI |

---

## 📦 Tech Stack

- **[LangGraph](https://github.com/langchain-ai/langgraph)** — Agentic AI workflow orchestration
- **[LangChain](https://github.com/langchain-ai/langchain)** — LLM framework and tooling
- **[Groq](https://groq.com/)** — Ultra-fast LLM inference (LLaMA 3.1)
- **[Streamlit](https://streamlit.io/)** — Interactive web application framework
- **[python-dotenv](https://github.com/theskumar/python-dotenv)** — Environment variable management

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

- **Windows:**
  ```bash
  .venv\Scripts\activate
  ```
- **macOS / Linux:**
  ```bash
  source .venv/bin/activate
  ```

### 3. Install dependencies

```bash
pip install streamlit langchain langchain-groq langgraph python-dotenv
```

### 4. Set up environment variables

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key_here
```

> 💡 Get your free API key from [Groq Console](https://console.groq.com/).

### 5. Run the application

```bash
streamlit run code_analyzer_app.py
```

The app will open in your browser at `http://localhost:8501`.

---

## 🎯 Usage

1. **Paste** your code snippet into the text area.
2. **Click** the "Analyze Code" button.
3. **Review** the detailed analysis including:
   - What the code does
   - Syntax errors found
   - Logical bugs detected
   - Optimization suggestions
   - Best practice recommendations
4. **Scroll down** to view your conversation history.

---

## 📁 Project Structure

```
Agentic-Ai-Code_Analyzer-/
├── code_analyzer_app.py   # Main application (UI + LangGraph workflow)
├── .env                   # Environment variables (not tracked)
├── .gitignore             # Git ignore rules
└── README.md              # Project documentation
```

---

## 🤝 Contributing

Contributions are welcome! Feel free to:

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
