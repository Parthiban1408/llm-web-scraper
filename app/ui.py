import streamlit as st
import pandas as pd
import PyPDF2
import io
from search import search_web
from llm_parser import chat_with_web, client as groq_client

# 1. PAGE CONFIGURATION
st.set_page_config(page_title="Roon: Smart Intelligence", page_icon="🚀", layout="wide")

# --- CUSTOM CSS FOR MODERN LOOK ---
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    .stChatMessage { border-radius: 15px; margin-bottom: 15px; border: 1px solid #30363d; }
    .stSidebar { background-color: #161b22; border-right: 1px solid #30363d; }
    div.stButton > button:first-child {
        background-color: #238636; color: white; border: none; width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR: DATA ANALYST CENTER ---
with st.sidebar:
    st.header("📁 Data Center")
    uploaded_file = st.file_uploader("Upload Data (CSV, Excel, PDF, TXT)", type=["csv", "xlsx", "pdf", "txt"])
    
    file_context = ""
    
    if uploaded_file:
        try:
            if uploaded_file.name.endswith('.pdf'):
                # PDF Extraction
                pdf_reader = PyPDF2.PdfReader(uploaded_file)
                text = ""
                for page in pdf_reader.pages[:10]: # Limit to first 10 pages for speed
                    text += page.extract_text()
                file_context = f"--- PDF CONTENT ({uploaded_file.name}) ---\n{text}"
                st.success(f"PDF indexed: {uploaded_file.name} ✅")
            
            elif uploaded_file.name.endswith(('.csv', '.xlsx')):
                # Excel/CSV Statistical Analysis
                df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
                stats = df.describe(include='all').to_string()
                cols = list(df.columns)
                head = df.head(5).to_string()
                file_context = f"--- DATASET SUMMARY ({uploaded_file.name}) ---\nColumns: {cols}\n\nStats:\n{stats}\n\nTop 5 Rows:\n{head}"
                st.success(f"Data Analyst Mode Active 📊")
            
            elif uploaded_file.name.endswith('.txt'):
                file_context = f"--- TXT CONTENT ---\n{uploaded_file.read().decode('utf-8')}"
                st.success("Text file loaded ✅")
        
        except Exception as e:
            st.error(f"Error processing file: {e}")

    st.divider()
    st.markdown("### Capabilities\n* **Live Web Data** (IPL, News, Prices)\n* **Data Analyst** (Excel/CSV Stats)\n* **Coding & Math** (Logic & Reasoning)\n* **PDF Summary** (Document Intelligence)")

# --- THE OMNI-BRAIN LOGIC ---
def get_omni_response(user_query, history, file_data):
    """
    Combines web data, file context, and high-level reasoning.
    """
    # 1. System Persona
    system_prompt = """You are Roon, an elite AI.
    - REASONING: Use internal logic for coding (Python, SQL), math, and general philosophy.
    - ANALYSIS: If 'FILE DATA' is present, act as a professional Data Analyst or Document Expert.
    - LIVE DATA: If 'WEB CONTEXT' is present, use it to provide real-time updates (scores, news, current events).
    - PERSONALITY: Emotionally intelligent, grounded, and helpful. Always cite web sources if used."""

    # 2. Universal Search (Always active for non-basic chat)
    web_data = ""
    is_basic = any(word in user_query.lower() for word in ["hi ", "hello", "hey", "who are you"])
    
    if not is_basic:
        try:
            # We fetch web results for every query to ensure the AI has 'live eyes'
            search_results = search_web(user_query)
            if search_results:
                web_data = f"\n\n--- LIVE WEB CONTEXT ---\n{search_results}"
        except:
            web_data = "\n(Note: Live web search was temporarily unavailable.)"

    # 3. Assemble the Intelligence Prompt
    final_prompt = f"""
    {system_prompt}
    
    FILE DATA: {file_data if file_data else "No file currently uploaded."}
    {web_data}
    
    CHAT HISTORY: {history[-3:] if history else "Start of conversation."}
    
    USER QUERY: {user_query}
    """

# 4. Process with a high-capacity reasoning model
    response = groq_client.chat.completions.create(
        model="llama3-70b-8192", # Try this exact spelling first
        messages=[{"role": "user", "content": final_prompt}],
        temperature=0.3
    )
    return response.choices[0].message.content

# --- MAIN UI ---
st.title("🚀 Roon: Smart Intelligence")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Render chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input
if user_input := st.chat_input("Ask about IPL scores, SQL code, or your uploaded files..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar="👤"):
        st.markdown(user_input)

    # Generate and add assistant response
    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("Thinking..."):
            ai_output = get_omni_response(user_input, st.session_state.messages, file_context)
            st.markdown(ai_output)
    
    st.session_state.messages.append({"role": "assistant", "content": ai_output})
