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
def get_ai_response(user_query, history, file_context):
    current_date = datetime.now().strftime("%B %d, %Y")
    
    # Contextual Query Rewriting (keeping your memory logic)
    search_refiner_prompt = f"Rewrite this as a standalone search query based on history. Today: {current_date}. History: {history[-2:]}. Question: {user_query}"
    refiner_res = groq_client.chat.completions.create(model="llama-3.1-8b-instant", messages=[{"role": "user", "content": search_refiner_prompt}], temperature=0)
    refined_query = refiner_res.choices[0].message.content.strip()

    # SENIOR DATA SCIENTIST SYSTEM PROMPT
    system_message = {
        "role": "system",
        "content": f"""You are a Principal Data Scientist and Market Strategist. 
        TODAY'S DATE: {current_date}
        FILE CONTEXT: {file_context if file_context else "No file uploaded."}
        
        ANALYSIS PROTOCOL:
        1. When analyzing files, provide:
           - Statistical Rigor: Identify correlations, outliers, and distribution anomalies.
           - Business Intelligence: Translate data points into actionable strategic advice.
           - Structure: Use clean Markdown tables, bold headers, and crisp bullet points.
        2. Combine FILE DATA with LIVE WEB RESULTS for a holistic 'Macro vs Micro' view.
        3. If data is missing or insufficient, state the statistical limitation clearly.
        4. Tone: Professional, decisive, and insightful. No fluff."""
    }

    # Execute Search (keeping your live data logic)
    web_context = ""
    with st.status(f"🔍 Senior Intel Retrieval: {refined_query}", expanded=False):
        results = search_web(refined_query)
        if results:
            web_context = "\n\n--- LIVE MARKET INTELLIGENCE ---\n" + "\n\n".join([f"Source: {r['url']}\n{r['content']}" for r in results])

    api_messages = [system_message]
    for msg in history[-10:]: api_messages.append({"role": msg["role"], "content": msg["content"]})
    
    # Final query with refined context
    api_messages.append({
        "role": "user", 
        "content": f"INTEGRATED CONTEXT:\n{web_context}\n\nUSER REQUEST: {user_query}"
    })

    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile", 
        messages=api_messages,
        temperature=0.1 # Low temperature for analytical precision
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
