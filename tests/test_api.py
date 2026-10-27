import pytest


@pytest.mark.asyncio
async def test_health(client):
    res = await client.get("/api/v1/health")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ok"
    assert body["db"] == "ok"


@pytest.mark.asyncio
async def test_analyze_and_records_flow(client):
    res = await client.post("/api/v1/analyze", json={"text": "物流超快，质量很好，非常满意！"})
    assert res.status_code == 200
    body = res.json()
    assert body["polarity"] == "positive"
    assert 0 <= body["confidence"] <= 1
    record_id = body["record_id"]

    # 列表
    res = await client.get("/api/v1/records")
    assert res.status_code == 200
    items = res.json()["items"]
    assert any(item["id"] == record_id for item in items)

    # 筛选
    res = await client.get("/api/v1/records", params={"polarity": "positive"})
    assert all(item["polarity"] == "positive" for item in res.json()["items"])

    # 详情
    res = await client.get(f"/api/v1/records/{record_id}")
    assert res.status_code == 200
    assert res.json()["content"].startswith("物流超快")

    # 删除
    res = await client.delete(f"/api/v1/records/{record_id}")
    assert res.status_code == 204
    res = await client.get(f"/api/v1/records/{record_id}")
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_analyze_validation(client):
    res = await client.post("/api/v1/analyze", json={"text": ""})
    assert res.status_code == 422
    res = await client.post("/api/v1/analyze", json={"text": "x" * 2001})
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_record_not_found(client):
    res = await client.get("/api/v1/records/99999")
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_static_index(client):
    res = await client.get("/")
    assert res.status_code == 200
    assert "评价情绪分析" in res.text
