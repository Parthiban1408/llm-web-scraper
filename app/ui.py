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
# --- 2. FULL-SCAN FILE PROCESSING ---
def process_file(uploaded_file):
    """Processes the entire file to provide a 100% complete data map."""
    try:
        if uploaded_file.name.endswith(('.xlsx', '.xls', '.csv')):
            # Load entire dataset into memory
            df = pd.read_excel(uploaded_file) if not uploaded_file.name.endswith('.csv') else pd.read_csv(uploaded_file)
            
            # 1. Full Statistical Profile (Covers 100% of rows)
            stats_summary = df.describe(include='all').to_string()
            
            # 2. Complete Column & Type Map
            buffer = io.StringIO()
            df.info(buf=buffer)
            full_schema = buffer.getvalue()
            
            # 3. Missing Value Analysis
            null_map = df.isnull().sum().to_string()

            # 4. Value Distribution for Categorical Columns
            # (Helps the AI see 'Hidden' values in large files)
            cat_distribution = ""
            for col in df.select_dtypes(include=['object']).columns[:5]: # Top 5 categorical columns
                cat_distribution += f"\nDistribution for {col}:\n{df[col].value_counts().head(10).to_string()}\n"

            return f"""
            ### FULL DATASET STRUCTURE ###
            {full_schema}
            
            ### GLOBAL STATISTICAL SUMMARY (All Rows) ###
            {stats_summary}
            
            ### MISSING DATA AUDIT ###
            {null_map}
            
            ### CATEGORICAL DISTRIBUTIONS ###
            {cat_distribution}
            
            ### REPRESENTATIVE SAMPLE (Top 100 Rows) ###
            {df.head(100).to_string()}
            """
        elif uploaded_file.name.endswith('.pdf'):
            pdf_reader = PyPDF2.PdfReader(uploaded_file)
            # Read all pages if the document is reasonably sized
            full_text = "\n".join([page.extract_text() for page in pdf_reader.pages])
            return f"FULL PDF CONTENT:\n{full_text}"
            
    except Exception as e:
        return f"Error during full-file scan: {e}"
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
# --- 1. INITIALIZE PERSISTENT MEMORY ---
if "messages" not in st.session_state:
    st.session_state.messages = []  # Normal chat history

# --- 2. UPDATED RESPONSE LOGIC ---
def get_ai_response(user_query, history, file_context):
    """
    Combines live data and file context into a 'Background Brain' 
    without disturbing the conversational flow.
    """
    
    # Live Search Integration (Only triggers if needed)
    web_results = ""
    search_keywords = ["price", "today", "latest", "news"]
    if any(word in user_query.lower() for word in search_keywords):
        with st.status("🌐 Checking live markets...", expanded=False):
            search_data = search_web(user_query) # Your existing search function
            web_results = f"\nLIVE WEB DATA: {search_data}"

    # THE SYSTEM PROMPT (The "Background Brain")
    # This stays invisible to the chat UI but guides every response
    system_instruction = {
        "role": "system",
        "content": f"""You are Roon, a helpful AI assistant. 
        TODAY'S DATE: {datetime.now().strftime('%Y-%m-%d')}
        
        KNOWLEDGE BASE (UPLOADED FILE): 
        {file_context if file_context else "No file uploaded currently."}
        
        {web_results}
        
        INSTRUCTIONS:
        - Engage in a natural, friendly conversation.
        - Reference the 'KNOWLEDGE BASE' only if it helps answer the user.
        - Use live web data for time-sensitive questions.
        - Maintain the flow of previous messages."""
    }

    # CONSTRUCT THE FULL PAYLOAD
    # We always start with the instruction, then add the full history
    api_messages = [system_instruction] + history + [{"role": "user", "content": user_query}]

    # Groq API Call
    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=api_messages,
        temperature=0.7 # Higher temperature for more "ChatGPT-like" fluidity
    )
    return response.choices[0].message.content

# --- 3. THE CHAT INTERFACE ---
st.title("🤖 Roon AI")

# Display conversation from history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask me anything..."):
    # 1. Show user message immediately
    st.chat_message("user").markdown(prompt)
    
    # 2. Get AI response using the combined context
    with st.chat_message("assistant"):
        # We pass the existing history to maintain context
        full_response = get_ai_response(prompt, st.session_state.messages, file_context)
        st.markdown(full_response)
    
    # 3. Append both to history for the next turn
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.messages.append({"role": "assistant", "content": full_response})
