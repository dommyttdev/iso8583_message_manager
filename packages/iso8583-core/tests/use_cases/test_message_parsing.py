"""
iso8583_core.use_cases.message_parsing のユニットテスト。
"""
import logging
import pytest
from unittest.mock import Mock

from iso8583_core.use_cases.message_parsing import ParseMessageUseCase
from iso8583_types.core.exceptions import MessageDecodeError
from iso8583_types.core.interfaces.iso_ports import IMessageGenerator
from iso8583_types.core.models.generated.iso_models import Iso8583MessageModel
from iso8583_types.core.models.mti import Mti


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


class TestParseMessageUseCaseSuccess:
    def test_parse_returns_mti(self, use_case, mock_adapter, sample_model):
        mock_adapter.parse.return_value = ("0200", sample_model)
        mti, _ = use_case.execute(raw_message=b"DUMMY", model_cls=Iso8583MessageModel)
        assert isinstance(mti, Mti)
        assert mti.to_str() == "0200"

    def test_parse_returns_model(self, use_case, mock_adapter, sample_model):
        mock_adapter.parse.return_value = ("0200", sample_model)
        _, model = use_case.execute(raw_message=b"DUMMY", model_cls=Iso8583MessageModel)
        assert model is sample_model

    def test_parse_calls_adapter_with_correct_args(self, use_case, mock_adapter, sample_model):
        mock_adapter.parse.return_value = ("0200", sample_model)
        use_case.execute(raw_message=b"DUMMY", model_cls=Iso8583MessageModel)
        mock_adapter.parse.assert_called_once_with(b"DUMMY", Iso8583MessageModel)


class TestParseMessageUseCaseError:
    def test_parse_raises_decode_error(self, use_case, mock_adapter):
        mock_adapter.parse.side_effect = MessageDecodeError("decode failed")
        with pytest.raises(MessageDecodeError):
            use_case.execute(raw_message=b"BAD", model_cls=Iso8583MessageModel)

    def test_parse_logs_error(self, use_case, mock_adapter, caplog):
        caplog.set_level(logging.INFO)
        mock_adapter.parse.side_effect = MessageDecodeError("fail")
        with pytest.raises(MessageDecodeError):
            use_case.execute(raw_message=b"BAD", model_cls=Iso8583MessageModel)
        assert "エラー" in caplog.text
