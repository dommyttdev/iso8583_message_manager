"""
error_handler.py のユニットテスト。

各 async ハンドラーが正しい HTTP ステータスコードとエラーコードを返すことを検証する。
"""
import asyncio
import json

import pytest
from unittest.mock import MagicMock

from iso8583_types.exceptions import (
    Iso8583Error,
    InvalidMtiError,
    MessageDecodeError,
    MessageEncodeError,
    SpecError,
)
from iso8583_api.error_handler import (
    invalid_mti_handler,
    iso8583_error_handler,
    message_decode_error_handler,
    message_encode_error_handler,
    spec_error_handler,
    value_error_handler,
)


def _run(coro):  # type: ignore[no-untyped-def]
    """asyncio.run のヘルパー。"""
    return asyncio.run(coro)


@pytest.fixture
def mock_request() -> MagicMock:
    return MagicMock()


class TestInvalidMtiHandler:
    def test_eh_01_returns_400_invalid_mti(self, mock_request: MagicMock) -> None:
        """InvalidMtiError → 400 INVALID_MTI"""
        exc = InvalidMtiError("不正な MTI: 9999")
        response = _run(invalid_mti_handler(mock_request, exc))
        assert response.status_code == 400
        body = json.loads(response.body)
        assert body["error_code"] == "INVALID_MTI"
        assert "不正な MTI: 9999" in body["detail"]


class TestMessageEncodeErrorHandler:
    def test_eh_02_returns_400_encode_error(self, mock_request: MagicMock) -> None:
        """MessageEncodeError → 400 MESSAGE_ENCODE_ERROR"""
        exc = MessageEncodeError("エンコード失敗")
        response = _run(message_encode_error_handler(mock_request, exc))
        assert response.status_code == 400
        body = json.loads(response.body)
        assert body["error_code"] == "MESSAGE_ENCODE_ERROR"
        assert "エンコード失敗" in body["detail"]


class TestMessageDecodeErrorHandler:
    def test_eh_03_returns_400_decode_error(self, mock_request: MagicMock) -> None:
        """MessageDecodeError → 400 MESSAGE_DECODE_ERROR"""
        exc = MessageDecodeError("デコード失敗")
        response = _run(message_decode_error_handler(mock_request, exc))
        assert response.status_code == 400
        body = json.loads(response.body)
        assert body["error_code"] == "MESSAGE_DECODE_ERROR"
        assert "デコード失敗" in body["detail"]


class TestSpecErrorHandler:
    def test_eh_04_returns_500_spec_error(self, mock_request: MagicMock) -> None:
        """SpecError → 500 SPEC_ERROR"""
        exc = SpecError("スペックファイルが不正")
        response = _run(spec_error_handler(mock_request, exc))
        assert response.status_code == 500
        body = json.loads(response.body)
        assert body["error_code"] == "SPEC_ERROR"
        assert "スペックファイルが不正" in body["detail"]

    def test_eh_05_spec_error_message_is_localized(self, mock_request: MagicMock) -> None:
        """SpecError レスポンスが日本語メッセージを含むこと"""
        exc = SpecError("test")
        response = _run(spec_error_handler(mock_request, exc))
        body = json.loads(response.body)
        assert "スペックファイルの処理中" in body["message"]


class TestIso8583ErrorHandler:
    def test_eh_06_returns_500_internal_error(self, mock_request: MagicMock) -> None:
        """Iso8583Error（基底） → 500 INTERNAL_ERROR"""
        exc = Iso8583Error("内部エラー発生")
        response = _run(iso8583_error_handler(mock_request, exc))
        assert response.status_code == 500
        body = json.loads(response.body)
        assert body["error_code"] == "INTERNAL_ERROR"
        assert "内部エラー発生" in body["detail"]

    def test_eh_07_internal_error_message_is_localized(self, mock_request: MagicMock) -> None:
        """INTERNAL_ERROR レスポンスが日本語メッセージを含むこと"""
        exc = Iso8583Error("test")
        response = _run(iso8583_error_handler(mock_request, exc))
        body = json.loads(response.body)
        assert "内部エラー" in body["message"]


class TestValueErrorHandler:
    def test_eh_08_returns_400_invalid_format(self, mock_request: MagicMock) -> None:
        """ValueError → 400 INVALID_FORMAT"""
        exc = ValueError("フォーマット不正")
        response = _run(value_error_handler(mock_request, exc))
        assert response.status_code == 400
        body = json.loads(response.body)
        assert body["error_code"] == "INVALID_FORMAT"
        assert "フォーマット不正" in body["detail"]

    def test_eh_09_invalid_format_message_is_localized(self, mock_request: MagicMock) -> None:
        """INVALID_FORMAT レスポンスが日本語メッセージを含むこと"""
        exc = ValueError("test")
        response = _run(value_error_handler(mock_request, exc))
        body = json.loads(response.body)
        assert "フォーマット" in body["message"]
