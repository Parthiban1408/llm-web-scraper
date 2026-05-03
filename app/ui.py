import streamlit as st
from groq import Groq
from tavily import TavilyClient
import os

# --- 1. CONFIGURATION & INITIALIZATION ---
st.set_page_config(page_title="Roon AI - Real-time Assistant", layout="centered")

# Initialize Clients (using Streamlit secrets)
# Make sure these are in your .streamlit/secrets.toml
try:
    groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    tavily_client = TavilyClient(api_key=st.secrets["TAVILY_API_KEY"])
except Exception as e:
    st.error("API Keys missing! Add GROQ_API_KEY and TAVILY_API_KEY to secrets.toml")
    st.stop()

# --- 2. SEARCH ENGINE LOGIC ---
def search_web(query):
    """Fetches real-time data using Tavily."""
    response = tavily_client.search(query=query, search_depth="basic", max_results=3)
    return response['results']

# --- 3. AI BRAIN (The Decision Maker) ---
def get_ai_response(user_query, history):
    # Aggressive instructions to stop the "Knowledge Cutoff" loop
    system_prompt = """You are Roon, an elite real-time AI.
    CRITICAL: You have access to the internet via the WEB RESULTS provided. 
    NEVER mention a 'knowledge cutoff'. NEVER say you don't have real-time data.
    If the WEB RESULTS contain data, use it to answer the user accurately. 
    If they are empty, provide the best answer possible without apologizing for your training date."""

    # Keywords that trigger a live search
    search_keywords = ["price", "today", "news", "latest", "weather", "current", "2025", "2026"]
    needs_search = any(word in user_query.lower() for word in search_keywords)
    
    web_context = ""
    
    if needs_search:
        # Show a status spinner while searching
        with st.status("🌐 Searching the live web...", expanded=False) as status:
            try:
                results = search_web(user_query)
                if results:
                    # Clean and format the search results for the AI
                    cleaned_data = [f"Source: {r['url']}\nContent: {r['content']}" for r in results]
                    web_context = "\n\n--- WEB RESULTS ---\n" + "\n\n".join(cleaned_data)
                    status.update(label="✅ Search complete!", state="complete")
                else:
                    status.update(label="⚠️ No live results found.", state="error")
            except Exception as e:
                st.error(f"Search failed: {e}")
                status.update(label="❌ Search Error", state="error")

    # Combine instructions, search data, and user query
    full_prompt = f"{system_prompt}\n\n{web_context}\n\nUser Question: {user_query}\nAnswer:"
    
    try:
        # Using 8b model as it is often more 'obedient' to specific system instructions
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant", 
            messages=[{"role": "user", "content": full_prompt}],
            temperature=0.0  # Low temperature for factual accuracy
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"AI Error: {str(e)}"

# --- 4. STREAMLIT UI LAYOUT ---
st.title("🤖 Roon AI")
st.caption("Real-time Data Assistant powered by Groq & Tavily")

# Initialize chat history in session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat Input Logic
if prompt := st.chat_input("Ask me anything about today..."):
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Generate and display AI response
    with st.chat_message("assistant"):
        response_text = get_ai_response(prompt, st.session_state.messages)
        st.markdown(response_text)
    st.session_state.messages.append({"role": "assistant", "content": response_text})
