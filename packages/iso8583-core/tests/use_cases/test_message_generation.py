import pytest
from unittest.mock import Mock
from iso8583_core.use_cases.message_generation import GenerateMessageUseCase
from iso8583_types.core.interfaces.iso_ports import IMessageGenerator
from iso8583_types.core.models.generated.iso_models import Iso8583MessageModel
from iso8583_types.core.models.mti import Mti

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
    
    mti = Mti.from_str("0100")
    
    # 実行
    result = use_case.execute(mti=mti, model_data=model)
    
    # 検証
    assert result == bytearray(b"MOCK_ISO_8583_BINARY")
    mock_adapter.generate.assert_called_once_with(mti, model)

def test_generate_message_with_raw_string_type_error():
    """生文字列（str）を渡した場合、型アノテーション違反の検知確認。"""
    mock_adapter = Mock(spec=IMessageGenerator)
    mock_adapter.generate.side_effect = AttributeError("'str' object has no attribute 'to_str'")
    
    use_case = GenerateMessageUseCase(message_generator=mock_adapter)
    model = Iso8583MessageModel()
    
    with pytest.raises(AttributeError):
        use_case.execute(mti="0100", model_data=model)  # type: ignore[arg-type]

def test_generate_message_logging_and_error_handling(caplog):
    import logging
    from iso8583_types.core.exceptions import MessageEncodeError
    
    caplog.set_level(logging.INFO)
    mock_adapter = Mock(spec=IMessageGenerator)
    mock_adapter.generate.side_effect = MessageEncodeError("Adapter failed")
    
    use_case = GenerateMessageUseCase(message_generator=mock_adapter)
    model = Iso8583MessageModel()
    mti = Mti.from_str("0200")
    
    with pytest.raises(MessageEncodeError):
        use_case.execute(mti=mti, model_data=model)
    
    assert "ISO 8583 メッセージ生成を開始します" in caplog.text
    assert "メッセージ生成中にエラーが発生しました" in caplog.text

def test_generate_message_success_logging(caplog):
    import logging
    caplog.set_level(logging.INFO)
    mock_adapter = Mock(spec=IMessageGenerator)
    mock_adapter.generate.return_value = b"success"
    
    use_case = GenerateMessageUseCase(message_generator=mock_adapter)
    model = Iso8583MessageModel()
    mti = Mti.from_str("0200")
    
    use_case.execute(mti=mti, model_data=model)
    
    assert "ISO 8583 メッセージ生成を開始します" in caplog.text
    assert "ISO 8583 メッセージ生成が正常に完了しました" in caplog.text
