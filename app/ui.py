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
                # OPTION 2: Limiting to 2 pages to stay under 12k token limit
                text = "".join([page.extract_text() for page in pdf_reader.pages[:2]])
                file_context = f"--- PDF SUMMARY (First 2 Pages) ---\n{text}"
                st.success(f"PDF context limited for speed ✅")
            
            elif uploaded_file.name.endswith(('.csv', '.xlsx')):
                df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
                # Limiting stats to prevent token overflow
                stats = df.describe().to_string()
                cols = list(df.columns)[:15] # Limit column list
                file_context = f"--- DATASET STATS ---\nColumns: {cols}\n\nStats:\n{stats}"
                st.success(f"Analyst Mode Active (Partial Data) 📊")
            
            elif uploaded_file.name.endswith('.txt'):
                # Read only first 5000 characters
                file_context = f"--- TXT SNIPPET ---\n{uploaded_file.read(5000).decode('utf-8')}"
                st.success("Text snippet loaded ✅")
        except Exception as e:
            st.error(f"File Error: {e}")

# --- THE OMNI-BRAIN LOGIC ---
def get_omni_response(user_query, history, file_data):
    system_instr = "You are Roon, an elite AI. Use FILE DATA for analysis and WEB CONTEXT for live updates. For coding/math, use your own reasoning."

    # Skip search for greetings
    web_data = ""
    is_basic = any(word in user_query.lower() for word in ["hi", "hello", "hey"])
    
    if not is_basic:
        try:
            results = search_web(user_query)
            if results:
                web_data = f"\n\nWEB CONTEXT: {results}"
        except:
            pass

    content = f"{system_instr}\n\nFILE DATA: {file_data}\n{web_data}\n\nUSER: {user_query}"

    try:
        # Using Llama 3.3 70B with truncated data to avoid the 12k TPM limit
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": content}],
            temperature=0.2,
            max_tokens=1024 # Reduced to keep total response within limits
        )
        return response.choices[0].message.content
    except Exception as e:
        # Friendly error handling for Rate Limits
        if "413" in str(e) or "rate_limit" in str(e).lower():
            return "⚠️ **Limit Reached:** The uploaded file is too large for the 70B model's free tier. Please try a smaller file or ask a question without the file context."
        return f"⚠️ **Groq API Error:** {str(e)}"

# --- MAIN UI ---
st.title("🚀 Roon: Smart Intelligence")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if user_input := st.chat_input("Ask about IPL, coding, or your files..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Analyzing..."):
            ai_output = get_omni_response(user_input, st.session_state.messages, file_context)
            st.markdown(ai_output)
    
    st.session_state.messages.append({"role": "assistant", "content": ai_output})
