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
    """, unsafe_allow_html=True)

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

# --- CHAT LOGIC ---
if user_input := st.chat_input("Ask about IPL 2026 or your files..."):
    # 1. Display user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar="👤"):
        st.markdown(user_input)

    # 2. Process Answer
    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("Thinking..."):
            # Contextualize query based on history
            search_query = contextualize_search(user_input, [m["content"] for m in st.session_state.messages])
            
            # Get search results
            if search_query:
                search_results = search_web(search_query)
                # Generate response using your parser logic
                response = chat_with_web(user_input, search_results)
            else:
                # Basic response for casual "Hi/Hello"
                response = "Hello! How can I help you today?"

            st.markdown(response)
    
    # 3. Store assistant response
    st.session_state.messages.append({"role": "assistant", "content": response})
