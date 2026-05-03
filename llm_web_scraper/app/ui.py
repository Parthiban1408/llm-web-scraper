import streamlit as st
from search import search_web
from llm_parser import chat_with_web, client as groq_client

# 1. This must remain the first 'st.' command
st.set_page_config(page_title="Roon", page_icon="🚀", layout="wide")

# --- CUSTOM CSS FOR COLOR ---aa
st.markdown("""
    <style>
    .main {
        background-color: #f0f2f6;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        border-radius: 10px;
    }
    .stTextInput>div>div>input {
        border: 2px solid #4CAF50;
    }
    </style>
    """, unsafe_access=True)

# --- SIDEBAR FOR FILE UPLOAD ---
with st.sidebar:
    st.header("📂 Data Center")
    uploaded_file = st.file_uploader("Upload a file (CSV, Excel, TXT)", type=["csv", "xlsx", "txt"])
    
    if uploaded_file is not None:
        st.success(f"Successfully uploaded: {uploaded_file.name} ✅")
        # You can add logic here to process the file (e.g., pd.read_csv)

    st.divider()
    st.info("💡 **Tip:** Use the search bar to ask about live market data or your uploaded files.")

# --- MAIN UI ---
st.title("🚀 AI Budd: Smart Search")
st.subheader("Your AI-powered assistant for live data and file analysis.")

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

# Display History with Icons
for msg in st.session_state.messages:
    icon = "👤" if msg["role"] == "user" else "🤖"
    with st.chat_message(msg["role"], avatar=icon):
        st.markdown(msg["content"])

# Chat Input
if user_input := st.chat_input("Ask about IPL 2026 or your files..."):
    # ... rest of your search logic from your previous ui.py ...
    pass