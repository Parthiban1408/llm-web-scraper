import streamlit as st
import pandas as pd
import PyPDF2
from groq import Groq
from tavily import TavilyClient
import io

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Roon AI - Assitant bud", layout="wide")

try:
    groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    tavily_client = TavilyClient(api_key=st.secrets["TAVILY_API_KEY"])
except Exception as e:
    st.error("Missing API Keys in secrets.toml")
    st.stop()

# --- 2. FILE PROCESSING FUNCTIONS ---
def process_file(uploaded_file):
    """Extracts text or data from Excel/PDF."""
    try:
        if uploaded_file.name.endswith('.xlsx') or uploaded_file.name.endswith('.xls'):
            df = pd.read_excel(uploaded_file)
            return f"Excel Data Summary:\n{df.head(20).to_string()}" # Send first 20 rows
        elif uploaded_file.name.endswith('.pdf'):
            pdf_reader = PyPDF2.PdfReader(uploaded_file)
            text = ""
            for page in pdf_reader.pages[:5]: # Limit to first 5 pages for context window
                text += page.extract_text()
            return f"PDF Content:\n{text}"
        elif uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
            return f"CSV Data Summary:\n{df.head(20).to_string()}"
    except Exception as e:
        return f"Error reading file: {e}"
    return ""

# --- 3. WEB SEARCH ---
def search_web(query):
    response = tavily_client.search(query=query, search_depth="basic", max_results=3)
    return response['results']

# --- 4. SIDEBAR (Data Scientist Mode) ---
with st.sidebar:
    st.title("📂 File uploader")
    uploaded_file = st.file_uploader("Upload Excel, PDF, or CSV", type=["xlsx", "xls", "pdf", "csv"])
    
    file_context = ""
    if uploaded_file:
        with st.spinner("Processing file..."):
            file_context = process_file(uploaded_file)
            st.success(f"Loaded: {uploaded_file.name}")
            if "Excel Data" in file_context or "CSV" in file_context:
                st.info("AI can now see the top rows of your data.")

# --- 5. AI LOGIC ---

def get_ai_response(user_query, history, file_context):
    # Base instructions for the AI
    system_message = {
        "role": "system",
        "content": f"""You are Roon, a high-level Data Scientist and Research AI.
        
        FILE DATA: {file_context if file_context else "No file uploaded."}
        
        INSTRUCTIONS:
        1. If the user asks about the uploaded file, prioritize the FILE DATA.
        2. If the user asks for current prices or news, use the WEB RESULTS provided.
        3. NEVER mention a 'knowledge cutoff'. Be the expert."""
    }

    # Prepare search context if needed
    search_keywords = ["price", "today", "latest", "news", "current", "weather"]
    needs_search = any(word in user_query.lower() for word in search_keywords)
    
    web_context = ""
    if needs_search:
        with st.status("🌐 Fetching live market data...", expanded=False) as status:
            results = search_web(user_query)
            if results:
                cleaned = [f"Source: {r['url']}\nContent: {r['content']}" for r in results]
                web_context = "\n\nWEB RESULTS:\n" + "\n\n".join(cleaned)
                status.update(label="✅ Live data retrieved!", state="complete")

    # Build the message history for Groq
    # We include the system prompt, then the history, then the latest query with web results
    api_messages = [system_message]
    
    # Add previous conversation turns (History)
    for msg in history:
        api_messages.append({"role": msg["role"], "content": msg["content"]})
    
    # Append the current query flavored with the web results
    current_content = f"{web_context}\n\nUser Question: {user_query}"
    api_messages.append({"role": "user", "content": current_content})

    # Call the API with the full conversation list
    response = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant", 
        messages=api_messages, # Now sending the full list, not just one string
        temperature=0.1
    )
    return response.choices[0].message.content

# --- 6. CHAT UI ---
st.title("🤖 Roon AI")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Analyze this file or ask about today's prices..."):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        response = get_ai_response(prompt, st.session_state.messages, file_context)
        st.markdown(response)
    st.session_state.messages.append({"role": "assistant", "content": response})
