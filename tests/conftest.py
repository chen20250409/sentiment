import os

os.environ["DATABASE_URL"] = "sqlite+aiosqlite://"  # 测试用内存 SQLite
os.environ["DB_PASSWORD"] = "test"

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.db.base import Base
from app.db.session import engine
from app.main import create_app


@pytest_asyncio.fixture
async def client():
    app = create_app()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.fixture
def anyio_backend():
    return "asyncio"
