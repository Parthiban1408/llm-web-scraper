import streamlit as st
import pandas as pd
from search import search_web
from llm_parser import chat_with_web, client as groq_client

# 1. Page Configuration (Must be first)
st.set_page_config(page_title="Roon", page_icon="🚀", layout="wide")

# --- CUSTOM UI STYLING ---
st.markdown("""
    <style>
    .stApp {
        background-color: #0e1117;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR: FILE UPLOADER ---
with st.sidebar:
    st.header("📂 Data Center")
    uploaded_file = st.file_uploader("Upload a file (CSV, Excel, TXT)", type=["csv", "xlsx", "txt"])
    
    df = None
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            st.success(f"Loaded: {uploaded_file.name} ✅")
        except Exception as e:
            st.error(f"Error loading file: {e}")

    st.divider()
    st.info("💡 **Tip:** Ask about market news or your uploaded data.")

# --- MAIN APP INTERFACE ---
st.title("🚀 AI Budd: Smart Search")

def contextualize_search(query, history):
    q = query.lower().strip()
    if q in ["hi", "hello", "thanks", "ok"]: return None
    if len(history) > 1:
        prompt = f"History: {history[-3:]}\nFollow-up: {query}\nStandalone search query:"
        res = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        return res.choices[0].message.content.strip()
    return query

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display Chat History
for msg in st.session_state.messages:
    icon = "👤" if msg["role"] == "user" else "🤖"
    with st.chat_message(msg["role"], avatar=icon):
        st.markdown(msg["content"])

# --- CHAT INPUT & LOGIC ---
if user_input := st.chat_input("Ask about IPL 2026 or your files..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar="👤"):
        st.markdown(user_input)

    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("Processing..."):
            # A. If file is uploaded and user asks about it
            if df is not None and ("file" in user_input.lower() or "explain" in user_input.lower()):
                response = f"I've analyzed **{uploaded_file.name}**. It contains {len(df)} rows and {len(df.columns)} columns: {', '.join(df.columns.tolist())}."
            
            # B. Default to Web Search
            else:
                try:
                    search_query = contextualize_search(user_input, [m["content"] for m in st.session_state.messages])
                    if search_query:
                        search_results = search_web(search_query)
                        # Only call parser if results exist to avoid TypeError
                        if search_results:
                            response = chat_with_web(user_input, search_results)
                        else:
                            response = "I couldn't find any specific live data for that. Anything else?"
                    else:
                        response = "Hello! I'm ready to help with searches or file analysis."
                except Exception as e:
                    response = f"Search Error: {str(e)}"

            st.markdown(response)
    
    st.session_state.messages.append({"role": "assistant", "content": response})
