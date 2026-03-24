"""
API 統合テスト（クロスパッケージ）。

実際の PyIso8583Adapter・実 spec ファイルを使い、HTTP エンドポイントを
End-to-End で検証する。dependency_overrides は一切使用しない。

検証するシナリオ:
  - 認証リクエスト（MTI 0200）の生成と解析往復
  - 有効な各 MTI クラスでの生成成功
  - 全フィールドを同時使用した最大メッセージの生成・解析
  - MTI の各コンポーネント説明が正しく返ること
  - 不正 MTI が API 全レイヤーで正しく拒否されること（400 INVALID_MTI）
"""
import pytest
from fastapi.testclient import TestClient

from iso8583_api.app import app

client = TestClient(app)

# 全フィールドを含む最大メッセージ用データ
_ALL_FIELDS = {
    "primary_account_number": "1234567890123456",
    "processing_code": "123456",
    "amount_transaction": "000000001000",
    "transmission_date_and_time": "1234567890",
    "systems_trace_audit_number": "111222",
    "response_code": "00",
}


# ==============================================================================
# シナリオ 1: 認証リクエスト（MTI 0200）の E2E 生成
# ==============================================================================

class TestAuthorizationRequestE2E:
    def test_int_01_generate_authorization_request_returns_200(self) -> None:
        """MTI 0200 の生成が 200 を返し必須フィールドを含むこと"""
        response = client.post("/api/v1/messages/generate", json={
            "mti": "0200",
            "fields": {
                "primary_account_number": "1234567890123456",
                "processing_code": "123456",
                "amount_transaction": "000000001000",
                "transmission_date_and_time": "1234567890",
                "systems_trace_audit_number": "111222",
            },
        })
        assert response.status_code == 200
        body = response.json()
        assert body["mti"] == "0200"
        assert body["output_format"] == "hex"
        assert body["byte_length"] > 0
        assert len(body["encoded_message"]) > 0

    def test_int_02_generate_hex_is_valid_bytes(self) -> None:
        """generate の encoded_message が有効な hex 文字列であること"""
        response = client.post("/api/v1/messages/generate", json={
            "mti": "0200",
            "fields": {"primary_account_number": "1234567890123456"},
        })
        assert response.status_code == 200
        hex_str = response.json()["encoded_message"]
        raw = bytes.fromhex(hex_str)
        assert len(raw) > 0

    def test_int_03_byte_length_matches_hex(self) -> None:
        """byte_length が encoded_message の実際のバイト数と一致すること"""
        response = client.post("/api/v1/messages/generate", json={
            "mti": "0200",
            "fields": {"primary_account_number": "1234567890123456"},
        })
        assert response.status_code == 200
        body = response.json()
        assert body["byte_length"] == len(bytes.fromhex(body["encoded_message"]))


# ==============================================================================
# シナリオ 2: API 経由でメッセージ生成→パースの往復整合性
# ==============================================================================

class TestGenerateParseRoundtrip:
    def test_int_04_roundtrip_fields_preserved(self) -> None:
        """generate → parse でフィールド値が完全に一致すること"""
        fields = {
            "primary_account_number": "1234567890123456",
            "processing_code": "123456",
            "amount_transaction": "000000001000",
            "transmission_date_and_time": "1234567890",
            "systems_trace_audit_number": "111222",
        }
        gen = client.post("/api/v1/messages/generate", json={"mti": "0200", "fields": fields})
        assert gen.status_code == 200

        parsed = client.post("/api/v1/messages/parse", json={
            "encoded_message": gen.json()["encoded_message"],
        })
        assert parsed.status_code == 200
        body = parsed.json()
        assert body["mti"] == "0200"
        assert body["fields"]["primary_account_number"] == "1234567890123456"
        assert body["fields"]["processing_code"] == "123456"
        assert body["fields"]["amount_transaction"] == "000000001000"
        assert body["fields"]["transmission_date_and_time"] == "1234567890"
        assert body["fields"]["systems_trace_audit_number"] == "111222"

    @pytest.mark.parametrize("mti", ["0100", "0200", "0400", "0800"])
    def test_int_05_mti_preserved_through_roundtrip(self, mti: str) -> None:
        """generate → parse で MTI が正確に保持されること（各 MTI クラス）"""
        gen = client.post("/api/v1/messages/generate", json={
            "mti": mti,
            "fields": {"primary_account_number": "1234567890123456"},
        })
        assert gen.status_code == 200, f"MTI {mti} generate 失敗: {gen.json()}"

        parsed = client.post("/api/v1/messages/parse", json={
            "encoded_message": gen.json()["encoded_message"],
        })
        assert parsed.status_code == 200, f"MTI {mti} parse 失敗: {parsed.json()}"
        assert parsed.json()["mti"] == mti

    def test_int_06_mti_description_components_correct(self) -> None:
        """MTI 0200 の parse 結果に正しい日本語説明が含まれること"""
        gen = client.post("/api/v1/messages/generate", json={
            "mti": "0200",
            "fields": {"primary_account_number": "1234567890123456"},
        })
        assert gen.status_code == 200

        parsed = client.post("/api/v1/messages/parse", json={
            "encoded_message": gen.json()["encoded_message"],
        })
        assert parsed.status_code == 200
        desc = parsed.json()["mti_description"]
        assert desc["version"] == "ISO 8583-1:1987年版"
        assert desc["class"] == "ファイナンシャル"
        assert desc["function"] == "要求"
        assert desc["origin"] == "アクワイアラ"


