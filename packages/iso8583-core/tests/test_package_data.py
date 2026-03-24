"""
パッケージデータアクセスのテスト。

iso8583_fields.json が importlib.resources 経由でアクセスできることを検証する。
パッケージインストール後も正しくスペックファイルを参照できることを保証する。
"""
import json
from importlib.resources import files


class TestPackageData:
    def test_pd_01_spec_file_accessible_via_importlib_resources(self) -> None:
        """iso8583_fields.json が importlib.resources でアクセス可能であること"""
        spec = files("iso8583_core.data.schemas") / "iso8583_fields.json"
        assert spec.is_file(), "iso8583_fields.json がパッケージデータとして存在しない"

    def test_pd_02_spec_file_is_valid_json(self) -> None:
        """iso8583_fields.json が有効な JSON であること"""
        spec = files("iso8583_core.data.schemas") / "iso8583_fields.json"
        content = spec.read_text(encoding="utf-8")
        data = json.loads(content)
        assert isinstance(data, dict), "トップレベルは dict（フィールド番号→定義）であること"
        assert len(data) > 0, "フィールド定義が1件以上あること"

    def test_pd_03_spec_file_has_required_keys(self) -> None:
        """各フィールド定義に必須キーが含まれること"""
        spec = files("iso8583_core.data.schemas") / "iso8583_fields.json"
        content = spec.read_text(encoding="utf-8")
        fields: dict = json.loads(content)
        required_keys = {"name"}
        for field_num, field_def in fields.items():
            missing = required_keys - field_def.keys()
            assert not missing, f"フィールド {field_num} の定義にキーが不足: {missing}"

    def test_pd_04_spec_path_resolves_to_existing_file(self) -> None:
        """importlib.resources で解決したスペックパスがファイルシステム上に存在すること"""
        from pathlib import Path

        spec = files("iso8583_core.data.schemas") / "iso8583_fields.json"
        path = Path(str(spec))
        assert path.exists(), f"デフォルトスペックパスが存在しない: {path}"
        assert path.name == "iso8583_fields.json"

    def test_pd_05_use_case_builds_with_default_spec(self) -> None:
        """デフォルトスペックパスでユースケースが正常に生成されること"""
        from pathlib import Path
        from iso8583_core.infrastructure.pyiso8583_adapter.wrapper import PyIso8583Adapter
        from iso8583_core.use_cases.message_generation import GenerateMessageUseCase

        spec_path = Path(str(files("iso8583_core.data.schemas") / "iso8583_fields.json"))
        adapter = PyIso8583Adapter(spec_json_path=str(spec_path))
        use_case = GenerateMessageUseCase(message_generator=adapter)
        assert use_case is not None
