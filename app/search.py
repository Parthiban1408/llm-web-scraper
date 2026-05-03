import os
from tavily import TavilyClient

def search_web(query):
    # Retrieve key from environment or replace with string
    api_key = os.getenv("TAVILY_API_KEY") or "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"
    
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