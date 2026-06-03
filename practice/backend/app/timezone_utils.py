"""时区工具函数 — 从 deerflow/roleplay/timezone_utils.py 迁移"""

import pytz
from datetime import datetime

from app.config import get_config


def get_timezone():
    """从配置获取时区对象"""
    config = get_config()
    timezone_str = config.timezone.timezone if config.timezone else "Asia/Shanghai"

    # 处理 UTC+X 格式
    if timezone_str.startswith("UTC") and "+" in timezone_str:
        try:
            offset_hours = int(timezone_str.split("+")[1])
            return pytz.FixedOffset(offset_hours * 60)
        except (ValueError, IndexError):
            pass

    # 使用 pytz 时区
    try:
        return pytz.timezone(timezone_str)
    except pytz.UnknownTimeZoneError:
        return pytz.timezone("Asia/Shanghai")


def now_local() -> datetime:
    """获取当前本地时间"""
    tz = get_timezone()
    return datetime.now(tz)


def to_local_time(dt: datetime) -> datetime:
    """将时间转换为本地时间"""
    tz = get_timezone()
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=pytz.UTC)
    return dt.astimezone(tz)
