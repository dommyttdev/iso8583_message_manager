import pytest
from pathlib import Path
from iso8583_manager.use_cases.message_generation import GenerateMessageUseCase
from iso8583_manager.infrastructure.pyiso8583_adapter.wrapper import PyIso8583Adapter
from iso8583_manager.core.models.generated.iso_models import Iso8583MessageModel
from iso8583_manager.core.models.mti import Mti

def test_integration_generate_and_parse_success():
    """
    ユースケース層とインフラストラクチャー層（pyiso8583）を結合した End-to-End のテスト。
    モデルの生成からバイナリ化、そして再度パースできるかまでを一貫して検証する。
    """
    # 1. 依存関係の組み立て (DI: Dependency Injection)
    schemas_dir = Path(__file__).parent.parent.parent / "data" / "schemas"
    json_path = schemas_dir / "iso8583_fields.json"
    
    adapter = PyIso8583Adapter(spec_json_path=str(json_path))
    use_case = GenerateMessageUseCase(message_generator=adapter)
    
    # 2. 自動生成されたPydanticモデルに入力データをセット
    model = Iso8583MessageModel(
        primary_account_number="1234567890123456",
        processing_code="123456",
        amount_transaction="000000001000",
        transmission_date_and_time="1234567890",
        systems_trace_audit_number="111222",
        response_code="00"
    )
    
    # 3. ユースケースの実行（ISO 8583 メッセージバイナリの生成）
    mti = Mti.from_str("0200")
    raw_bytes = use_case.execute(mti=mti, model_data=model)
    
    # 検証：bytearrayとして出力されていること
    assert isinstance(raw_bytes, bytearray)
    assert len(raw_bytes) > 0
    
    # 4. バイト列から再パースしてオブジェクトが復元できるか結合テスト
    parsed_model = adapter.parse(raw_message=raw_bytes, model_cls=Iso8583MessageModel)
    
    # アサーション：入力した値とパース後の値が完全一致するか
    assert parsed_model.primary_account_number == "1234567890123456"
    assert parsed_model.processing_code == "123456"
    assert parsed_model.amount_transaction == "000000001000"
    assert parsed_model.transmission_date_and_time == "1234567890"
    assert parsed_model.response_code == "00"
