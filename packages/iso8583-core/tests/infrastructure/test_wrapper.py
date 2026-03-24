from importlib.resources import files as _pkg_files
from iso8583_core.infrastructure.pyiso8583_adapter.wrapper import PyIso8583Adapter
from iso8583_types.models.generated.iso_models import Iso8583MessageModel
from iso8583_types.models.mti import Mti

def test_generate_and_parse():
    # Setup
    json_path = _pkg_files("iso8583_core.data.schemas") / "iso8583_fields.json"
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
    
    mti = Mti.from_str("0200")
    
    # Generate
    raw_message = adapter.generate(mti=mti, model_data=model)
    
    assert isinstance(raw_message, bytearray)
    assert len(raw_message) > 0
    
    # Parse back
    mti_str, parsed_model = adapter.parse(raw_message, model_cls=Iso8583MessageModel)

    assert mti_str == "0200"
    assert isinstance(parsed_model, Iso8583MessageModel)
    assert parsed_model.primary_account_number == "1234567890123456"
    assert parsed_model.processing_code == "000000"
    assert parsed_model.response_code == "00"
