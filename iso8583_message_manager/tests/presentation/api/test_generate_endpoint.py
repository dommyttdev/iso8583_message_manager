"""
POST /api/v1/messages/generate のルーターユニットテスト。

テスト戦略 doc/api/api_design.md §9.3 API-GEN-01〜10 に対応。
ユースケース層はモックで差し替え、Presentation 層の責務のみを検証する。
"""
import base64
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from iso8583_manager.core.exceptions import InvalidMtiError, MessageEncodeError
from iso8583_manager.presentation.api.app import app
from iso8583_manager.presentation.api.routers.messages import get_generate_use_case


@pytest.fixture
def mock_use_case(request: pytest.FixtureRequest) -> MagicMock:
    """GenerateMessageUseCase のモック。デフォルトでは有効なバイト列を返す。"""
    mock = MagicMock()
    mock.execute.return_value = bytearray(b"\x02\x00\x00\x00\x00\x00\x00\x00")
    app.dependency_overrides[get_generate_use_case] = lambda: mock
    yield mock
    app.dependency_overrides.clear()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


class TestGenerateEndpointSuccess:
    def test_api_gen_01_hex_output(
        self, client: TestClient, mock_use_case: MagicMock
    ) -> None:
        """API-GEN-01: 正常リクエスト（output_format: hex） → 200, hex 文字列。"""
        response = client.post(
            "/api/v1/messages/generate",
            json={
                "mti": "0200",
                "fields": {"primary_account_number": "4111111111111111"},
                "output_format": "hex",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "encoded_message" in data
        # hex 文字列であることを確認
        bytes.fromhex(data["encoded_message"])
        assert data["output_format"] == "hex"
        assert data["mti"] == "0200"

    def test_api_gen_02_base64_output(
        self, client: TestClient, mock_use_case: MagicMock
    ) -> None:
        """API-GEN-02: output_format: base64 → 200, Base64 文字列。"""
        response = client.post(
            "/api/v1/messages/generate",
            json={"mti": "0200", "fields": {}, "output_format": "base64"},
        )
        assert response.status_code == 200
        data = response.json()
        # Base64 文字列であることを確認
        base64.b64decode(data["encoded_message"])
        assert data["output_format"] == "base64"

    def test_api_gen_03_fields_omitted(
        self, client: TestClient, mock_use_case: MagicMock
    ) -> None:
        """API-GEN-03: フィールド省略（MTI のみ） → 200。"""
        response = client.post(
            "/api/v1/messages/generate",
            json={"mti": "0200"},
        )
        assert response.status_code == 200


class TestGenerateEndpointValidationErrors:
    def test_api_gen_04_mti_format_invalid(
        self, client: TestClient, mock_use_case: MagicMock
    ) -> None:
        """API-GEN-04: mti 形式不正（3桁） → 422, パターン違反。"""
        response = client.post(
            "/api/v1/messages/generate",
            json={"mti": "020"},
        )
        assert response.status_code == 422

    def test_api_gen_06_unknown_field_name(
        self, client: TestClient, mock_use_case: MagicMock
    ) -> None:
        """API-GEN-06: 未定義フィールド名 → 422, additionalProperties 違反。"""
        response = client.post(
            "/api/v1/messages/generate",
            json={"mti": "0200", "fields": {"unknown_field": "xxx"}},
        )
        assert response.status_code == 422

    def test_api_gen_07_field_max_length_exceeded(
        self, client: TestClient, mock_use_case: MagicMock
    ) -> None:
        """API-GEN-07: フィールド値が maxLength 超過 → 422。"""
        response = client.post(
            "/api/v1/messages/generate",
            json={
                "mti": "0200",
                # primary_account_number max=19、20桁はNG
                "fields": {"primary_account_number": "12345678901234567890"},
            },
        )
        assert response.status_code == 422

    def test_api_gen_08_fixed_field_length_mismatch(
        self, client: TestClient, mock_use_case: MagicMock
    ) -> None:
        """API-GEN-08: 固定長フィールドの長さ不一致 → 422, min/max_length 違反。"""
        response = client.post(
            "/api/v1/messages/generate",
            json={
                "mti": "0200",
                # processing_code は固定長6桁（min_length=6）、5桁はNG
                "fields": {"processing_code": "12345"},
            },
        )
        assert response.status_code == 422

    def test_api_gen_09_mti_missing(
        self, client: TestClient, mock_use_case: MagicMock
    ) -> None:
        """API-GEN-09: mti キー欠落 → 422, required フィールド欠落。"""
        response = client.post(
            "/api/v1/messages/generate",
            json={"fields": {}},
        )
        assert response.status_code == 422


class TestGenerateEndpointBusinessErrors:
    def test_api_gen_05_invalid_mti_value(self, client: TestClient) -> None:
        """API-GEN-05: mti 未定義クラス（"0900"） → 400, INVALID_MTI。"""
        # モックなし（実際の MTI バリデーションを通す）
        response = client.post(
            "/api/v1/messages/generate",
            json={"mti": "0900", "fields": {}},
        )
        assert response.status_code == 400
        data = response.json()
        assert data["error_code"] == "INVALID_MTI"

    def test_api_gen_10_encode_failure(
        self, client: TestClient, mock_use_case: MagicMock
    ) -> None:
        """API-GEN-10: エンコード失敗（アダプターエラー） → 400, MESSAGE_ENCODE_ERROR。"""
        mock_use_case.execute.side_effect = MessageEncodeError("エンコード失敗")
        response = client.post(
            "/api/v1/messages/generate",
            json={"mti": "0200", "fields": {}},
        )
        assert response.status_code == 400
        data = response.json()
        assert data["error_code"] == "MESSAGE_ENCODE_ERROR"
