"""
iso8583_api POST /api/v1/messages/generate エンドポイントのテスト。
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from iso8583_api.app import app


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


class TestGenerateEndpoint:
    def test_generate_returns_200_with_valid_request(self, client: TestClient):
        mock_result = bytearray(b"\x00\x00\x00\x01")
        with patch("iso8583_api.routers.messages.build_generate_use_case") as mock_factory:
            mock_uc = MagicMock()
            mock_uc.execute.return_value = mock_result
            mock_factory.return_value = mock_uc

            response = client.post(
                "/api/v1/messages/generate",
                json={"mti": "0200", "fields": {"processing_code": "000000"}},
            )
        assert response.status_code == 200

    def test_generate_returns_422_with_invalid_mti(self, client: TestClient):
        response = client.post(
            "/api/v1/messages/generate",
            json={"mti": "XXXX", "fields": {}},
        )
        assert response.status_code in (400, 422)
