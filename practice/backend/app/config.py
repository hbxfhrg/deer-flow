"""简化配置系统 — 从 config.yaml 加载，支持 ${ENV_VAR} 替换"""

import os
import re
import logging
from pathlib import Path
from functools import lru_cache
from typing import Any

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()

logger = logging.getLogger(__name__)

# ── 配置模型 ────────────────────────────────────────────────────


class ModelConfig(BaseModel):
    """单个 LLM 模型配置"""

    name: str
    display_name: str | None = None
    use: str = "langchain_openai:ChatOpenAI"
    model: str
    api_key: str = ""
    base_url: str = ""
    request_timeout: float = 120.0
    max_retries: int = 3
    max_tokens: int = 8192
    temperature: float = 0.7

    @property
    def resolved_api_key(self) -> str:
        return _resolve_env(self.api_key)

    @property
    def resolved_base_url(self) -> str:
        return _resolve_env(self.base_url)


class DatabaseConfig(BaseModel):
    """MySQL 数据库配置"""

    host: str = "localhost"
    port: int = 3306
    name: str = "deerflow_roleplay"
    user: str = ""
    password: str = ""

    @property
    def url(self) -> str:
        pwd = _resolve_env(self.password)
        user = _resolve_env(self.user)
        if user and pwd:
            return f"mysql+aiomysql://{user}:{pwd}@{self.host}:{self.port}/{self.name}"
        return f"mysql+aiomysql://{self.host}:{self.port}/{self.name}"


class OSSConfig(BaseModel):
    """阿里云 OSS 配置"""

    endpoint: str = "oss-cn-hangzhou.aliyuncs.com"
    access_key_id: str = ""
    access_key_secret: str = ""
    bucket_name: str = ""
    bucket_host: str = ""

    def is_configured(self) -> bool:
        return all([
            self.endpoint,
            _resolve_env(self.access_key_id),
            _resolve_env(self.access_key_secret),
            self.bucket_name,
        ])

    @property
    def resolved_access_key_id(self) -> str:
        return _resolve_env(self.access_key_id)

    @property
    def resolved_access_key_secret(self) -> str:
        return _resolve_env(self.access_key_secret)


class DashScopeConfig(BaseModel):
    """阿里云 DashScope 配置"""

    api_key: str = ""
    base_url: str = "https://dashscope.aliyuncs.com/api/v1"

    def is_configured(self) -> bool:
        return bool(_resolve_env(self.api_key))

    @property
    def resolved_api_key(self) -> str:
        return _resolve_env(self.api_key)


class TimezoneConfig(BaseModel):
    """时区配置"""

    timezone: str = "Asia/Shanghai"


class AppConfig(BaseModel):
    """应用总配置"""

    log_level: str = "info"
    models: list[ModelConfig] = []
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    oss: OSSConfig = Field(default_factory=OSSConfig)
    dashscope: DashScopeConfig = Field(default_factory=DashScopeConfig)
    timezone: TimezoneConfig = Field(default_factory=TimezoneConfig)

    def get_model_config(self, name: str | None) -> ModelConfig | None:
        """根据名称查找模型配置"""
        if name is None and self.models:
            return self.models[0]
        for m in self.models:
            if m.name == name:
                return m
        return None


# ── 环境变量解析 ─────────────────────────────────────────────────


def _resolve_env(value: str) -> str:
    """解析 ${VAR} 格式的环境变量引用"""
    if not isinstance(value, str):
        return value
    if value.startswith("$"):
        env_var = value[1:]
        return os.getenv(env_var, value)
    return value


def _resolve_env_recursive(data: Any) -> Any:
    """递归解析数据结构中的 ${VAR} 引用"""
    if isinstance(data, dict):
        return {k: _resolve_env_recursive(v) for k, v in data.items()}
    if isinstance(data, list):
        return [_resolve_env_recursive(v) for v in data]
    if isinstance(data, str):
        return _resolve_env(data)
    return data


