"""
iso8583_core.use_cases.message_generation のユニットテスト。
"""
import logging
import pytest
from unittest.mock import Mock

from iso8583_core.use_cases.message_generation import GenerateMessageUseCase
from iso8583_types.core.exceptions import MessageEncodeError
from iso8583_types.core.interfaces.iso_ports import IMessageGenerator
from iso8583_types.core.models.generated.iso_models import Iso8583MessageModel
from iso8583_types.core.models.mti import Mti


class TestGenerateMessageUseCase:
    def test_execute_returns_encoded_bytes(self):
        mock_adapter = Mock(spec=IMessageGenerator)
        mock_adapter.generate.return_value = bytearray(b"MOCK_ISO_8583_BINARY")

        use_case = GenerateMessageUseCase(message_generator=mock_adapter)
        model = Iso8583MessageModel(primary_account_number="9876543210987654")
        mti = Mti.from_str("0100")

        result = use_case.execute(mti=mti, model_data=model)

        assert result == bytearray(b"MOCK_ISO_8583_BINARY")
        mock_adapter.generate.assert_called_once_with(mti, model)

    def test_execute_raises_on_adapter_error(self):
        mock_adapter = Mock(spec=IMessageGenerator)
        mock_adapter.generate.side_effect = MessageEncodeError("Adapter failed")

        use_case = GenerateMessageUseCase(message_generator=mock_adapter)

        with pytest.raises(MessageEncodeError):
            use_case.execute(mti=Mti.from_str("0200"), model_data=Iso8583MessageModel())

    def test_execute_logs_start_and_success(self, caplog):
        caplog.set_level(logging.INFO)
        mock_adapter = Mock(spec=IMessageGenerator)
        mock_adapter.generate.return_value = bytearray(b"ok")

        use_case = GenerateMessageUseCase(message_generator=mock_adapter)
        use_case.execute(mti=Mti.from_str("0200"), model_data=Iso8583MessageModel())

        assert "ISO 8583 メッセージ生成を開始します" in caplog.text
        assert "ISO 8583 メッセージ生成が正常に完了しました" in caplog.text

    def test_execute_logs_error_on_failure(self, caplog):
        caplog.set_level(logging.INFO)
        mock_adapter = Mock(spec=IMessageGenerator)
        mock_adapter.generate.side_effect = MessageEncodeError("fail")

        use_case = GenerateMessageUseCase(message_generator=mock_adapter)

        with pytest.raises(MessageEncodeError):
            use_case.execute(mti=Mti.from_str("0200"), model_data=Iso8583MessageModel())

        assert "メッセージ生成中にエラーが発生しました" in caplog.text
