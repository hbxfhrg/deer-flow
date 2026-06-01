"""DashScope configuration for ASR and TTS services."""

import os
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DashScopeConfig(BaseModel):
    """Configuration for Aliyun DashScope API (ASR and TTS)."""

    model_config = ConfigDict(extra="allow")

    api_key: str = Field(default="", description="DashScope API key for authentication")
    base_url: str = Field(
        default="https://dashscope.aliyuncs.com/api/v1",
        description="Base URL for DashScope API"
    )

    def is_configured(self) -> bool:
        """Check if DashScope is properly configured."""
        return bool(self.api_key and self.api_key != "")

    @classmethod
    def from_dict(cls, config_dict: dict[str, Any] | None) -> "DashScopeConfig":
        """Create DashScopeConfig from dictionary.

        Args:
            config_dict: Dictionary containing DashScope configuration

        Returns:
            DashScopeConfig instance
        """
        if config_dict is None:
            config_dict = {}

        return cls(
            api_key=config_dict.get("api_key", os.getenv("DASHSCOPE_API_KEY", "")),
            base_url=config_dict.get("base_url", "https://dashscope.aliyuncs.com/api/v1"),
        )