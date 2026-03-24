from importlib.resources import files as _pkg_files
from iso8583_core.use_cases.message_generation import GenerateMessageUseCase
from iso8583_core.infrastructure.pyiso8583_adapter.wrapper import PyIso8583Adapter
from iso8583_types.models.generated.iso_models import Iso8583MessageModel
from iso8583_types.models.mti import Mti

def test_integration_generate_and_parse_success():
    """
    ユースケース層とインフラストラクチャー層（pyiso8583）を結合した End-to-End のテスト。
    モデルの生成からバイナリ化、そして再度パースできるかまでを一貫して検証する。
    """
    # 1. 依存関係の組み立て (DI: Dependency Injection)
    json_path = _pkg_files("iso8583_core.data.schemas") / "iso8583_fields.json"
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
    mti_str, parsed_model = adapter.parse(raw_message=raw_bytes, model_cls=Iso8583MessageModel)

    # アサーション：MTIが正しく復元されていること
    assert mti_str == "0200"

    # アサーション：入力した値とパース後の値が完全一致するか
    assert parsed_model.primary_account_number == "1234567890123456"
    assert parsed_model.processing_code == "123456"
    assert parsed_model.amount_transaction == "000000001000"
    assert parsed_model.transmission_date_and_time == "1234567890"
    assert parsed_model.response_code == "00"


def test_integration_all_fields_max_message():
    """
    全フィールドを同時使用した最大メッセージの生成・解析統合テスト。

    ISO 8583 モデルが定義する全フィールドを同時に設定してエンコードし、
    デコード後に全フィールドが欠損なく復元されることを検証する。
    """
    json_path = _pkg_files("iso8583_core.data.schemas") / "iso8583_fields.json"
    adapter = PyIso8583Adapter(spec_json_path=str(json_path))
    use_case = GenerateMessageUseCase(message_generator=adapter)

    # 全フィールドを設定（モデルが定義するすべてのフィールドを使用）
    all_fields = {
        "primary_account_number": "1234567890123456",
        "processing_code": "123456",
        "amount_transaction": "000000001000",
        "transmission_date_and_time": "1234567890",
        "systems_trace_audit_number": "111222",
        "response_code": "00",
    }
    model = Iso8583MessageModel(**all_fields)

    mti = Mti.from_str("0200")
    raw_bytes = use_case.execute(mti=mti, model_data=model)

    assert isinstance(raw_bytes, bytearray)

    # 全フィールドを含むため、単一フィールド時より大きいこと
    single_model = Iso8583MessageModel(primary_account_number="1234567890123456")
    single_bytes = use_case.execute(mti=mti, model_data=single_model)
    assert len(raw_bytes) > len(single_bytes)

    # 全フィールドが欠損なくデコードされること
    mti_str, parsed = adapter.parse(raw_message=raw_bytes, model_cls=Iso8583MessageModel)
    assert mti_str == "0200"
    assert parsed.primary_account_number == all_fields["primary_account_number"]
    assert parsed.processing_code == all_fields["processing_code"]
    assert parsed.amount_transaction == all_fields["amount_transaction"]
    assert parsed.transmission_date_and_time == all_fields["transmission_date_and_time"]
    assert parsed.systems_trace_audit_number == all_fields["systems_trace_audit_number"]
    assert parsed.response_code == all_fields["response_code"]


def test_integration_invalid_mti_rejected_at_core_layer():
    """
    不正 MTI がコア層（Mti.from_str）で正しく拒否されることを検証する。

    各 MTI コンポーネント（version/class/function/origin）の未定義値を
    それぞれ単独でテストし、InvalidMtiError が送出されることを確認する。
    """
    from iso8583_types.exceptions import InvalidMtiError

    invalid_cases = [
        ("3200", "未定義バージョン"),
        ("0900", "未定義クラス"),
        ("0150", "未定義機能"),
        ("0106", "未定義発生源"),
    ]
    for mti_str, label in invalid_cases:
        try:
            Mti.from_str(mti_str)
            raise AssertionError(f"{label}: InvalidMtiError が発生しなかった ({mti_str})")
        except InvalidMtiError:
            pass  # 期待通り
