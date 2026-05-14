"""Middleware to extract roleplay evaluation data from AI message content into additional_kwargs.

This makes evaluation data accessible via structured metadata rather than parsing JSON from text,
making it portable across different frontends.

The evaluation extraction runs asynchronously in the background to avoid blocking the main
conversation flow. The next question is displayed immediately, while evaluation runs in parallel.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
import threading
from concurrent.futures import ThreadPoolExecutor, Future
from typing import TYPE_CHECKING, Any, override
from typing_extensions import Literal
from contextvars import copy_context

from langchain.agents.middleware import AgentMiddleware
from langgraph.runtime import Runtime

if TYPE_CHECKING:
    from langchain_core.messages import BaseMessage

logger = logging.getLogger(__name__)

# Background task storage for evaluation results
_evaluation_background_tasks: dict[str, dict[str, Any]] = {}
_evaluation_tasks_lock = threading.Lock()

# Thread pool for async evaluation execution
_evaluation_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="roleplay-eval-")

# Pattern to match JSON in markdown code blocks or raw JSON
_JSON_CODE_BLOCK_RE = re.compile(r"```(?:json)?\s*\n*([\s\S]*?)\n*```", re.IGNORECASE)
_RAW_JSON_RE = re.compile(r"(\{[\s\S]*\})")

# Fields that indicate this is a roleplay evaluation
_ROLEPLAY_EVALUATION_FIELDS = (
    "evaluation",
    "is_complete",
    "customer_message",
    "round",
    "total_score",
    "dimension_scores",
    "strengths",
    "improvements",
    "summary",
)


def _extract_json_from_content(content: str) -> dict[str, Any] | None:
    """Extract JSON object from content string."""
    if not content:
        return None

    # Try JSON code blocks first
    json_matches = _JSON_CODE_BLOCK_RE.findall(content)
    for json_str in json_matches:
        try:
            parsed = json.loads(json_str.strip())
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            continue

    # Try raw JSON object at end of content
    raw_matches = _RAW_JSON_RE.findall(content)
    for json_str in reversed(raw_matches):
        try:
            parsed = json.loads(json_str.strip())
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            continue

    # Try parsing entire content as JSON
    try:
        parsed = json.loads(content.strip())
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    return None


def _is_roleplay_evaluation(data: dict[str, Any]) -> bool:
    """Check if the JSON data looks like a roleplay evaluation."""
    if not isinstance(data, dict):
        return False

    # Must have evaluation field or is_complete field
    has_evaluation = "evaluation" in data and isinstance(data.get("evaluation"), dict)
    has_is_complete = "is_complete" in data
    has_round = "round" in data

    return has_evaluation or has_is_complete or has_round


def _extract_evaluation_metadata(message_content: str) -> dict[str, Any] | None:
    """Extract roleplay evaluation metadata from message content.

    Returns None if no valid evaluation JSON is found.
    """
    data = _extract_json_from_content(message_content)
    if not data or not _is_roleplay_evaluation(data):
        return None

    return {"evaluation": data}


def _run_async_evaluation_extraction(coro):
    """Helper to run async evaluation extraction in a thread pool."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop is not None and loop.is_running():
        # Submit to thread pool to avoid blocking the main loop
        future = _evaluation_executor.submit(asyncio.run, coro)
        return future.result()
    else:
        # No running loop, can use asyncio.run directly
        return asyncio.run(coro)


