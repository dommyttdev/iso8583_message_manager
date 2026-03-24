"""
iso8583_core.infrastructure.pyiso8583_adapter.wrapper のユニットテスト。

PyIso8583Adapter の初期化・エラー処理を検証する。
"""
import json
import pytest
from pathlib import Path

from iso8583_core.infrastructure.pyiso8583_adapter.wrapper import PyIso8583Adapter
from iso8583_types.core.exceptions import SpecError


@pytest.fixture()
def spec_path(tmp_path: Path) -> str:
    """最小限の有効スペックファイルを一時ディレクトリに作成する。"""
    spec = {
        "2": {"max_length": 19, "length_type": "LLVAR", "data_encoding": "ascii",
              "description": "Primary Account Number", "type": "n"},
        "3": {"max_length": 6, "length_type": "fixed", "data_encoding": "ascii",
              "description": "Processing Code", "type": "n"},
    }
    p = tmp_path / "iso8583_fields.json"
    p.write_text(json.dumps(spec), encoding="utf-8")
    return str(p)


class TestPyIso8583AdapterInit:
    def test_init_with_valid_spec(self, spec_path: str):
        adapter = PyIso8583Adapter(spec_json_path=spec_path)
        assert adapter is not None

    def test_init_with_missing_spec_raises_spec_error(self, tmp_path: Path):
        with pytest.raises(SpecError):
            PyIso8583Adapter(spec_json_path=str(tmp_path / "nonexistent.json"))

    def test_init_with_invalid_json_raises_spec_error(self, tmp_path: Path):
        bad = tmp_path / "bad.json"
        bad.write_text("not valid json", encoding="utf-8")
        with pytest.raises(SpecError):
            PyIso8583Adapter(spec_json_path=str(bad))
