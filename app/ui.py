import streamlit as st
import pandas as pd
import PyPDF2
from datetime import datetime
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


# --- 2. ENHANCED FILE PROCESSING (Senior DS Level) ---
def process_file(uploaded_file):
    """Extracts deep statistical insights and data samples."""
    try:
        if uploaded_file.name.endswith(('.xlsx', '.xls', '.csv')):
            df = pd.read_excel(uploaded_file) if not uploaded_file.name.endswith('.csv') else pd.read_csv(uploaded_file)
            
            # Statistical Metadata for Senior Analysis
            buffer = io.StringIO()
            df.info(buf=buffer)
            info_str = buffer.getvalue()
            stats_summary = df.describe(include='all').to_string()
            missing_values = df.isnull().sum().to_string()
            
            return f"""
            DATASET METADATA:
            {info_str}
            
            STATISTICAL DESCRIPTIVES:
            {stats_summary}
            
            MISSING VALUES:
            {missing_values}
            
            DATA SAMPLE (TOP 50 ROWS):
            {df.head(50).to_string()}
            """
        elif uploaded_file.name.endswith('.pdf'):
            pdf_reader = PyPDF2.PdfReader(uploaded_file)
            # Increased page limit for deeper context
            text = "\n".join([page.extract_text() for page in pdf_reader.pages[:15]])
            return f"FULL PDF CONTENT (EXCERPT):\n{text}"
    except Exception as e:
        return f"Error in data extraction: {e}"
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





# --- 5. SENIOR AI LOGIC (High-Level Analysis) ---
# --- 5. SMART SENIOR AI LOGIC (No More Greeting Madness) ---
def get_ai_response(user_query, history, file_context):
    current_date = datetime.now().strftime("%B %d, %Y")
    
    # Check if it's a simple greeting or small talk
    greetings = ["hi", "hello", "hey", "how are you", "who are you", "gm", "gn"]
    is_greeting = user_query.lower().strip() in greetings

    # 1. GREETING SHORT-CIRCUIT (Saves your Rate Limit and avoids crazy analysis)
    if is_greeting:
        return "Hello! I'm Roon. I'm ready to analyze your files or fetch live market data. What's on your mind today?"

    # 2. CONTEXTUAL QUERY REWRITING
    search_refiner_prompt = f"Rewrite for search. Today: {current_date}. History: {history[-2:]}. Question: {user_query}"
    try:
        refiner_res = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant", # Using smaller model to save rate limits
            messages=[{"role": "user", "content": search_refiner_prompt}],
            temperature=0
        )
        refined_query = refiner_res.choices[0].message.content.strip()
    except:
        refined_query = user_query

    # 3. SENIOR DATA SCIENTIST SYSTEM PROMPT
    system_message = {
        "role": "system",
        "content": f"""You are a Principal Data Scientist. TODAY: {current_date}. 
        FILE DATA: {file_context if file_context else "None"}
        RULES:
        - For DATA/NEWS: Use Markdown tables and statistical insights.
        - For CHAT: Be concise and professional.
        - NEVER analyze a greeting as a dataset."""
    }

    # 4. LIVE SEARCH
    web_context = ""
    with st.status(f"🔍 Intel Search: {refined_query}", expanded=False):
        try:
            results = search_web(refined_query)
            if results:
                web_context = "\n\n--- LIVE DATA ---\n" + "\n".join([r['content'] for r in results])
        except:
            web_context = "Search unavailable."

    # 5. FINAL RESPONSE
    api_messages = [system_message]
    for msg in history[-5:]: api_messages.append({"role": msg["role"], "content": msg["content"]})
    api_messages.append({"role": "user", "content": f"DATA: {web_context}\n\nUSER: {user_query}"})

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant", 
            messages=api_messages,
            temperature=0.1
        )
        return response.choices[0].message.content
    except Exception as e:
        return "⚠️ Rate limit hit. Please wait 60 seconds or use a smaller model like 'llama-3.1-8b-instant'."
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
