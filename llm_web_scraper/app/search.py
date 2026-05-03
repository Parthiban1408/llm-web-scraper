import os
import streamlit as st
from tavily import TavilyClient

def search_web(query):
    try:
        # Pass the secret directly into the client here
        client = TavilyClient(api_key=st.secrets["TAVILY_API_KEY"])
        response = client.search(
            query=query,
            search_depth="advanced", 
            max_results=5, 
            include_raw_content=True
        )
        return response.get("results", [])
    except Exception as e:
        print(f"Search error: {e}")
        return []
