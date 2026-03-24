import pytest
from unittest.mock import patch, mock_open, MagicMock
import logging
from iso8583_core.infrastructure.pyiso8583_adapter.wrapper import PyIso8583Adapter
from iso8583_types.exceptions import SpecError, MessageEncodeError, MessageDecodeError
from iso8583_types.models.mti import Mti, MtiVersion, MtiClass, MtiFunction, MtiOrigin

def test_init_raises_spec_error_if_file_not_found():
    with patch("builtins.open", side_effect=FileNotFoundError):
        with pytest.raises(SpecError) as excinfo:
            PyIso8583Adapter("non_existent.json")
        assert "スペックファイルが見つかりません" in str(excinfo.value)

def test_init_raises_spec_error_if_json_invalid():
    with patch("builtins.open", mock_open(read_data="invalid json")):
        with pytest.raises(SpecError) as excinfo:
            PyIso8583Adapter("invalid.json")
        assert "スペックファイルの形式が正しくありません" in str(excinfo.value)

def test_generate_raises_message_encode_error_on_pyiso8583_failure():
    # インスタンス化の際の spec 読み込みも Mock する
    with patch("builtins.open", mock_open(read_data='{"2": {}}')):
        adapter = PyIso8583Adapter("dummy.json")
    
    mti = Mti(MtiVersion.V1987, MtiClass.FINANCIAL, MtiFunction.REQUEST, MtiOrigin.ACQUIRER)
    model_mock = MagicMock()
    model_mock.to_iso_dict.return_value = {"2": "123456"}

    with patch("iso8583_core.infrastructure.pyiso8583_adapter.wrapper.iso8583.encode", side_effect=Exception("Encoding failed")):
        with pytest.raises(MessageEncodeError) as excinfo:
            adapter.generate(mti, model_mock)
        assert "エンコードに失敗しました" in str(excinfo.value)

def test_parse_raises_message_decode_error_on_pyiso8583_failure():
    with patch("builtins.open", mock_open(read_data='{"2": {}}')):
        adapter = PyIso8583Adapter("dummy.json")
    
    from unittest.mock import MagicMock
    with patch("iso8583_core.infrastructure.pyiso8583_adapter.wrapper.iso8583.decode", side_effect=Exception("Decoding failed")):
        with pytest.raises(MessageDecodeError) as excinfo:
            adapter.parse(b"dummy", MagicMock())
        assert "デコードに失敗しました" in str(excinfo.value)

def test_logging_output(caplog):
    caplog.set_level(logging.INFO)
    # len_type=2 → LLVAR (可変長), max_len=6 → 6バイトの値が有効
    with patch("builtins.open", mock_open(read_data='{"2": {"len_type": 2, "max_len": 6}}')):
        adapter = PyIso8583Adapter("dummy.json")

    assert "PyIso8583Adapter initialized with spec" in caplog.text

    mti = Mti(MtiVersion.V1987, MtiClass.FINANCIAL, MtiFunction.REQUEST, MtiOrigin.ACQUIRER)
    model_mock = MagicMock()
    model_mock.to_iso_dict.return_value = {"2": "123456"}

    adapter.generate(mti, model_mock)
    assert "Generating ISO 8583 message for MTI: 0200" in caplog.text
    assert "Successfully encoded ISO 8583 message" in caplog.text
