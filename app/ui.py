import streamlit as st
import pandas as pd
from search import search_web
from llm_parser import chat_with_web, client as groq_client

# 1. Page Configuration
st.set_page_config(page_title="Roon", page_icon="🚀", layout="wide")

# --- CUSTOM UI STYLING ---
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; }
    .stChatMessage { border-radius: 15px; margin-bottom: 10px; }
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
    # Only try to contextualize if there is actual history
    if len(history) < 1:
        return query
    
    q_lower = query.lower().strip()
    if q_lower in ["hi", "hello", "thanks", "ok"]: 
        return None
        
    try:
        prompt = f"History: {history[-3:]}\nFollow-up: {query}\nConvert this into a single standalone Google search query:"
        res = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        return res.choices[0].message.content.strip()
    except:
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
    # Show user message immediately
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar="👤"):
        st.markdown(user_input)

    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("Processing..."):
            response = ""
            
            # A. If file is uploaded and user asks about it
            if df is not None and ("file" in user_input.lower() or "explain" in user_input.lower() or "data" in user_input.lower()):
                response = f"I've analyzed **{uploaded_file.name}**. It contains {len(df)} rows and {len(df.columns)} columns. The columns are: {', '.join(df.columns.tolist())}. What would you like to know about this data?"
            
            # B. Default to Web Search
            else:
                try:
                    # Get the refined search term
                    search_term = contextualize_search(user_input, [m["content"] for m in st.session_state.messages[:-1]])
                    
                    if search_term:
                        results = search_web(search_term)
                        if results and len(results) > 0:
                            response = chat_with_web(user_input, results)
                        else:
                            response = f"I searched for '{search_term}' but couldn't find any live results. Please try a different topic."
                    else:
                        response = "Hello! I'm ready to help with searches or file analysis."
                except Exception as e:
                    response = f"I encountered an error: {str(e)}"

            st.markdown(response)
    
    st.session_state.messages.append({"role": "assistant", "content": response})