class RoleplayEvaluationMiddleware(AgentMiddleware):
    """Extract roleplay evaluation JSON from AI message content into additional_kwargs.

    This middleware looks for JSON code blocks or raw JSON at the end of AI message
    content that contains roleplay evaluation data (evaluation.round_score, is_complete, etc.)
    and moves it to additional_kwargs.evaluation for easier frontend consumption.

    This approach is more portable than parsing JSON from raw text content.
    
    The evaluation extraction runs asynchronously in the background to avoid blocking
    the main conversation flow. The next question is displayed immediately, while
    evaluation runs in parallel.
    """

    def _extract_and_store_evaluation(
        self,
        messages: list[BaseMessage],
        last_ai_idx: int,
        runtime: Runtime,
    ) -> None:
        """Extract evaluation and store it (runs in background thread)."""
        try:
            last_ai = messages[last_ai_idx]
            content = getattr(last_ai, "content", "")
            
            if not content:
                return
            
            # Try to extract evaluation metadata
            eval_metadata = _extract_evaluation_metadata(content)
            if not eval_metadata:
                return
            
            logger.debug(f"Extracted evaluation metadata in background: {list(eval_metadata.keys())}")
            
            # Update the message with additional_kwargs
            current_kwargs = dict(getattr(last_ai, "additional_kwargs", {}) or {})
            current_kwargs.update(eval_metadata)
            
            # Create updated message
            updated_msg = last_ai.model_copy(
                update={"additional_kwargs": current_kwargs}
            )
            messages[last_ai_idx] = updated_msg
            
            # Store the evaluation result for later retrieval
            thread_id = runtime.context.get("thread_id") if runtime.context else None
            run_id = runtime.context.get("run_id") if runtime.context else None
            
            if thread_id and run_id:
                task_key = f"{thread_id}:{run_id}"
                with _evaluation_tasks_lock:
                    _evaluation_background_tasks[task_key] = {
                        "evaluation": eval_metadata,
                        "updated_message": updated_msg,
                        "status": "completed",
                    }
                logger.info(f"Stored evaluation result for thread={thread_id}, run={run_id}")
            
        except Exception as e:
            logger.error(f"Background evaluation extraction failed: {e}", exc_info=True)

    @override
    def after_agent(
        self,
        state: dict[str, Any],
        runtime: Runtime,
        *,
        messages: list[BaseMessage] | None = None,
    ) -> dict[str, Any] | None:
        """Process the final state after agent execution.
        
        This method now returns immediately without blocking on evaluation extraction.
        The evaluation is extracted asynchronously in a background thread.
        """
        if messages is None:
            return None

        # Find the last AI message
        last_ai_idx = None
        for i in reversed(range(len(messages))):
            msg = messages[i]
            if getattr(msg, "type", None) == "ai":
                last_ai_idx = i
                break

        if last_ai_idx is None:
            return None

        last_ai = messages[last_ai_idx]
        content = getattr(last_ai, "content", "")

        if not content:
            return None

        # Start background evaluation extraction (non-blocking)
        # This allows the next question to be displayed immediately
        thread_id = runtime.context.get("thread_id") if runtime.context else None
        run_id = runtime.context.get("run_id") if runtime.context else None
        
        if thread_id and run_id:
            task_key = f"{thread_id}:{run_id}"
            with _evaluation_tasks_lock:
                _evaluation_background_tasks[task_key] = {
                    "status": "pending",
                }
            
            # Submit evaluation extraction to background thread pool
            parent_context = copy_context()
            def run_extraction():
                return parent_context.run(
                    self._extract_and_store_evaluation,
                    messages,
                    last_ai_idx,
                    runtime,
                )
            
            _evaluation_executor.submit(run_extraction)
            logger.info(f"Started background evaluation extraction for thread={thread_id}, run={run_id}")

        # Return None immediately - don't block the main flow
        # The evaluation will be extracted asynchronously
        return None

    @override
    async def aafter_agent(
        self,
        state: dict[str, Any],
        runtime: Runtime,
        *,
        messages: list[BaseMessage] | None = None,
    ) -> dict[str, Any] | None:
        """Async version of after_agent - also runs evaluation in background."""
        return self.after_agent(state, runtime, messages=messages)


def get_evaluation_result(thread_id: str, run_id: str) -> dict[str, Any] | None:
    """Get the evaluation result for a specific thread/run.
    
    Args:
        thread_id: The thread ID
        run_id: The run ID
        
    Returns:
        Evaluation result dict if available, None otherwise
    """
    task_key = f"{thread_id}:{run_id}"
    with _evaluation_tasks_lock:
        return _evaluation_background_tasks.get(task_key)
