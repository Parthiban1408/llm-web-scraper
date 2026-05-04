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



# --- 5. UPDATED AI LOGIC WITH DATE-AWARE SEARCH ---
def get_ai_response(user_query, history, file_context):
    # Get current date for context
    current_date = datetime.now().strftime("%B %d, %Y")
    
    system_message = {
        "role": "system",
        "content": f"""You are Roon, a high-level Data Scientist and Research AI.
        TODAY'S DATE: {current_date}
        
        FILE DATA: {file_context if file_context else "No file uploaded."}
        
        INSTRUCTIONS:
        1. ALWAYS prioritize the WEB RESULTS provided for news, events, or prices.
        2. If the user mentions a past year (e.g., 2024, 2025) or a specific date, fetch data for that period.
        3. Otherwise, ALWAYS assume the user wants 'Today's' live news.
        4. NEVER mention a 'knowledge cutoff'. If you have web results, you are current."""
    }

    # NEW LOGIC: Always search unless it's a generic greeting or math
    non_search_phrases = ["hello", "hi", "who are you", "calculate", "1+", "how are you"]
    is_generic = any(phrase in user_query.lower() for phrase in non_search_phrases)
    
    web_context = ""
    # If it's not a tiny generic phrase, we search the web to prevent hallucinations
    if not is_generic:
        # Detect if user is asking about a specific date
        search_query = user_query
        if "today" in user_query.lower() or not any(year in user_query for year in ["2024", "2025", "2023"]):
            # If no specific past year is mentioned, force "today" or "May 2026" into the search
            search_query = f"{user_query} news today {current_date}"

        with st.status(f"🌐 Fetching live data for: {search_query}", expanded=False) as status:
            try:
                results = search_web(search_query)
                if results:
                    cleaned = [f"Source: {r['url']}\nContent: {r['content']}" for r in results]
                    web_context = "\n\n--- LIVE WEB RESULTS ---\n" + "\n\n".join(cleaned)
                    status.update(label="✅ Live data retrieved!", state="complete")
                else:
                    status.update(label="⚠️ No results found. Answering from memory.", state="error")
            except Exception as e:
                status.update(label=f"❌ Search Error: {e}", state="error")

    # Build the message history for Groq
    api_messages = [system_message]
    for msg in history[-10:]: # Keep last 10 messages for memory
        api_messages.append({"role": msg["role"], "content": msg["content"]})
    
    # Final query sent to AI
    current_content = f"{web_context}\n\nUser Question: {user_query}"
    api_messages.append({"role": "user", "content": current_content})

    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile", 
        messages=api_messages,
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
