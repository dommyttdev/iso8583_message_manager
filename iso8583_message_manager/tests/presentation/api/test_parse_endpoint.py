"""
POST /api/v1/messages/parse のルーターユニットテスト。

テスト戦略 doc/api/api_design.md §9.3 API-PAR-01〜07 に対応。
ユースケース層はモックで差し替え、Presentation 層の責務のみを検証する。
"""
import base64
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from iso8583_types.core.exceptions import MessageDecodeError
from iso8583_types.core.models.generated.iso_models import Iso8583MessageModel
from iso8583_types.core.models.mti import Mti
from iso8583_api.app import app
from iso8583_api.routers.messages import get_parse_use_case


def _make_mock_parse_result(
    mti_str: str = "0200",
    pan: str = "4111111111111111",
) -> tuple[Mti, Iso8583MessageModel]:
    """テスト用のモック戻り値を生成する。"""
    mti = Mti.from_str(mti_str)
    model = Iso8583MessageModel(primary_account_number=pan)
    return mti, model


@pytest.fixture
def mock_use_case() -> MagicMock:
    mock = MagicMock()
    mock.execute.return_value = _make_mock_parse_result()
    app.dependency_overrides[get_parse_use_case] = lambda: mock
    yield mock
    app.dependency_overrides.clear()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


# 正常系テスト用の有効な hex メッセージ（"0200" MTI + ビットマップ 16桁 PAN）
_VALID_HEX = "02004000000000000010313131313131313131313131313131"


class TestParseEndpointSuccess:
    def test_api_par_01_hex_input(
        self, client: TestClient, mock_use_case: MagicMock
    ) -> None:
        """API-PAR-01: 正常 hex 入力 → 200, mti・fields・mti_description を含む。"""
        response = client.post(
            "/api/v1/messages/parse",
            json={"encoded_message": _VALID_HEX, "input_format": "hex"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "mti" in data
        assert "fields" in data
        assert "mti_description" in data

    def test_api_par_02_base64_input(
        self, client: TestClient, mock_use_case: MagicMock
    ) -> None:
        """API-PAR-02: 正常 base64 入力 → 200。"""
        raw = bytes.fromhex(_VALID_HEX)
        b64 = base64.b64encode(raw).decode("ascii")
        response = client.post(
            "/api/v1/messages/parse",
            json={"encoded_message": b64, "input_format": "base64"},
        )
        assert response.status_code == 200

    def test_api_par_03_mti_description_has_4_keys(
        self, client: TestClient, mock_use_case: MagicMock
    ) -> None:
        """API-PAR-03: mti_description の全 4 キー（version/class/function/origin）存在。"""
        response = client.post(
            "/api/v1/messages/parse",
            json={"encoded_message": _VALID_HEX, "input_format": "hex"},
        )
        assert response.status_code == 200
        mti_desc = response.json()["mti_description"]
        assert "version" in mti_desc
        assert "class" in mti_desc
        assert "function" in mti_desc
        assert "origin" in mti_desc


class TestParseEndpointErrors:
    def test_api_par_04_invalid_hex_characters(
        self, client: TestClient, mock_use_case: MagicMock
    ) -> None:
        """API-PAR-04: 不正な hex 文字列（非 16 進数文字含む） → 400, INVALID_FORMAT。"""
        response = client.post(
            "/api/v1/messages/parse",
            json={"encoded_message": "ZZZZ", "input_format": "hex"},
        )
        assert response.status_code == 400
        assert response.json()["error_code"] == "INVALID_FORMAT"

    def test_api_par_05_odd_length_hex(
        self, client: TestClient, mock_use_case: MagicMock
    ) -> None:
        """API-PAR-05: 奇数長の hex 文字列 → 400, INVALID_FORMAT。"""
        response = client.post(
            "/api/v1/messages/parse",
            json={"encoded_message": "020", "input_format": "hex"},
        )
        assert response.status_code == 400
        assert response.json()["error_code"] == "INVALID_FORMAT"

    def test_api_par_06_decode_failure(
        self, client: TestClient, mock_use_case: MagicMock
    ) -> None:
        """API-PAR-06: デコード失敗（破損データ） → 400, MESSAGE_DECODE_ERROR。"""
        mock_use_case.execute.side_effect = MessageDecodeError("デコード失敗")
        # 有効な hex だが pyiso8583 としては不正なバイト列
        response = client.post(
            "/api/v1/messages/parse",
            json={"encoded_message": "deadbeef", "input_format": "hex"},
        )
        assert response.status_code == 400
        assert response.json()["error_code"] == "MESSAGE_DECODE_ERROR"

    def test_api_par_07_encoded_message_missing(
        self, client: TestClient, mock_use_case: MagicMock
    ) -> None:
        """API-PAR-07: encoded_message キー欠落 → 422。"""
        response = client.post(
            "/api/v1/messages/parse",
            json={"input_format": "hex"},
        )
        assert response.status_code == 422
