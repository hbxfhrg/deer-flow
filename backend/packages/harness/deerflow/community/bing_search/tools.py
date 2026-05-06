"""
Bing Search Tool - Search the web using Microsoft Bing Search API.

Requires API key from: https://www.microsoft.com/en-us/bing/apis/bing-web-search-api
"""

import json
import logging

from langchain.tools import tool

from deerflow.config import get_app_config

logger = logging.getLogger(__name__)


def _bing_search(
    query: str,
    max_results: int = 5,
    api_key: str = None,
) -> list[dict]:
    """
    Execute search using Microsoft Bing Search API.

    Args:
        query: Search keywords
        max_results: Maximum number of results
        api_key: Bing API key (optional, uses config if not provided)

    Returns:
        List of search results
    """
    try:
        import requests
    except ImportError:
        logger.error("requests library not installed")
        return []

    if api_key is None:
        config = get_app_config().get_tool_config("web_search")
        if config is not None and "api_key" in config.model_extra:
            api_key = config.model_extra.get("api_key")
    
    if not api_key:
        logger.error("Bing API key not configured")
        return []

    url = "https://api.bing.microsoft.com/v7.0/search"
    headers = {"Ocp-Apim-Subscription-Key": api_key}
    params = {
        "q": query,
        "count": max_results,
        "mkt": "zh-CN",
        "safeSearch": "Moderate"
    }

    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        results = []
        if "webPages" in data and "value" in data["webPages"]:
            for item in data["webPages"]["value"]:
                results.append({
                    "title": item.get("name", ""),
                    "url": item.get("url", ""),
                    "content": item.get("snippet", ""),
                    "description": item.get("description", "")
                })
        
        return results

    except Exception as e:
        logger.error(f"Failed to search with Bing: {e}")
        return []


@tool("web_search", parse_docstring=True)
def web_search_tool(
    query: str,
    max_results: int = 5,
) -> str:
    """Search the web for information using Bing Search.

    Use this tool to find current information, news, articles, and facts from the internet.

    Args:
        query: Search keywords describing what you want to find. Be specific for better results.
        max_results: Maximum number of results to return. Default is 5.
    """
    config = get_app_config().get_tool_config("web_search")

    # Override max_results from config if set
    if config is not None and "max_results" in config.model_extra:
        max_results = config.model_extra.get("max_results", max_results)

    results = _bing_search(
        query=query,
        max_results=max_results,
    )

    if not results:
        return json.dumps({"error": "No results found", "query": query}, ensure_ascii=False)

    normalized_results = [
        {
            "title": r.get("title", ""),
            "url": r.get("url", ""),
            "content": r.get("content", r.get("description", "")),
        }
        for r in results
    ]

    output = {
        "query": query,
        "total_results": len(normalized_results),
        "results": normalized_results,
    }

    return json.dumps(output, indent=2, ensure_ascii=False)