# ==============================================================================
# シナリオ 3: 全フィールドを同時使用した最大メッセージ
# ==============================================================================

class TestAllFieldsMaxMessage:
    def test_int_07_generate_all_fields_returns_200(self) -> None:
        """全フィールドを同時使用したメッセージが正常に生成されること"""
        response = client.post("/api/v1/messages/generate", json={
            "mti": "0200",
            "fields": _ALL_FIELDS,
        })
        assert response.status_code == 200
        body = response.json()
        assert body["byte_length"] > 0

    def test_int_08_all_fields_preserved_through_roundtrip(self) -> None:
        """全フィールドが generate → parse で欠損なく往復すること"""
        gen = client.post("/api/v1/messages/generate", json={
            "mti": "0200",
            "fields": _ALL_FIELDS,
        })
        assert gen.status_code == 200

        parsed = client.post("/api/v1/messages/parse", json={
            "encoded_message": gen.json()["encoded_message"],
        })
        assert parsed.status_code == 200
        result_fields = parsed.json()["fields"]
        for field_name, expected_value in _ALL_FIELDS.items():
            assert result_fields.get(field_name) == expected_value, (
                f"フィールド '{field_name}' の値が不一致: "
                f"期待={expected_value}, 実際={result_fields.get(field_name)}"
            )

    def test_int_09_all_fields_message_larger_than_single_field(self) -> None:
        """全フィールド使用時のメッセージが単一フィールドより大きいこと"""
        single = client.post("/api/v1/messages/generate", json={
            "mti": "0200",
            "fields": {"primary_account_number": "1234567890123456"},
        })
        full = client.post("/api/v1/messages/generate", json={
            "mti": "0200",
            "fields": _ALL_FIELDS,
        })
        assert single.status_code == 200
        assert full.status_code == 200
        assert full.json()["byte_length"] > single.json()["byte_length"]


# ==============================================================================
# シナリオ 4: 不正 MTI が全レイヤーで正しく拒否されること
# ==============================================================================

class TestInvalidMtiRejectedAcrossLayers:
    def test_int_10_undefined_mti_class_returns_400_invalid_mti(self) -> None:
        """未定義 MTI クラス（0900）→ 全レイヤー通過後に 400 INVALID_MTI を返すこと"""
        response = client.post("/api/v1/messages/generate", json={
            "mti": "0900",  # class=9 は MtiClass に未定義
            "fields": {},
        })
        assert response.status_code == 400
        body = response.json()
        assert body["error_code"] == "INVALID_MTI"

    def test_int_11_undefined_mti_version_returns_400(self) -> None:
        """未定義バージョン（3200）→ 400 INVALID_MTI"""
        response = client.post("/api/v1/messages/generate", json={
            "mti": "3200",  # version=3 は MtiVersion に未定義
            "fields": {},
        })
        assert response.status_code == 400
        body = response.json()
        assert body["error_code"] == "INVALID_MTI"

    def test_int_12_undefined_mti_function_returns_400(self) -> None:
        """未定義機能（0150）→ 400 INVALID_MTI"""
        response = client.post("/api/v1/messages/generate", json={
            "mti": "0150",  # function=5 は MtiFunction に未定義
            "fields": {},
        })
        assert response.status_code == 400
        body = response.json()
        assert body["error_code"] == "INVALID_MTI"

    def test_int_13_undefined_mti_origin_returns_400(self) -> None:
        """未定義発生源（0106）→ 400 INVALID_MTI"""
        response = client.post("/api/v1/messages/generate", json={
            "mti": "0106",  # origin=6 は MtiOrigin に未定義
            "fields": {},
        })
        assert response.status_code == 400
        body = response.json()
        assert body["error_code"] == "INVALID_MTI"

    def test_int_14_format_invalid_mti_returns_422(self) -> None:
        """フォーマット不正 MTI（3桁）→ FastAPI バリデーション 422"""
        response = client.post("/api/v1/messages/generate", json={
            "mti": "020",  # 4桁でない
            "fields": {},
        })
        assert response.status_code == 422

    def test_int_15_corrupted_parse_message_returns_400(self) -> None:
        """破損メッセージの parse → 400 MESSAGE_DECODE_ERROR"""
        response = client.post("/api/v1/messages/parse", json={
            "encoded_message": "deadbeefdeadbeef",
        })
        assert response.status_code == 400
        body = response.json()
        assert body["error_code"] == "MESSAGE_DECODE_ERROR"
