"""
iso8583_types.exceptions のユニットテスト。

例外クラスの継承関係と isinstance チェックを検証する。
"""
import pytest
from iso8583_types.exceptions import (
    Iso8583Error,
    InvalidMtiError,
    MessageDecodeError,
    MessageEncodeError,
    SpecError,
)


class TestExceptionHierarchy:
    def test_iso8583_error_is_exception(self):
        assert issubclass(Iso8583Error, Exception)

    def test_spec_error_is_iso8583_error(self):
        assert issubclass(SpecError, Iso8583Error)

    def test_message_encode_error_is_iso8583_error(self):
        assert issubclass(MessageEncodeError, Iso8583Error)

    def test_message_decode_error_is_iso8583_error(self):
        assert issubclass(MessageDecodeError, Iso8583Error)

    def test_invalid_mti_error_is_iso8583_error(self):
        assert issubclass(InvalidMtiError, Iso8583Error)

    def test_invalid_mti_error_is_value_error(self):
        """後方互換性のため ValueError も継承する。"""
        assert issubclass(InvalidMtiError, ValueError)


class TestExceptionRaisable:
    def test_iso8583_error_can_be_raised(self):
        with pytest.raises(Iso8583Error):
            raise Iso8583Error("基底エラー")

    def test_spec_error_caught_as_iso8583_error(self):
        with pytest.raises(Iso8583Error):
            raise SpecError("スペックエラー")

    def test_invalid_mti_error_caught_as_value_error(self):
        with pytest.raises(ValueError):
            raise InvalidMtiError("不正MTI")
