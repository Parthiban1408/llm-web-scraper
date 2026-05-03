import os
import streamlit as st
from groq import Groq
import streamlit as st
from groq import Groq

# This pulls directly from that Secrets box you just edited
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

def chat_with_web(user_input, search_results, history):
    # 1. Prepare the search data safely
    context_list = []
    
    for res in search_results:
        # This check prevents the "string indices must be integers" error
        if isinstance(res, dict):
            content = res.get('content', '') or res.get('snippet', '')
            url = res.get('url', 'No Source')
            context_list.append(f"Source ({url}): {content}")
        elif isinstance(res, str):
            # If the result is just a string, use it directly
            context_list.append(res)
            
    context_text = "\n\n".join(context_list)

    # 2. Build the Prompt
    prompt = f"""
    You are Roon, a helpful AI assistant.
    
    User Query: {user_input}
    
    Web Search Results:
    {context_text}
    
    Conversation History:
    {history[-3:] if history else "No previous history"}
    
    Based on the web results above, provide a clear and concise answer. 
    If the results don't contain the answer, say you don't have enough live data.
    """

    # 3. Call Groq
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5
    )
    
    return response.choices[0].message.content
