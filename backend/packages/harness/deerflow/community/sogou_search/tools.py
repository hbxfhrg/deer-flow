"""
Sogou Search Tool - Search the web using Sogou Search API.

Requires API key from: https://fanyi.sogou.com/open/api/
"""

import json
import logging

from langchain.tools import tool

from deerflow.config import get_app_config

logger = logging.getLogger(__name__)


def _sogou_search(
    query: str,
    max_results: int = 5,
    api_key: str = None,
) -> list[dict]:
    """
    Execute search using Sogou Search API.

    Args:
        query: Search keywords
        max_results: Maximum number of results
        api_key: Sogou API key

    Returns:
        List of search results
    """
    try:
        import requests
    except ImportError:
        logger.error("requests library not installed")
        return []

    if api_key is None:
        config = get_app_config().get_tool_config("sogou_search")
        if config is not None and "api_key" in config.model_extra:
            api_key = config.model_extra.get("api_key")
    
    if not api_key:
        logger.error("Sogou API key not configured")
        return []

    # Sogou Search API endpoint
    url = "https://api.sogou.com/web/search"
    
    params = {
        "query": query,
        "num": max_results,
        "type": "web",
        "appid": api_key.split(":")[0] if ":" in api_key else api_key,
        "signature": api_key.split(":")[1] if ":" in api_key else ""
    }

    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        results = []
        if "results" in data:
            for item in data["results"]:
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "content": item.get("description", ""),
                })
        
        return results

    except Exception as e:
        logger.error(f"Failed to search with Sogou: {e}")
        return []


@tool("sogou_search", parse_docstring=True)
def sogou_search_tool(
    query: str,
    max_results: int = 5,
) -> str:
    """Search the web for information using Sogou Search.

    Use this tool to find current information, news, articles, and facts from the internet.

    Args:
        query: Search keywords describing what you want to find. Be specific for better results.
        max_results: Maximum number of results to return. Default is 5.
    """
    config = get_app_config().get_tool_config("sogou_search")

    if config is not None and "max_results" in config.model_extra:
        max_results = config.model_extra.get("max_results", max_results)

    results = _sogou_search(
        query=query,
        max_results=max_results,
    )

    if not results:
        return json.dumps({"error": "No results found", "query": query}, ensure_ascii=False)

    normalized_results = [
        {
            "title": r.get("title", ""),
            "url": r.get("url", ""),
            "content": r.get("content", ""),
        }
        for r in results
    ]

    output = {
        "query": query,
        "total_results": len(normalized_results),
        "results": normalized_results,
    }

    return json.dumps(output, indent=2, ensure_ascii=False)