"""
iso8583_api GET /health エンドポイントのテスト。
"""
import pytest
from fastapi.testclient import TestClient
from iso8583_api.app import app


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


class TestHealthEndpoint:
    def test_health_returns_200(self, client: TestClient):
        response = client.get("/api/v1/health")
        assert response.status_code == 200

    def test_health_returns_status_ok(self, client: TestClient):
        response = client.get("/api/v1/health")
        data = response.json()
        assert data.get("status") == "ok"
