import streamlit as st
from search import search_web
from llm_parser import chat_with_web, client as groq_client
import streamlit as st

# This must be the first 'st.' command
st.set_page_config(page_title="Roon", layout="wide")

st.title("AI budd")

    
st.write(len(st.secrets["GROQ_API_KEY"]))
# This function fixes the "Who scored the most runs?" follow-up issue
def contextualize_search(query, history):
    q = query.lower().strip()
    if q in ["hi", "hello", "thanks", "ok"]: return None
    
    if len(history) > 1:
        # Mini-call to Llama to turn "who won?" into "who won DC vs RR May 1 2026"
        prompt = f"History: {history[-3:]}\nFollow-up: {query}\nStandalone search query:"
        res = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": f"Convert this follow-up into a standalone Google search query. Be specific with dates and teams. Output ONLY the query:\n{prompt}"}],
            temperature=0
        )
        return res.choices[0].message.content.strip()
    return query


if "messages" not in st.session_state:
    st.session_state.messages = []

# Display History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_input = st.chat_input("Ask anything you want")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        # 1. Rewrite the query to include memory context
        search_q = contextualize_search(user_input, st.session_state.messages)
        
        context = ""
        sources = []
        
        if search_q:
            with st.spinner(f"Searching for: {search_q}..."):
                results = search_web(search_q)
                for i, r in enumerate(results):
                    snippet = r.get("raw_content") or r.get("content") or ""
                    url = r.get("url")
                    context += f"[SOURCE {i+1}]\n{snippet[:1000]}\nURL: {url}\n\n"
                    sources.append(url)
        
        # 2. Final Answer
        with st.spinner("Analyzing..."):
            ans = chat_with_web(context, user_input, st.session_state.messages)
            st.markdown(ans)
            if sources:
                with st.expander("Sources"):
                    for s in sources: st.write(s)
            
    st.session_state.messages.append({"role": "assistant", "content": ans})
