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




# --- 5. UPDATED AI LOGIC: SMART MEMORY + LIVE SEARCH ---
def get_ai_response(user_query, history, file_context):
    current_date = datetime.now().strftime("%B %d, %Y")
    
    # STEP 1: CONTEXTUAL QUERY REWRITING
    # This turns "in India" into "Current price of sugar in India May 2026"
    search_refiner_prompt = f"""
    Given the following conversation history and a new user question, 
    rewrite the question into a standalone search query for Google/Tavily.
    If the question is a follow-up, include the main subject from the history.
    Today's Date: {current_date}
    
    History: {history[-3:] if history else "None"}
    New Question: {user_query}
    Standalone Search Query:"""

    try:
        refiner_res = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": search_refiner_prompt}],
            temperature=0.0
        )
        refined_query = refiner_res.choices[0].message.content.strip()
    except:
        refined_query = user_query # Fallback

    # STEP 2: THE SYSTEM PROMPT
    system_message = {
        "role": "system",
        "content": f"""You are Roon, an elite Data Scientist. 
        TODAY'S DATE: {current_date}
        FILE DATA: {file_context if file_context else "No file uploaded."}
        
        STRICT RULES:
        1. Use ONLY the 'LIVE WEB RESULTS' for news, scores, and prices. 
        2. If you don't see the specific info in the web results, say 'Data not found in live search'—DO NOT GUESS.
        3. For IPL matches or elections, always look for 'Live Score' or 'Current Trends'."""
    }

    # STEP 3: EXECUTE SEARCH
    web_context = ""
    with st.status(f"🔍 Searching for: {refined_query}", expanded=False) as status:
        try:
            results = search_web(refined_query)
            if results:
                cleaned = [f"Source: {r['url']}\nContent: {r['content']}" for r in results]
                web_context = "\n\n--- LIVE WEB RESULTS ---\n" + "\n\n".join(cleaned)
                status.update(label="✅ Live data retrieved!", state="complete")
            else:
                web_context = "\nNo live results found for this specific query."
                status.update(label="⚠️ No results found.", state="error")
        except Exception as e:
            status.update(label="❌ Search Error", state="error")

    # STEP 4: FINAL RESPONSE GENERATION
    api_messages = [system_message]
    
    # Add history for conversational memory
    for msg in history[-10:]:
        api_messages.append({"role": msg["role"], "content": msg["content"]})
    
    # Add the refined context and current user query
    api_messages.append({
        "role": "user", 
        "content": f"Contextual Live Data: {web_context}\n\nUser Question: {user_query}"
    })

    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile", 
        messages=api_messages,
        temperature=0.0 # 0.0 is best for accuracy/no hallucinations
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
