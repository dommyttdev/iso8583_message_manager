"""
GET /api/v1/health のルーターユニットテスト。

テスト戦略 doc/api/api_design.md §9.3 API-HLT-01 に対応。
"""
from fastapi.testclient import TestClient

from iso8583_manager.presentation.api.app import app

client = TestClient(app)


class TestHealthEndpoint:
    def test_api_hlt_01_health_returns_ok(self) -> None:
        """API-HLT-01: GET /api/v1/health → 200, {"status": "ok"}。"""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data
