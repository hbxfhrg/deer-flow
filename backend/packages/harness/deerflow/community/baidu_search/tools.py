"""
Baidu Search Tool - Search the web using Baidu Search API.

Requires API key from: https://developer.baidu.com/
"""

import json
import logging

from langchain.tools import tool

from deerflow.config import get_app_config

logger = logging.getLogger(__name__)


def _baidu_search(
    query: str,
    max_results: int = 5,
    api_key: str = None,
    secret_key: str = None,
) -> list[dict]:
    """
    Execute search using Baidu Search API.

    Args:
        query: Search keywords
        max_results: Maximum number of results
        api_key: Baidu API key
        secret_key: Baidu secret key

    Returns:
        List of search results
    """
    try:
        import requests
        import hashlib
        import time
        import random
    except ImportError:
        logger.error("requests library not installed")
        return []

    if api_key is None or secret_key is None:
        config = get_app_config().get_tool_config("baidu_search")
        if config is not None:
            api_key = config.model_extra.get("api_key")
            secret_key = config.model_extra.get("secret_key")
    
    if not api_key or not secret_key:
        logger.error("Baidu API key or secret key not configured")
        return []

    # Baidu Search API endpoint
    url = "https://aip.baidubce.com/rpc/2.0/solution/v1/search/search"
    
    # Generate signature
    timestamp = str(int(time.time()))
    nonce = str(random.randint(100000, 999999))
    sign_str = f"{api_key}{timestamp}{nonce}{secret_key}"
    signature = hashlib.md5(sign_str.encode()).hexdigest()

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    params = {
        "q": query,
        "num": max_results,
        "start": 0
    }

    try:
        response = requests.get(
            url,
            headers=headers,
            params={
                "access_token": api_key,
                "timestamp": timestamp,
                "nonce": nonce,
                "signature": signature,
                **params
            },
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        
        results = []
        if "result" in data and "items" in data["result"]:
            for item in data["result"]["items"]:
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "content": item.get("description", ""),
                })
        
        return results

    except Exception as e:
        logger.error(f"Failed to search with Baidu: {e}")
        return []


@tool("baidu_search", parse_docstring=True)
def baidu_search_tool(
    query: str,
    max_results: int = 5,
) -> str:
    """Search the web for information using Baidu Search.

    Use this tool to find current information, news, articles, and facts from the internet.

    Args:
        query: Search keywords describing what you want to find. Be specific for better results.
        max_results: Maximum number of results to return. Default is 5.
    """
    config = get_app_config().get_tool_config("baidu_search")

    if config is not None and "max_results" in config.model_extra:
        max_results = config.model_extra.get("max_results", max_results)

    results = _baidu_search(
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