import pytest


@pytest.mark.asyncio
async def test_health_check_returns_200(client):
    response = await client.get("/health")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_health_check_returns_ok_status(client):
    response = await client.get("/health")
    data = response.json()
    assert data["status"] == "ok"
    assert "service" in data
