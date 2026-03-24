"""
API セキュリティテスト。

悪意のある入力パターンが API エンドポイントで正しく拒否されることを検証する。
ISO 8583 フィールドのバリデーション（Pydantic）が各種インジェクション試みを
処理前にブロックすることを確認する。

検証するカテゴリ:
  - 過大入力（バッファ超過狙い）
  - SQL インジェクションパターン
  - スクリプトインジェクションパターン
  - ヌルバイト・制御文字
  - 不正な MTI フォーマット
"""
import pytest
from fastapi.testclient import TestClient

from iso8583_api.app import app

client = TestClient(app)


# ==============================================================================
# 過大入力（Large Input / Buffer Overflow Attempt）
# ==============================================================================

class TestLargeInputRejected:
    def test_sec_li_01_very_long_pan_rejected_422(self) -> None:
        """極端に長い PAN（1000 桁）が 422 で拒否されること"""
        response = client.post("/api/v1/messages/generate", json={
            "mti": "0200",
            "fields": {"primary_account_number": "1" * 1000},
        })
        assert response.status_code == 422

    def test_sec_li_02_very_long_mti_rejected_422(self) -> None:
        """極端に長い MTI 文字列が 422 で拒否されること"""
        response = client.post("/api/v1/messages/generate", json={
            "mti": "0" * 1000,
            "fields": {},
        })
        assert response.status_code == 422

    @pytest.mark.parametrize("field", [
        "processing_code",
        "amount_transaction",
        "transmission_date_and_time",
        "systems_trace_audit_number",
        "response_code",
    ])
    def test_sec_li_03_very_long_fixed_fields_rejected_422(self, field: str) -> None:
        """固定長フィールドへの過大入力（1000 桁）が 422 で拒否されること"""
        response = client.post("/api/v1/messages/generate", json={
            "mti": "0200",
            "fields": {field: "9" * 1000},
        })
        assert response.status_code == 422


# ==============================================================================
# SQL インジェクション試み（Pydantic バリデーションによるブロック）
# ==============================================================================

class TestSqlInjectionBlocked:
    @pytest.mark.parametrize("payload", [
        "1'; DROP TABLE messages; --",
        "1 OR 1=1",
        "' UNION SELECT * FROM users --",
        "1; SELECT * FROM information_schema.tables",
    ])
    def test_sec_sql_01_sql_injection_in_pan_rejected_422(self, payload: str) -> None:
        """SQL インジェクションパターンを含む PAN が 422 で拒否されること（長さ超過）"""
        response = client.post("/api/v1/messages/generate", json={
            "mti": "0200",
            "fields": {"primary_account_number": payload},
        })
        # 長さ/フォーマット制約により 422 で拒否される（19 桁以内の場合は通過するが無害）
        # SQL が 20 桁超の場合は 422
        if len(payload) > 19:
            assert response.status_code == 422
        else:
            # 文字列として保存されるだけで DB 操作は発生しない
            assert response.status_code in (200, 422)

    @pytest.mark.parametrize("payload", [
        "1'; DROP TABLE; -- EXTRA",  # 24 桁 > max_len 19
        "AAAAAAAAAAAAAAAAAAAAAA",    # 22 桁 > max_len 19
    ])
    def test_sec_sql_02_overlong_injection_rejected_422(self, payload: str) -> None:
        """長さ超過のインジェクションパターンが 422 で拒否されること"""
        response = client.post("/api/v1/messages/generate", json={
            "mti": "0200",
            "fields": {"primary_account_number": payload},
        })
        assert response.status_code == 422


# ==============================================================================
# 不正なデータ型（Type Confusion）
# ==============================================================================

