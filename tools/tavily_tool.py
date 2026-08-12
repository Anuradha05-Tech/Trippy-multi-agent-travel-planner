from dotenv import load_dotenv
import os
from tavily import TavilyClient

load_dotenv()

API_KEY = os.getenv("TAVILY_API_KEY")

def tavily_search(query: str) -> str:
    """Search the web for information using Tavily."""
    if not API_KEY:
        return "Error: TAVILY_API_KEY is not set in environment."
    
    try:
        client = TavilyClient(api_key=API_KEY)
        response = client.search(query=query)
        results = response.get("results", [])
        
        formatted = []
        for res in results[:5]:
            title = res.get("title", "No Title")
            url = res.get("url", "No URL")
            content = res.get("content", "")
            formatted.append(f"Title: {title}\nURL: {url}\nContent: {content}")
        
        return "\n\n".join(formatted) if formatted else "No results found."
    except Exception as e:
        return f"Error executing Tavily search: {str(e)}"
