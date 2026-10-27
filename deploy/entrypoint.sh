#!/bin/sh
set -e

echo "[entrypoint] waiting for database..."
python - <<'PYEOF'
import asyncio, os, sys, time

import aiomysql

host = os.environ.get("DB_HOST", "mysql")
port = int(os.environ.get("DB_PORT", "3306"))
user = os.environ.get("DB_USER", "nlp")
pwd = os.environ.get("DB_PASSWORD", "")
db = os.environ.get("DB_NAME", "sentiment")

async def try_connect():
    conn = await aiomysql.connect(host=host, port=port, user=user, password=pwd, db=db)
    conn.close()

for i in range(60):
    try:
        asyncio.run(try_connect())
        print("[entrypoint] database is ready")
        sys.exit(0)
    except Exception as e:
        print(f"[entrypoint] db not ready ({i + 1}/60): {e}")
        time.sleep(2)
print("[entrypoint] database unreachable, giving up")
sys.exit(1)
PYEOF

echo "[entrypoint] starting uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
