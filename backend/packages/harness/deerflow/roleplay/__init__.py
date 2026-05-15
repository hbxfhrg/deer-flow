from contextlib import asynccontextmanager
from functools import wraps
from typing import AsyncGenerator, Callable

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from deerflow.config.database_config import DatabaseConfig

class RoleplayBase(DeclarativeBase):
    pass

_engine = None
_session_factory = None

def init_roleplay_db(config: DatabaseConfig):
    global _engine, _session_factory
    
    db_url = config.get_roleplay_db_url
    _engine = create_async_engine(
        db_url,
        pool_size=10,
        max_overflow=20,
        echo=False,
        pool_pre_ping=True,
        pool_recycle=3600
    )
    _session_factory = async_sessionmaker(_engine, expire_on_commit=False)

def get_session_factory():
    if _session_factory is None:
        raise RuntimeError("Roleplay database not initialized. Call init_roleplay_db first.")
    return _session_factory

@asynccontextmanager
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    if _session_factory is None:
        raise RuntimeError("Roleplay database not initialized. Call init_roleplay_db first.")
    async with _session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise

def get_db_dependency() -> Callable[[], AsyncGenerator[AsyncSession, None]]:
    def _get_db() -> AsyncGenerator[AsyncSession, None]:
        return get_db()
    return _get_db

async def create_roleplay_tables():
    if _engine is None:
        raise RuntimeError("Roleplay database not initialized")
    async with _engine.begin() as conn:
        await conn.run_sync(RoleplayBase.metadata.create_all)

async def close_roleplay_db():
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _session_factory = None

def is_roleplay_db_initialized() -> bool:
    return _engine is not None and _session_factory is not None