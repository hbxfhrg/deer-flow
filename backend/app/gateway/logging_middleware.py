"""Logging middleware for API request/response tracing.

Records request parameters and response data while filtering out
large streaming outputs from LLM calls.
"""

import json
import logging
from collections.abc import Callable
from typing import Any

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)

# Paths that should have detailed logging (API endpoints)
_API_PATH_PREFIXES = (
    "/api/",
    "/health",
)

# Paths to exclude from detailed logging (e.g., static files, docs)
_EXCLUDED_PATH_PREFIXES = (
    "/docs",
    "/redoc",
    "/openapi.json",
    "/static/",
)

# Paths that return streaming LLM responses - we should log them differently
_STREAMING_PATH_PREFIXES = (
    "/api/langgraph/",
    "/api/threads/",
    "/api/runs/",
)

# Maximum payload size to log (to avoid logging large responses)
_MAX_LOG_PAYLOAD_SIZE = 2000


def _should_log_detailed(path: str) -> bool:
    """Check if we should log detailed request/response for this path."""
    if any(path.startswith(prefix) for prefix in _EXCLUDED_PATH_PREFIXES):
        return False
    return any(path.startswith(prefix) for prefix in _API_PATH_PREFIXES)


def _is_streaming_path(path: str) -> bool:
    """Check if this path returns streaming LLM responses."""
    return any(path.startswith(prefix) for prefix in _STREAMING_PATH_PREFIXES)


def _truncate_content(content: Any, max_length: int = _MAX_LOG_PAYLOAD_SIZE) -> str:
    """Truncate content for logging while preserving structure."""
    if content is None:
        return "None"
    
    try:
        if isinstance(content, bytes):
            content = content.decode("utf-8", errors="replace")
        elif isinstance(content, dict):
            content = json.dumps(content, ensure_ascii=False)
        else:
            content = str(content)
    except Exception:
        content = str(content)
    
    if len(content) > max_length:
        return content[:max_length] + "..."
    
    return content


class RequestResponseLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log API request and response parameters.
    
    Features:
    - Logs request method, path, headers, query params, and body
    - Logs response status code and body
    - Filters out streaming LLM responses to avoid log spam
    - Truncates large payloads to prevent excessive logging
    """

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path
        
        # Skip detailed logging for excluded paths
        if not _should_log_detailed(path):
            return await call_next(request)
        
        is_streaming = _is_streaming_path(path)
        
        # Log request details
        request_log = {
            "method": request.method,
            "path": path,
            "query_params": dict(request.query_params),
            "client_ip": request.client.host if request.client else None,
        }
        
        # Only log body for non-streaming requests
        if not is_streaming:
            try:
                body = await request.body()
                if body:
                    request_log["body"] = _truncate_content(body)
            except Exception:
                request_log["body"] = "Unable to read request body"
        
        logger.info(f"📤 Request: {json.dumps(request_log, ensure_ascii=False)}")
        
        # Process the request
        response = await call_next(request)
        
        # Log response details
        response_log = {
            "method": request.method,
            "path": path,
            "status_code": response.status_code,
        }
        
        # For streaming responses, don't log the body content
        if is_streaming:
            response_log["body"] = "(Streaming LLM response - content not logged)"
        else:
            # Try to extract response body
            try:
                # Get the response body before returning
                body = b""
                async for chunk in response.body_iterator:
                    body += chunk
                
                # Reconstruct response with the body
                response = Response(
                    content=body,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type=response.media_type,
                )
                
                response_log["body"] = _truncate_content(body)
            except Exception as e:
                response_log["body"] = f"Unable to read response body: {str(e)}"
        
        logger.info(f"📥 Response: {json.dumps(response_log, ensure_ascii=False)}")
        
        return response
