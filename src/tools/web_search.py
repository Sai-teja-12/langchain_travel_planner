import json
import os

from dotenv import load_dotenv
from langchain_core.tools import tool
from tavily import TavilyClient

load_dotenv()


@tool
def web_search(query: str, max_results: int = 5) -> str:
    """Search the web for travel info: visas, weather, tips, local events.

    Args:
        query: The search query
        max_results: Maximum number of results to return (1-10)
    """
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return json.dumps({"error": "TAVILY_API_KEY not set. Use your own knowledge."})

    try:
        client = TavilyClient(api_key=api_key)
        data = client.search(
            query=query,
            max_results=max(1, min(max_results, 10)),
            include_answer=True,
        )
        return json.dumps(
            {
                "answer": data.get("answer"),
                "results": [
                    {
                        "title": r.get("title"),
                        "url": r.get("url"),
                        "content": (r.get("content") or "")[:600],
                    }
                    for r in data.get("results", [])
                ],
            }
        )
    except Exception as exc:
        return json.dumps({"error": f"Web search failed: {exc}"})
