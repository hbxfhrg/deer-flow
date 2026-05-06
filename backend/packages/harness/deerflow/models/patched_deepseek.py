"""Patched ChatDeepSeek that preserves reasoning_content in multi-turn conversations.

This module provides a patched version of ChatDeepSeek that properly handles
reasoning_content when sending messages back to the API. The original implementation
stores reasoning_content in additional_kwargs but doesn't include it when making
subsequent API calls, which causes errors with APIs that require reasoning_content
on all assistant messages when thinking mode is enabled.
"""

from typing import Any

from langchain_core.language_models import LanguageModelInput
from langchain_core.messages import AIMessage
from langchain_deepseek import ChatDeepSeek


class PatchedChatDeepSeek(ChatDeepSeek):
    """ChatDeepSeek with proper reasoning_content preservation.

    When using thinking/reasoning enabled models, the API expects reasoning_content
    to be present on ALL assistant messages in multi-turn conversations. This patched
    version ensures reasoning_content from additional_kwargs is included in the
    request payload.
    
    Also properly handles thinking mode by removing the 'thinking' param from
    extra_body when it should be disabled, to avoid API errors.
    """

    def __init__(self, **kwargs: Any) -> None:
        """Initialize with thinking parameter cleanup."""
        # Clean up thinking in extra_body if it's a boolean (invalid)
        extra_body = kwargs.get("extra_body")
        if extra_body and isinstance(extra_body, dict) and "thinking" in extra_body:
            thinking_value = extra_body["thinking"]
            if isinstance(thinking_value, bool):
                del extra_body["thinking"]
                if not extra_body:
                    kwargs.pop("extra_body", None)
        
        # Also clean up direct thinking parameter if it's a boolean
        if "thinking" in kwargs and isinstance(kwargs["thinking"], bool):
            kwargs.pop("thinking", None)
        
        super().__init__(**kwargs)

    @classmethod
    def is_lc_serializable(cls) -> bool:
        return True

    @property
    def lc_secrets(self) -> dict[str, str]:
        return {"api_key": "DEEPSEEK_API_KEY", "openai_api_key": "DEEPSEEK_API_KEY"}

    def _get_request_payload(
        self,
        input_: LanguageModelInput,
        *,
        stop: list[str] | None = None,
        **kwargs: Any,
    ) -> dict:
        """Get request payload with reasoning_content preserved.

        Overrides the parent method to inject reasoning_content from
        additional_kwargs into assistant messages in the payload.
        Also removes 'thinking' from extra_body if it's set to False (invalid).
        """
        # Get the original messages before conversion
        original_messages = self._convert_input(input_).to_messages()

        # Call parent to get the base payload
        payload = super()._get_request_payload(input_, stop=stop, **kwargs)

        # Fix: Remove thinking from extra_body if it's set to invalid value (False/True booleans)
        # DeepSeek API expects thinking to be an object like {"type": "disabled"} or not present
        extra_body = payload.get("extra_body", {})
        if "thinking" in extra_body:
            thinking_value = extra_body["thinking"]
            # If thinking is a boolean (invalid), remove it from the payload
            if isinstance(thinking_value, bool):
                del extra_body["thinking"]
                if not extra_body:
                    payload.pop("extra_body", None)
        
        # Also fix: If thinking is directly in the payload (not in extra_body)
        if "thinking" in payload:
            thinking_value = payload["thinking"]
            if isinstance(thinking_value, bool):
                del payload["thinking"]

        # Match payload messages with original messages to restore reasoning_content
        payload_messages = payload.get("messages", [])

        # The payload messages and original messages should be in the same order
        # Iterate through both and match by position
        if len(payload_messages) == len(original_messages):
            for payload_msg, orig_msg in zip(payload_messages, original_messages):
                if payload_msg.get("role") == "assistant" and isinstance(orig_msg, AIMessage):
                    reasoning_content = orig_msg.additional_kwargs.get("reasoning_content")
                    if reasoning_content is not None:
                        payload_msg["reasoning_content"] = reasoning_content
        else:
            # Fallback: match by counting assistant messages
            ai_messages = [m for m in original_messages if isinstance(m, AIMessage)]
            assistant_payloads = [(i, m) for i, m in enumerate(payload_messages) if m.get("role") == "assistant"]

            for (idx, payload_msg), ai_msg in zip(assistant_payloads, ai_messages):
                reasoning_content = ai_msg.additional_kwargs.get("reasoning_content")
                if reasoning_content is not None:
                    payload_messages[idx]["reasoning_content"] = reasoning_content

        return payload
