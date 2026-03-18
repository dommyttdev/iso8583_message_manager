import pytest
import os
from pathlib import Path
from iso8583_manager.infrastructure.pyiso8583_adapter.wrapper import PyIso8583Adapter
from iso8583_manager.core.models.generated.iso_models import Iso8583MessageModel

def test_generate_and_parse():
    # Setup
    schemas_dir = Path(__file__).parent.parent.parent / "data" / "schemas"
    json_path = schemas_dir / "iso8583_fields.json"
    
    adapter = PyIso8583Adapter(spec_json_path=str(json_path))
    
    # 正常系モデル
    model = Iso8583MessageModel(
        primary_account_number="1234567890123456",
        processing_code="000000",
        amount_transaction="000000100000",
        transmission_date_and_time="1010101010",
        systems_trace_audit_number="123456",
        response_code="00"
    )
    
    # Generate
    raw_message = adapter.generate(mti="0200", model_data=model)
    
    assert isinstance(raw_message, bytearray)
    assert len(raw_message) > 0
    
    # Parse back
    parsed_model = adapter.parse(raw_message, model_cls=Iso8583MessageModel)
    
    assert isinstance(parsed_model, Iso8583MessageModel)
    assert parsed_model.primary_account_number == "1234567890123456"
    assert parsed_model.processing_code == "000000"
    assert parsed_model.response_code == "00"
