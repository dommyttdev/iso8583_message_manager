import pytest
from unittest.mock import Mock
from iso8583_manager.use_cases.message_generation import GenerateMessageUseCase
from iso8583_manager.core.interfaces.iso_ports import IMessageGenerator
from iso8583_manager.core.models.generated.iso_models import Iso8583MessageModel

def test_generate_message_usecase():
    # インフラの実装の代わりにMockを注入 (DIPを利用)
    mock_adapter = Mock(spec=IMessageGenerator)
    mock_adapter.generate.return_value = bytearray(b"MOCK_ISO_8583_BINARY")

    # Use Case に DI（依存性の注入）を行う
    use_case = GenerateMessageUseCase(message_generator=mock_adapter)

    # 正常系モデル
    model = Iso8583MessageModel(
        primary_account_number="9876543210987654"
    )
    
    # 実行
    result = use_case.execute(mti="0100", model_data=model)
    
    # 検証
    assert result == bytearray(b"MOCK_ISO_8583_BINARY")
    mock_adapter.generate.assert_called_once_with("0100", model)

def test_generate_message_invalid_mti():
    mock_adapter = Mock(spec=IMessageGenerator)
    use_case = GenerateMessageUseCase(message_generator=mock_adapter)
    
    model = Iso8583MessageModel()
    
    # 異常系：MTIが4桁未満
    with pytest.raises(ValueError, match="MTI must be exactly 4 characters."):
        use_case.execute(mti="200", model_data=model)