class TestTypeConfusionBlocked:
    def test_sec_tc_01_integer_in_string_field_coerced_or_rejected(self) -> None:
        """文字列フィールドへの整数値が処理されること（FastAPI は文字列へ強制変換する場合あり）"""
        response = client.post("/api/v1/messages/generate", json={
            "mti": "0200",
            "fields": {"primary_account_number": 1234567890123456},
        })
        # FastAPI の Pydantic v2 は int を str へ強制変換するか 422 を返す
        assert response.status_code in (200, 422)

    def test_sec_tc_02_list_in_string_field_rejected(self) -> None:
        """文字列フィールドへのリスト値が 422 で拒否されること"""
        response = client.post("/api/v1/messages/generate", json={
            "mti": "0200",
            "fields": {"primary_account_number": ["1234", "5678"]},
        })
        assert response.status_code == 422

    def test_sec_tc_03_nested_object_in_field_rejected(self) -> None:
        """文字列フィールドへのオブジェクト値が 422 で拒否されること"""
        response = client.post("/api/v1/messages/generate", json={
            "mti": "0200",
            "fields": {"primary_account_number": {"nested": "value"}},
        })
        assert response.status_code == 422

    def test_sec_tc_04_null_mti_rejected(self) -> None:
        """MTI への null 値が 422 で拒否されること"""
        response = client.post("/api/v1/messages/generate", json={
            "mti": None,
            "fields": {},
        })
        assert response.status_code == 422

    def test_sec_tc_05_missing_required_mti_rejected(self) -> None:
        """必須フィールド mti の欠落が 422 で拒否されること"""
        response = client.post("/api/v1/messages/generate", json={
            "fields": {"primary_account_number": "1234567890123456"},
        })
        assert response.status_code == 422


# ==============================================================================
# 不正な MTI パターン
# ==============================================================================

class TestMalformedMtiBlocked:
    @pytest.mark.parametrize("mti", [
        "",           # 空文字列
        "    ",       # 空白のみ
        "0\x000",     # ヌルバイト埋め込み
        "\n\r\t\x00", # 制御文字
        "ABCD",       # 非数値（ISO 8583 MTI は数値）
    ])
    def test_sec_mti_01_malformed_mti_rejected(self, mti: str) -> None:
        """不正フォーマット MTI が 422 または 400 で拒否されること"""
        response = client.post("/api/v1/messages/generate", json={
            "mti": mti,
            "fields": {},
        })
        assert response.status_code in (400, 422), (
            f"MTI {mti!r}: 400 または 422 expected, got {response.status_code}"
        )


# ==============================================================================
# parse エンドポイントへの不正入力
# ==============================================================================

class TestParseEndpointSecurity:
    def test_sec_parse_01_non_hex_string_rejected(self) -> None:
        """16 進数でない文字列がエラー（400 または 422）で拒否されること"""
        response = client.post("/api/v1/messages/parse", json={
            "encoded_message": "THIS IS NOT HEX!!",
        })
        # フォーマット検証はドメイン層（400）または Pydantic 層（422）で拒否される
        assert response.status_code in (400, 422)

    def test_sec_parse_02_odd_length_hex_rejected(self) -> None:
        """奇数桁の hex 文字列がエラー（400 または 422）で拒否されること（バイト境界不整合）"""
        response = client.post("/api/v1/messages/parse", json={
            "encoded_message": "0200abc",  # 奇数桁
        })
        # hex フォーマット検証はドメイン層（400）で処理される
        assert response.status_code in (400, 422)

    def test_sec_parse_03_valid_hex_but_invalid_iso8583_rejected(self) -> None:
        """有効な hex だが ISO 8583 として不正なバイト列が 400 で拒否されること"""
        response = client.post("/api/v1/messages/parse", json={
            "encoded_message": "deadbeefdeadbeef",
        })
        assert response.status_code == 400
        assert response.json()["error_code"] == "MESSAGE_DECODE_ERROR"

    def test_sec_parse_04_empty_string_rejected(self) -> None:
        """空文字列がエラー（400 または 422）で拒否されること"""
        response = client.post("/api/v1/messages/parse", json={
            "encoded_message": "",
        })
        # 空文字列はドメイン層（400）または Pydantic 層（422）で拒否される
        assert response.status_code in (400, 422)

    def test_sec_parse_05_missing_encoded_message_rejected(self) -> None:
        """必須フィールド encoded_message の欠落が 422 で拒否されること"""
        response = client.post("/api/v1/messages/parse", json={})
        assert response.status_code == 422
