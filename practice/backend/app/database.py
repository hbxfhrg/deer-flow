"""MySQL 数据库连接管理 — 从 deerflow/roleplay/__init__.py 简化而来"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.config import get_config

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """所有 ORM 模型的基类"""
    pass


_engine = None
_session_factory = None

# SQL 日志开关
_SQL_LOGGING_ENABLED = False


def init_db():
    """初始化数据库连接"""
    global _engine, _session_factory

    config = get_config()
    db_url = config.database.url

    logger.info(f"Connecting to MySQL: {config.database.host}:{config.database.port}/{config.database.name}")

    _engine = create_async_engine(
        db_url,
        pool_size=10,
        max_overflow=20,
        echo=False,
        pool_pre_ping=True,
        pool_recycle=3600,
    )

    if _SQL_LOGGING_ENABLED:
        from sqlalchemy import event

        def _log_sql(conn, cursor, statement, parameters, context, executemany):
            print(f"\n[SQL] {statement}")
            if parameters:
                print(f"[SQL PARAMS] {parameters}\n")

        event.listen(_engine.sync_engine, "before_cursor_execute", _log_sql)

    _session_factory = async_sessionmaker(_engine, expire_on_commit=False)
    logger.info("Database connection established")


def get_session_factory():
    if _session_factory is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _session_factory


@asynccontextmanager
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话的上下文管理器"""
    if _session_factory is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    async with _session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def close_db():
    """关闭数据库连接"""
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _session_factory = None
        logger.info("Database connection closed")


def is_db_initialized() -> bool:
    return _engine is not None and _session_factory is not None
