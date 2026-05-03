import os
import streamlit as st
from groq import Groq

# Initialize Groq Client
client = Groq(
    api_key = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")
)
def chat_with_web(context, query, history):
    messages = [
        {
            "role": "system",
            "content": """
            You are a factual, real-time AI assistant.
            
            STRICT RULES:
            1. BASE YOUR ANSWER ONLY ON THE 'WEB DATA'.
            2. If 'WEB DATA' does not contain the answer, say "I cannot find this in current search results" instead of guessing.
            3. FOR SPORTS: Prioritize exact scores, player names, and dates found in the data.
            4. CITATIONS: Cite sources as [SOURCE X] when using them.
            5. CONVERSATION: If the user is just saying "hi" or "thanks", ignore the 'WEB DATA' and reply naturally.
            """
        }
    ]

    # Inject conversation memory (Last 5 turns for efficiency)
    for msg in history[-6:-1]: 
        messages.append({"role": msg["role"], "content": msg["content"]})

    # Add current context and user query
    messages.append({
        "role": "user",
        "content": f"WEB DATA:\n{context}\n\nUSER QUESTION: {query}"
    })

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",   
        messages=messages,
        temperature=0.1 # Low temperature prevents hallucinations
    )

    return response.choices[0].message.content