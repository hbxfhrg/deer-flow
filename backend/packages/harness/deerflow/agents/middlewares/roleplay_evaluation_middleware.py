"""Middleware to extract roleplay evaluation data from AI message content into additional_kwargs.

This makes evaluation data accessible via structured metadata rather than parsing JSON from text,
making it portable across different frontends.
"""

from __future__ import annotations

import json
import logging
import re
from typing import TYPE_CHECKING, Any, override
from typing_extensions import Literal

from langchain.agents.middleware import AgentMiddleware
from langgraph.runtime import Runtime

if TYPE_CHECKING:
    from langchain_core.messages import BaseMessage

logger = logging.getLogger(__name__)

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


class RoleplayEvaluationMiddleware(AgentMiddleware):
    """Extract roleplay evaluation JSON from AI message content into additional_kwargs.

    This middleware looks for JSON code blocks or raw JSON at the end of AI message
    content that contains roleplay evaluation data (evaluation.round_score, is_complete, etc.)
    and moves it to additional_kwargs.evaluation for easier frontend consumption.

    This approach is more portable than parsing JSON from raw text content.
    """

    @override
    def after_agent(
        self,
        state: dict[str, Any],
        runtime: Runtime,
        *,
        messages: list[BaseMessage] | None = None,
    ) -> dict[str, Any] | None:
        """Process the final state after agent execution."""
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

        # Try to extract evaluation metadata
        eval_metadata = _extract_evaluation_metadata(content)
        if not eval_metadata:
            return None

        logger.debug(f"Extracted evaluation metadata: {list(eval_metadata.keys())}")

        # Update the message with additional_kwargs
        current_kwargs = dict(getattr(last_ai, "additional_kwargs", {}) or {})
        current_kwargs.update(eval_metadata)

        # Create updated message
        updated_msg = last_ai.model_copy(
            update={"additional_kwargs": current_kwargs}
        )

        return {"messages": {"__root__": messages, last_ai_idx: updated_msg}}

    @override
    async def aafter_agent(
        self,
        state: dict[str, Any],
        runtime: Runtime,
        *,
        messages: list[BaseMessage] | None = None,
    ) -> dict[str, Any] | None:
        """Async version of after_agent."""
        return self.after_agent(state, runtime, messages=messages)
