import streamlit as st
import pandas as pd
import PyPDF2
import io
from search import search_web
from llm_parser import client as groq_client

# 1. PAGE CONFIGURATION
st.set_page_config(page_title="Roon: Smart Intelligence", page_icon="🚀", layout="wide")

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    .stSidebar { background-color: #161b22; border-right: 1px solid #30363d; }
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
                pdf_reader = PyPDF2.PdfReader(uploaded_file)
                text = "".join([page.extract_text() for page in pdf_reader.pages[:10]])
                file_context = f"--- PDF CONTENT ({uploaded_file.name}) ---\n{text}"
                st.success(f"PDF indexed ✅")
            
            elif uploaded_file.name.endswith(('.csv', '.xlsx')):
                df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
                stats = df.describe(include='all').to_string()
                file_context = f"--- DATASET SUMMARY ---\nColumns: {list(df.columns)}\n\nStats:\n{stats}"
                st.success(f"Analyst Mode Active 📊")
            
            elif uploaded_file.name.endswith('.txt'):
                file_context = f"--- TXT CONTENT ---\n{uploaded_file.read().decode('utf-8')}"
                st.success("Text loaded ✅")
        except Exception as e:
            st.error(f"File Error: {e}")

# --- THE OMNI-BRAIN LOGIC ---
def get_omni_response(user_query, history, file_data):
    # 1. Simplified System Instruction
    system_instr = "You are Roon, a smart AI. Use FILE DATA for analysis and WEB CONTEXT for live updates. For coding/math, use your own reasoning."

    # 2. Universal Search (Skips basic greetings)
    web_data = ""
    is_basic = any(word in user_query.lower() for word in ["hi", "hello", "hey"])
    
    if not is_basic:
        try:
            results = search_web(user_query)
            if results:
                web_data = f"\n\nWEB CONTEXT: {results}"
        except:
            pass

    # 3. Assemble Prompt
    content = f"{system_instr}\n\nFILE DATA: {file_data}\n{web_data}\n\nUSER: {user_query}"

    # 4. API Call with Exception Handling to prevent crashes
    try:
        # llama3-70b-8192 is the most stable model for high-reasoning tasks
    
        # UPDATED: Use the current supported production model
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile", 
            messages=[{"role": "user", "content": content}],
            temperature=0.2,
            max_tokens=2048
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"⚠️ **Groq API Error:** {str(e)}\n\n*Check your API key or Rate Limits in Streamlit Secrets.*"

# --- MAIN UI ---
st.title("🚀 Roon: Smart Intelligence")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Input logic
if user_input := st.chat_input("Ask me about IPL scores, code, or your files..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Processing..."):
            ai_output = get_omni_response(user_input, st.session_state.messages, file_context)
            st.markdown(ai_output)
    
    st.session_state.messages.append({"role": "assistant", "content": ai_output})