# ── 配置加载 ─────────────────────────────────────────────────────


def _find_config_file() -> Path:
    """查找 config.yaml 文件"""
    # 1. 环境变量指定
    env_path = os.getenv("PRACTICE_CONFIG_PATH")
    if env_path:
        p = Path(env_path)
        if p.exists():
            return p

    # 2. 当前目录
    cwd = Path.cwd() / "config.yaml"
    if cwd.exists():
        return cwd

    # 3. backend 目录
    backend = Path(__file__).resolve().parents[1] / "config.yaml"
    if backend.exists():
        return backend

    raise FileNotFoundError(
        "config.yaml not found. Set PRACTICE_CONFIG_PATH env var or "
        "place config.yaml in the current directory or backend/ directory."
    )


def _map_database_config(raw: dict) -> DatabaseConfig:
    """将 config.yaml 中的 database 段映射为 DatabaseConfig"""
    db = raw.get("database", {})
    return DatabaseConfig(
        host=db.get("roleplay_db_host", raw.get("roleplay_db_host", "localhost")),
        port=db.get("roleplay_db_port", raw.get("roleplay_db_port", 3306)),
        name=db.get("roleplay_db_name", raw.get("roleplay_db_name", "deerflow_roleplay")),
        user=db.get("roleplay_db_user", raw.get("roleplay_db_user", "")),
        password=db.get("roleplay_db_password", raw.get("roleplay_db_password", "")),
    )


def _map_oss_config(raw: dict) -> OSSConfig:
    """将 config.yaml 中的 oss 段映射为 OSSConfig"""
    oss = raw.get("oss", {})
    return OSSConfig(
        endpoint=oss.get("endpoint", "oss-cn-hangzhou.aliyuncs.com"),
        access_key_id=oss.get("access_key_id", ""),
        access_key_secret=oss.get("access_key_secret", ""),
        bucket_name=oss.get("bucket_name", ""),
        bucket_host=oss.get("bucket_host", ""),
    )


def _map_dashscope_config(raw: dict) -> DashScopeConfig:
    """将 config.yaml 中的 dashscope 段映射为 DashScopeConfig"""
    ds = raw.get("dashscope", {})
    return DashScopeConfig(
        api_key=ds.get("api_key", ""),
        base_url=ds.get("base_url", "https://dashscope.aliyuncs.com/api/v1"),
    )


@lru_cache(maxsize=1)
def load_config(config_path: str | None = None) -> AppConfig:
    """加载配置（带缓存）"""
    if config_path:
        path = Path(config_path)
    else:
        path = _find_config_file()

    logger.info(f"Loading config from: {path}")
    with open(path, encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    # 递归解析环境变量
    raw = _resolve_env_recursive(raw)

    # 构建配置对象
    models = []
    for m in raw.get("models", []):
        models.append(ModelConfig(
            name=m.get("name", ""),
            display_name=m.get("display_name"),
            use=m.get("use", "langchain_openai:ChatOpenAI"),
            model=m.get("model", ""),
            api_key=m.get("api_key", ""),
            base_url=m.get("base_url", ""),
            request_timeout=m.get("request_timeout", 120.0),
            max_retries=m.get("max_retries", 3),
            max_tokens=m.get("max_tokens", 8192),
            temperature=m.get("temperature", 0.7),
        ))

    return AppConfig(
        log_level=raw.get("log_level", "info"),
        models=models,
        database=_map_database_config(raw),
        oss=_map_oss_config(raw),
        dashscope=_map_dashscope_config(raw),
        timezone=TimezoneConfig(timezone=raw.get("timezone", {}).get("timezone", "Asia/Shanghai") if isinstance(raw.get("timezone"), dict) else raw.get("timezone", "Asia/Shanghai")),
    )


def get_config() -> AppConfig:
    """获取配置单例"""
    return load_config()


def reload_config() -> AppConfig:
    """强制重新加载配置"""
    load_config.cache_clear()
    return load_config()
