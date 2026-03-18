import pytest
from unittest.mock import Mock
from iso8583_manager.use_cases.message_generation import GenerateMessageUseCase
from iso8583_manager.core.interfaces.iso_ports import IMessageGenerator
from iso8583_manager.core.models.generated.iso_models import Iso8583MessageModel
from iso8583_manager.core.models.mti import Mti

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
    """生文字列（str）を渡した場合、型アノテーション違反の検知確認。
    
    Python は動的型付けのため実行時に TypeError は発生しないが、
    型チェッカー（mypy等）では違反として検出される。
    本テストではアダプター層でエラーになる動作（to_str() 未定義）を確認する。
    """
    mock_adapter = Mock(spec=IMessageGenerator)
    # str が Mti として渡された場合、to_str() が str にはないためアダプター内でエラーになる
    mock_adapter.generate.side_effect = AttributeError("'str' object has no attribute 'to_str'")
    
    use_case = GenerateMessageUseCase(message_generator=mock_adapter)
    model = Iso8583MessageModel()
    
    with pytest.raises(AttributeError):
        # 型アノテーション上 mti: Mti だが、str を渡した場合のランタイム挙動を検証
        use_case.execute(mti="0100", model_data=model)  # type: ignore[arg-type]
