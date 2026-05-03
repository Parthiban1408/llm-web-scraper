import os
import streamlit as st
from tavily import TavilyClient

def search_web(query):
    # Retrieve key from environment or replace with string
    api_key = st.secrets.get("TAVILY_API_KEY") or os.getenv("TAVILY_API_KEY")
    
    try:
        client = TavilyClient(api_key=api_key)
        response = client.search(
            query=query,
            search_depth="advanced", # Required for live/recent events
            max_results=5, 
            include_raw_content=True
        )
        return response.get("results", [])
    except Exception as e:
        print(f"Search error: {e}")
        return []