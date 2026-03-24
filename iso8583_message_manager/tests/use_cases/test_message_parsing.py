"""
ParseMessageUseCase のユニットテスト。

TDD: Red Phase — テストを先に作成し、実装前に失敗することを確認する。
"""
import logging
from unittest.mock import Mock

import pytest

from iso8583_manager.core.exceptions import MessageDecodeError
from iso8583_manager.core.interfaces.iso_ports import IMessageGenerator
from iso8583_manager.core.models.generated.iso_models import Iso8583MessageModel
from iso8583_manager.core.models.mti import Mti
from iso8583_manager.use_cases.message_parsing import ParseMessageUseCase


# ==============================================================================
# フィクスチャ
# ==============================================================================

@pytest.fixture()
def mock_adapter() -> Mock:
    return Mock(spec=IMessageGenerator)


@pytest.fixture()
def use_case(mock_adapter: Mock) -> ParseMessageUseCase:
    return ParseMessageUseCase(message_generator=mock_adapter)


@pytest.fixture()
def sample_model() -> Iso8583MessageModel:
    return Iso8583MessageModel(
        primary_account_number="1234567890123456",
        amount_transaction="000000001000",
    )


# ==============================================================================
# 正常系
# ==============================================================================

class TestParseMessageUseCaseSuccess:
    def test_parse_returns_mti(
        self, use_case: ParseMessageUseCase, mock_adapter: Mock, sample_model: Iso8583MessageModel
    ) -> None:
        """成功時に Mti インスタンスを返す。"""
        mock_adapter.parse.return_value = ("0200", sample_model)

        mti, _ = use_case.execute(raw_message=b"DUMMY", model_cls=Iso8583MessageModel)

        assert isinstance(mti, Mti)
        assert mti.to_str() == "0200"

    def test_parse_returns_model(
        self, use_case: ParseMessageUseCase, mock_adapter: Mock, sample_model: Iso8583MessageModel
    ) -> None:
        """成功時に IIso8583Model の実装インスタンスを返す。"""
        mock_adapter.parse.return_value = ("0200", sample_model)

        _, model = use_case.execute(raw_message=b"DUMMY", model_cls=Iso8583MessageModel)

        assert isinstance(model, Iso8583MessageModel)
        assert model.primary_account_number == "1234567890123456"

    def test_parse_passes_raw_message_to_adapter(
        self, use_case: ParseMessageUseCase, mock_adapter: Mock, sample_model: Iso8583MessageModel
    ) -> None:
        """adapter.parse() に raw_message bytes が正しく渡される。"""
        raw = b"\x30\x32\x30\x30"
        mock_adapter.parse.return_value = ("0200", sample_model)

        use_case.execute(raw_message=raw, model_cls=Iso8583MessageModel)

        mock_adapter.parse.assert_called_once_with(raw, Iso8583MessageModel)

    def test_parse_passes_model_cls_to_adapter(
        self, use_case: ParseMessageUseCase, mock_adapter: Mock, sample_model: Iso8583MessageModel
    ) -> None:
        """adapter.parse() に model_cls が正しく渡される。"""
        mock_adapter.parse.return_value = ("0100", sample_model)

        use_case.execute(raw_message=b"DUMMY", model_cls=Iso8583MessageModel)

        _, kwargs = mock_adapter.parse.call_args
        # positional: (raw_message, model_cls)
        assert mock_adapter.parse.call_args[0][1] is Iso8583MessageModel


# ==============================================================================
# エラー伝搬
# ==============================================================================

class TestParseMessageUseCaseErrorPropagation:
    def test_parse_propagates_message_decode_error(
        self, use_case: ParseMessageUseCase, mock_adapter: Mock
    ) -> None:
        """MessageDecodeError はそのまま再 raise される。"""
        mock_adapter.parse.side_effect = MessageDecodeError("デコード失敗")

        with pytest.raises(MessageDecodeError):
            use_case.execute(raw_message=b"BAD", model_cls=Iso8583MessageModel)

    def test_parse_does_not_swallow_unexpected_error(
        self, use_case: ParseMessageUseCase, mock_adapter: Mock
    ) -> None:
        """予期しない例外（RuntimeError）も再 raise される。"""
        mock_adapter.parse.side_effect = RuntimeError("予期しないエラー")

        with pytest.raises(RuntimeError):
            use_case.execute(raw_message=b"BAD", model_cls=Iso8583MessageModel)


# ==============================================================================
# ロギング
# ==============================================================================

class TestParseMessageUseCaseLogging:
    def test_parse_logs_info_on_start(
        self, use_case: ParseMessageUseCase, mock_adapter: Mock,
        sample_model: Iso8583MessageModel, caplog: pytest.LogCaptureFixture
    ) -> None:
        """処理開始時に INFO ログが記録される。"""
        mock_adapter.parse.return_value = ("0200", sample_model)

        with caplog.at_level(logging.INFO):
            use_case.execute(raw_message=b"DUMMY", model_cls=Iso8583MessageModel)

        assert any("開始" in r.message for r in caplog.records)

    def test_parse_logs_info_on_complete(
        self, use_case: ParseMessageUseCase, mock_adapter: Mock,
        sample_model: Iso8583MessageModel, caplog: pytest.LogCaptureFixture
    ) -> None:
        """処理完了時に INFO ログが記録される。"""
        mock_adapter.parse.return_value = ("0200", sample_model)

        with caplog.at_level(logging.INFO):
            use_case.execute(raw_message=b"DUMMY", model_cls=Iso8583MessageModel)

        assert any("完了" in r.message for r in caplog.records)

    def test_parse_logs_error_on_failure(
        self, use_case: ParseMessageUseCase, mock_adapter: Mock,
        caplog: pytest.LogCaptureFixture
    ) -> None:
        """エラー時に ERROR ログが exc_info とともに記録される。"""
        mock_adapter.parse.side_effect = MessageDecodeError("失敗")

        with caplog.at_level(logging.ERROR):
            with pytest.raises(MessageDecodeError):
                use_case.execute(raw_message=b"BAD", model_cls=Iso8583MessageModel)

        error_records = [r for r in caplog.records if r.levelno == logging.ERROR]
        assert len(error_records) > 0
        assert error_records[0].exc_info is not None
