"""
API 境界値テスト。

ISO 8583 フィールドの最小・最大・超過値が HTTP エンドポイントを通じて
正しく受け入れ / 拒否されることを検証する。
FastAPI の Pydantic バリデーション（422）とドメインバリデーション（400）の
両レイヤーを対象とする。
"""
import pytest
from fastapi.testclient import TestClient

from iso8583_api.app import app

client = TestClient(app)


# ==============================================================================
# PAN (primary_account_number) 境界値
# ==============================================================================

class TestPanApiBoundary:
    def test_bv_api_pan_01_min_length_1_accepted(self) -> None:
        """PAN 1 桁（最小）が 200 を返すこと"""
        response = client.post("/api/v1/messages/generate", json={
            "mti": "0200",
            "fields": {"primary_account_number": "1"},
        })
        assert response.status_code == 200

    def test_bv_api_pan_02_max_length_19_accepted(self) -> None:
        """PAN 19 桁（最大）が 200 を返すこと"""
        response = client.post("/api/v1/messages/generate", json={
            "mti": "0200",
            "fields": {"primary_account_number": "1234567890123456789"},
        })
        assert response.status_code == 200

    def test_bv_api_pan_03_empty_string_rejected_422(self) -> None:
        """PAN 空文字列が 422 を返すこと（Pydantic バリデーション）"""
        response = client.post("/api/v1/messages/generate", json={
            "mti": "0200",
            "fields": {"primary_account_number": ""},
        })
        assert response.status_code == 422

    def test_bv_api_pan_04_over_max_length_rejected_422(self) -> None:
        """PAN 20 桁（最大超過）が 422 を返すこと"""
        response = client.post("/api/v1/messages/generate", json={
            "mti": "0200",
            "fields": {"primary_account_number": "12345678901234567890"},
        })
        assert response.status_code == 422


# ==============================================================================
# 固定長フィールドの境界値（processing_code, amount_transaction, etc.）
# ==============================================================================

class TestFixedLengthFieldsBoundary:
    @pytest.mark.parametrize("field,valid_value,short_value,long_value", [
        ("processing_code",            "123456",       "12345",        "1234567"),
        ("amount_transaction",         "000000001000", "00000000100",  "0000000010000"),
        ("transmission_date_and_time", "1234567890",   "123456789",    "12345678901"),
        ("systems_trace_audit_number", "111222",       "11122",        "1112222"),
        ("response_code",              "00",           "0",            "000"),
    ])
    def test_bv_api_fixed_01_exact_length_accepted(
        self,
        field: str,
        valid_value: str,
        short_value: str,
        long_value: str,
    ) -> None:
        """固定長フィールドの正確な長さが 200 を返すこと"""
        response = client.post("/api/v1/messages/generate", json={
            "mti": "0200",
            "fields": {field: valid_value},
        })
        assert response.status_code == 200, f"{field}={valid_value!r}: {response.json()}"

    @pytest.mark.parametrize("field,valid_value,short_value,long_value", [
        ("processing_code",            "123456",       "12345",        "1234567"),
        ("amount_transaction",         "000000001000", "00000000100",  "0000000010000"),
        ("transmission_date_and_time", "1234567890",   "123456789",    "12345678901"),
        ("systems_trace_audit_number", "111222",       "11122",        "1112222"),
        ("response_code",              "00",           "0",            "000"),
    ])
    def test_bv_api_fixed_02_too_short_rejected_422(
        self,
        field: str,
        valid_value: str,
        short_value: str,
        long_value: str,
    ) -> None:
        """固定長フィールドの短い値が 422 を返すこと"""
        response = client.post("/api/v1/messages/generate", json={
            "mti": "0200",
            "fields": {field: short_value},
        })
        assert response.status_code == 422, f"{field}={short_value!r}: 422 expected"

    @pytest.mark.parametrize("field,valid_value,short_value,long_value", [
        ("processing_code",            "123456",       "12345",        "1234567"),
        ("amount_transaction",         "000000001000", "00000000100",  "0000000010000"),
        ("transmission_date_and_time", "1234567890",   "123456789",    "12345678901"),
        ("systems_trace_audit_number", "111222",       "11122",        "1112222"),
        ("response_code",              "00",           "0",            "000"),
    ])
    def test_bv_api_fixed_03_too_long_rejected_422(
        self,
        field: str,
        valid_value: str,
        short_value: str,
        long_value: str,
    ) -> None:
        """固定長フィールドの長い値が 422 を返すこと"""
        response = client.post("/api/v1/messages/generate", json={
            "mti": "0200",
            "fields": {field: long_value},
        })
        assert response.status_code == 422, f"{field}={long_value!r}: 422 expected"


# ==============================================================================
# MTI フォーマット境界値
# ==============================================================================

class TestMtiBoundary:
    @pytest.mark.parametrize("mti", ["0100", "0200", "0400", "0800"])
    def test_bv_api_mti_01_valid_4digit_mtis(self, mti: str) -> None:
        """有効な 4 桁 MTI が全て受け入れられること"""
        response = client.post("/api/v1/messages/generate", json={
            "mti": mti,
            "fields": {"primary_account_number": "1234567890123456"},
        })
        assert response.status_code == 200, f"MTI {mti}: {response.json()}"

    @pytest.mark.parametrize("mti", ["020", "02000", "XXXX", ""])
    def test_bv_api_mti_02_invalid_format_rejected_422(self, mti: str) -> None:
        """4 桁以外のMTI が 422 を返すこと"""
        response = client.post("/api/v1/messages/generate", json={
            "mti": mti,
            "fields": {},
        })
        assert response.status_code == 422, f"MTI {mti!r}: 422 expected"

    def test_bv_api_mti_03_unknown_class_rejected_400(self) -> None:
        """未定義クラスの MTI が 400 INVALID_MTI を返すこと"""
        response = client.post("/api/v1/messages/generate", json={
            "mti": "0900",
            "fields": {},
        })
        assert response.status_code == 400
        assert response.json()["error_code"] == "INVALID_MTI"


# ==============================================================================
# 空フィールドセット
# ==============================================================================

class TestEmptyFieldsBoundary:
    def test_bv_api_empty_01_no_fields_generates_mti_only(self) -> None:
        """フィールド未指定でも MTI のみのメッセージが生成されること"""
        response = client.post("/api/v1/messages/generate", json={
            "mti": "0200",
            "fields": {},
        })
        assert response.status_code == 200
        body = response.json()
        assert body["byte_length"] > 0

    def test_bv_api_empty_02_null_fields_same_as_empty(self) -> None:
        """全フィールド None は空フィールドと同等であること"""
        response = client.post("/api/v1/messages/generate", json={
            "mti": "0200",
            "fields": {
                "primary_account_number": None,
                "processing_code": None,
            },
        })
        assert response.status_code == 200
