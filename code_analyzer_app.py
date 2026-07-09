import os
import streamlit as st
from typing import TypedDict, Annotated
from operator import add
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain.tools import tool
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langgraph.graph import StateGraph, START, END

load_dotenv()
# ==============================
# API KEY
# ==============================

api_key = os.getenv("GROQ_API_KEY")
# print("Api Key:",api_key)

# OR replace with your key if testing
# api_key = "YOUR_GROQ_API_KEY"

if not api_key:
    st.error("GROQ_API_KEY is not set.")
    st.stop()

# ==============================
# LLM
# ==============================

llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0,
    api_key=api_key,
)

# ==============================
# STATE
# ==============================

class CodeState(TypedDict):
    query: str
    context: str
    messages: Annotated[list[BaseMessage], add]
    response: str

# ==============================
# HELPER FUNCTION
# ==============================

def analyze_code_context(query: str) -> str:
    return f"Analyzing the following code:\n\n{query}"

# ==============================
# TOOLS
# ==============================

@tool
def get_code_analysis_guidance(query: str) -> str:
    """
    Gives guidance for analyzing code.
    """
    return (
        "Analyze syntax, logical errors, readability, "
        "performance, coding standards, and best practices."
    )

tools = [get_code_analysis_guidance]

# ==============================
# AGENT
# ==============================

agent = create_agent(
    model=llm,
    tools=tools,
    system_prompt="""
You are an expert code reviewer.

For every code snippet:

1. Explain what the code does.
2. Find syntax errors.
3. Find logical bugs.   
4. Suggest optimizations.
5. Suggest better coding practices.
6. Explain everything clearly.
"""
)

# ==============================
# GRAPH NODES
# ==============================

def create_prompt_node(state: CodeState):

    query = state["query"]

    context = analyze_code_context(query)

    prompt = f"""
Context:
{context}

User Code:

{query}
"""

    return {
        **state,
        "context": context,
        "messages": [HumanMessage(content=prompt)]
    }


def generate_response_node(state: CodeState):

    response = agent.invoke(
        {
            "messages": state["messages"]
        }
    )

    if isinstance(response, dict):

        if "messages" in response:

            response_text = response["messages"][-1].content

        else:

            response_text = str(response)

    else:

        response_text = str(response)

    return {
        **state,
        "response": response_text,
        "messages": state["messages"]
        + [AIMessage(content=response_text)],
    }

# ==============================
# GRAPH
# ==============================

def build_graph():

    graph = StateGraph(CodeState)

    graph.add_node("create_prompt", create_prompt_node)

    graph.add_node("generate_response", generate_response_node)

    graph.add_edge(START, "create_prompt")

    graph.add_edge("create_prompt", "generate_response")

    graph.add_edge("generate_response", END)

    return graph.compile()

workflow = build_graph()

# ==============================
# STREAMLIT UI
# ==============================

st.set_page_config(
    page_title="Code Analyzer",
    page_icon="💻",
    layout="wide",
)

st.title("💻 Code Analyzer Chatbot")
st.write("Paste your code below and receive a detailed analysis.")

if "conversation" not in st.session_state:
    st.session_state.conversation = []

user_code = st.text_area(
    "Paste your code here",
    height=300,
)

if st.button("Analyze Code"):

    if not user_code.strip():

        st.warning("Please paste some code first.")

    else:

        with st.spinner("Analyzing..."):

            initial_state = {
                "query": user_code,
                "context": "",
                "messages": [],
                "response": "",
            }

            result = workflow.invoke(initial_state)

            bot_response = result["response"]

            st.session_state.conversation.append(
                {
                    "user": user_code,
                    "bot": bot_response,
                }
            )

        st.success("Analysis Completed!")

        st.subheader("Your Code")

        st.code(user_code, language="python")

        st.subheader("Analysis")

        st.write(bot_response)

        with st.expander("Context Used"):

            st.write(result.get("context"))

# ==============================
# HISTORY
# ==============================

if st.session_state.conversation:

    st.divider()

    st.subheader("Conversation History")

    for chat in reversed(st.session_state.conversation):

        st.code(chat["user"], language="python")

        st.write(chat["bot"])

        st.divider()