"""时区工具函数

从配置中读取时区设置，提供统一的时间处理接口。
"""

import pytz
from datetime import datetime
from typing import Optional

from deerflow.config.app_config import get_app_config


def get_timezone():
    """从配置获取时区对象"""
    config = get_app_config()
    timezone_str = config.timezone.timezone if config.timezone else "Asia/Shanghai"
    
    # 处理 UTC+X 格式
    if timezone_str.startswith("UTC") and "+" in timezone_str:
        try:
            offset_hours = int(timezone_str.split("+")[1])
            return pytz.FixedOffset(offset_hours * 60)
        except:
            pass
    
    # 使用 pytz 时区
    try:
        return pytz.timezone(timezone_str)
    except pytz.UnknownTimeZoneError:
        # 默认使用上海时区
        return pytz.timezone("Asia/Shanghai")


def now_local() -> datetime:
    """获取当前本地时间（根据配置的时区）"""
    tz = get_timezone()
    return datetime.now(tz)


def to_local_time(dt: datetime) -> datetime:
    """将时间转换为本地时间"""
    tz = get_timezone()
    if dt.tzinfo is None:
        # 假设没有时区信息的时间是 UTC 时间
        dt = dt.replace(tzinfo=pytz.UTC)
    return dt.astimezone(tz)


def to_local_time_str(dt: datetime) -> str:
    """将时间转换为本地时间并返回 ISO 格式字符串"""
    local_dt = to_local_time(dt)
    return local_dt.isoformat()
