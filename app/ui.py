import streamlit as st
import pandas as pd
import PyPDF2
from search import search_web
from llm_parser import chat_with_web, client as groq_client

st.set_page_config(page_title="Roon AI", page_icon="🚀", layout="wide")

# --- Enhanced Sidebar ---
with st.sidebar:
    st.header("📁 Data Center")
    uploaded_file = st.file_uploader("Upload Data (CSV, Excel, PDF)", type=["csv", "xlsx", "pdf", "txt"])
    
    file_context = ""
    df_preview = None

    if uploaded_file:
        if uploaded_file.name.endswith('.pdf'):
            reader = PyPDF2.PdfReader(uploaded_file)
            file_context = " ".join([page.extract_text() for page in reader.pages[:5]]) # First 5 pages
            st.success("PDF Content Indexed ✅")
        elif uploaded_file.name.endswith(('.csv', '.xlsx')):
            df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
            df_preview = df.describe().to_string() # Statistical Analysis
            file_context = f"File: {uploaded_file.name}. Stats: {df_preview}. Columns: {list(df.columns)}"
            st.success("Data Analyst Mode Active 📊")

# --- The "Decision" Brain ---
def get_ai_response(user_query, history, file_data):
    # System prompt to set the "Gemini-like" personality
    system_prompt = """You are Roon, an elite AI with emotional, mathematical, and coding intelligence.
    - If data is provided, act as a Data Analyst. Perform statistical summaries and reasoning.
    - For coding/math, answer directly using your internal logic.
    - For live news, use web search results.
    - Be concise but deeply insightful."""

    # Decide if we need web search
    needs_search = any(word in user_query.lower() for word in ["news", "price", "today", "weather", "latest"])
    
    context = ""
    if needs_search:
        results = search_web(user_query)
        context = f"Web Search Results: {results}"
    
    full_prompt = f"{system_prompt}\n\nFile Context: {file_data}\n\nUser: {user_query}\nAI:"
    
    res = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile", # Using a larger model for better reasoning
        messages=[{"role": "user", "content": full_prompt}],
        temperature=0.3
    )
    return res.choices[0].message.content

# --- Main Interface ---
st.title("🚀 Roon: Smart Intelligence")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]): st.markdown(msg["content"])

if user_input := st.chat_input("Ask me anything..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"): st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = get_ai_response(user_input, st.session_state.messages, file_context)
            st.markdown(response)
          

# --- The "Decision" Brain ---
def get_ai_response(user_query, history, file_data):
    # Absolutely zero tolerance for AI disclaimers
    system_prompt = """You are a direct data-parser. You do not have opinions. 
    You must read the WEB RESULTS block and output the answer directly.
    NEVER mention a knowledge cutoff. NEVER mention that you are an AI.
    If the WEB RESULTS are empty, reply exactly with: "Search failed. No live data available." """

    search_keywords = [
        "news", "price", "today", "yesterday", "current", "latest", "weather",
        "2024", "2025", "2026", "live", "stock", "petrol"
    ]
    
    needs_search = any(word in user_query.lower() for word in search_keywords)
    
    web_context = ""
    if needs_search:
        try:
            raw_results = search_web(user_query)
            
            cleaned_results = []
            for res in raw_results:
                if isinstance(res, dict):
                    content = res.get('content', '') or res.get('snippet', '')
                    cleaned_results.append(f"- {content}")
            
            if cleaned_results:
                web_context = "\n\n--- WEB RESULTS ---\n" + "\n".join(cleaned_results)
                # THIS WILL SHOW UP ON YOUR SCREEN:
                st.info(f"🔍 Search Success! Passing this to AI:\n {web_context[:200]}...") 
            else:
                web_context = "\n\n--- WEB RESULTS ---\nEMPTY"
                # THIS WILL SHOW UP ON YOUR SCREEN:
                st.warning("⚠️ Search returned empty! Check your Tavily API key.")
        except Exception as e:
            web_context = "\n\n--- WEB RESULTS ---\nEMPTY"
            st.error(f"❌ Search Error: {str(e)}")
    
    full_prompt = f"{system_prompt}\n\nFile Context: {file_data}{web_context}\n\nUser Question: {user_query}\nAnswer:"
    
    res = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": full_prompt}],
        temperature=0.0 # 0.0 forces strict logic, zero creativity
    )
    return res.choices[0].message.content
