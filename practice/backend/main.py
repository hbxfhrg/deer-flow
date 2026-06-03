"""DeerFlow Practice Backend — 独立对练后端入口

启动方式:
    cd practice/backend
    uvicorn main:app --reload --host 0.0.0.0 --port 8001
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_config, load_config
from app.database import init_db, close_db
from app.routers import roleplay, tts, asr, oss

# ── 日志配置 ──────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ── 应用生命周期 ─────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用启动/关闭时的资源管理"""
    # 启动时加载配置
    config = load_config()
    logging_level = getattr(logging, config.log_level.upper(), logging.INFO)
    logging.getLogger("app").setLevel(logging_level)
    logging.getLogger("roleplay").setLevel(logging_level)
    logger.info(f"Log level: {config.log_level}")

    # 初始化数据库连接
    init_db()
    logger.info(f"Database: {config.database.host}:{config.database.port}/{config.database.name}")

    # DashScope 状态
    if config.dashscope.is_configured():
        logger.info("DashScope: configured")
    else:
        logger.warning("DashScope: NOT configured (TTS/ASR will not work)")

    # OSS 状态
    if config.oss.is_configured():
        logger.info(f"OSS: {config.oss.bucket_name} @ {config.oss.endpoint}")
    else:
        logger.warning("OSS: NOT configured (audio file upload will not work)")

    # 模型列表
    for m in config.models:
        logger.info(f"Model: {m.name} ({m.model})")

    yield

    # 关闭时释放资源
    await close_db()
    logger.info("Backend shutdown complete")


# ── 创建应用 ──────────────────────────────────────────────────────

app = FastAPI(
    title="DeerFlow Practice Backend",
    description="对练模块独立后端 API — 场景管理、课程管理、自由式对练、语音合成/识别",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(roleplay.router)
app.include_router(tts.router)
app.include_router(asr.router)
app.include_router(oss.router)


# ── 健康检查 ──────────────────────────────────────────────────────

@app.get("/health")
async def health():
    from app.database import is_db_initialized

    config = get_config()
    return {
        "status": "ok",
        "version": "1.0.0",
        "db": "connected" if is_db_initialized() else "disconnected",
        "dashscope_configured": config.dashscope.is_configured(),
        "oss_configured": config.oss.is_configured(),
        "models_count": len(config.models),
    }


# ── 直接运行 ──────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
