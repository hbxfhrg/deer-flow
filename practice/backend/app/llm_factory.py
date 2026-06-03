"""简化 LLM 工厂 — 直接使用 langchain_openai.ChatOpenAI，不依赖 deerflow-harness"""

import logging
from importlib import import_module

from langchain.chat_models import BaseChatModel

from app.config import get_config, ModelConfig

logger = logging.getLogger(__name__)


def create_chat_model(name: str | None = None, thinking_enabled: bool = False, **kwargs) -> BaseChatModel:
    """创建 LLM 实例

    Args:
        name: 模型名称，None 则使用配置中第一个模型
        thinking_enabled: 忽略（保留接口兼容性）
        **kwargs: 额外参数

    Returns:
        BaseChatModel 实例
    """
    config = get_config()

    if name is None:
        if not config.models:
            raise ValueError("No models configured in config.yaml")
        name = config.models[0].name

    model_cfg = config.get_model_config(name)
    if model_cfg is None:
        raise ValueError(f"Model '{name}' not found in config")

    # 解析 use 字段: "langchain_openai:ChatOpenAI" → 模块和类
    if ":" in model_cfg.use:
        module_path, class_name = model_cfg.use.split(":", 1)
    else:
        module_path, class_name = model_cfg.use, "ChatOpenAI"

    try:
        module = import_module(module_path)
        model_class = getattr(module, class_name)
    except (ImportError, AttributeError) as e:
        raise ImportError(f"Failed to load model class '{model_cfg.use}': {e}") from e

    # 构建参数
    params = {
        "model": model_cfg.model,
        "api_key": model_cfg.resolved_api_key,
        "base_url": model_cfg.resolved_base_url,
        "temperature": model_cfg.temperature,
        "max_tokens": model_cfg.max_tokens,
        "timeout": model_cfg.request_timeout,
        "max_retries": model_cfg.max_retries,
        "stream_usage": True,
    }

    # 移除空值
    params = {k: v for k, v in params.items() if v is not None and v != ""}

    # 合并额外参数
    params.update(kwargs)

    # 移除不支持的参数
    params.pop("reasoning_effort", None)

    try:
        instance = model_class(**params)
    except TypeError as e:
        # 某些参数可能不被支持，逐步移除
        logger.warning(f"Model creation error with all params, retrying with minimal: {e}")
        safe_params = {k: v for k, v in params.items()
                       if k in ("model", "api_key", "base_url", "temperature",
                                "max_tokens", "timeout", "max_retries")}
        instance = model_class(**safe_params)

    logger.info(f"Created LLM: {model_cfg.name} ({model_cfg.model})")
    return instance
