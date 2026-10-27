import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.v1 import analyze, health, records
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.db.base import Base
from app.db.session import engine

logger = logging.getLogger(__name__)
STATIC_DIR = Path(__file__).resolve().parent / "static"


async def _wait_and_create_tables() -> None:
    """启动时等待数据库就绪并建表（对 MySQL 部署是首次建表，对本地开发幂等）。"""
    for attempt in range(1, 31):
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("database ready, tables ensured")
            return
        except Exception as exc:  # noqa: BLE001
            logger.warning("db not ready (%s/30): %s", attempt, exc)
            await asyncio.sleep(2)
    raise RuntimeError("database unreachable after 30 attempts")


def create_app() -> FastAPI:
    settings = get_settings()
    setup_logging()

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        await _wait_and_create_tables()
        yield

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="电商评价情绪分析 API：正向 / 负面 / 中性 + 置信度",
        lifespan=lifespan,
    )
    app.include_router(health.router, prefix="/api/v1")
    app.include_router(analyze.router, prefix="/api/v1")
    app.include_router(records.router, prefix="/api/v1")
    app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
    return app


app = create_app()
