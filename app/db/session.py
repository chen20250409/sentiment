from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings

settings = get_settings()

_engine_kwargs: dict = {}
if settings.db_url.startswith("sqlite"):
    # 内存/文件 SQLite 供测试使用，需共享同一连接
    _engine_kwargs["poolclass"] = StaticPool
    _engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    _engine_kwargs.update(pool_pre_ping=True, pool_recycle=1800, pool_size=5, max_overflow=5)

engine = create_async_engine(settings.db_url, **_engine_kwargs)

SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_db():
    async with SessionLocal() as session:
        yield session
