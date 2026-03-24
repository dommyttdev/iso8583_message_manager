"""
fields コマンドのユニットテスト。

TDD: Red Phase — テストを先に作成し、実装前に失敗することを確認する。
"""
from importlib.resources import files as _pkg_files

from typer.testing import CliRunner

from iso8583_manager.presentation.cli.app import app

runner = CliRunner()

_REAL_SPEC_PATH = str(_pkg_files("iso8583_core.data.schemas") / "iso8583_fields.json")


# ==============================================================================
# 正常系
# ==============================================================================

class TestFieldsCommandSuccess:
    def test_fields_exits_zero(self) -> None:
        result = runner.invoke(app, ["fields", "--spec", _REAL_SPEC_PATH])
        assert result.exit_code == 0

    def test_fields_shows_all_property_names(self) -> None:
        result = runner.invoke(app, ["fields", "--spec", _REAL_SPEC_PATH])
        assert "primary_account_number" in result.output
        assert "processing_code" in result.output
        assert "amount_transaction" in result.output
        assert "transmission_date_and_time" in result.output
        assert "systems_trace_audit_number" in result.output
        assert "response_code" in result.output

    def test_fields_shows_all_iso_field_ids(self) -> None:
        result = runner.invoke(app, ["fields", "--spec", _REAL_SPEC_PATH])
        for field_id in ["2", "3", "4", "7", "11", "39"]:
            assert field_id in result.output

    def test_fields_shows_max_lengths(self) -> None:
        result = runner.invoke(app, ["fields", "--spec", _REAL_SPEC_PATH])
        for max_len in ["19", "6", "12", "10", "2"]:
            assert max_len in result.output

    def test_fields_shows_data_types(self) -> None:
        result = runner.invoke(app, ["fields", "--spec", _REAL_SPEC_PATH])
        assert "n" in result.output
        assert "an" in result.output

    def test_fields_shows_descriptions(self) -> None:
        result = runner.invoke(app, ["fields", "--spec", _REAL_SPEC_PATH])
        assert "Primary Account Number" in result.output or "PAN" in result.output

    def test_fields_all_defined_fields_present(self) -> None:
        """出力に含まれるフィールドID数がspecの定義数と一致する。"""
        import json
        with open(_REAL_SPEC_PATH, encoding="utf-8") as f:
            spec = json.load(f)
        result = runner.invoke(app, ["fields", "--spec", _REAL_SPEC_PATH])
        for field_id in spec.keys():
            assert field_id in result.output


# ==============================================================================
# エラー系
# ==============================================================================

class TestFieldsCommandErrors:
    def test_fields_invalid_spec_path_exits_2(self) -> None:
        result = runner.invoke(app, ["fields", "--spec", "/nonexistent/spec.json"])
        assert result.exit_code == 2

    def test_fields_missing_spec_file_exits_2(self) -> None:
        result = runner.invoke(app, ["fields", "--spec", "/tmp/does_not_exist.json"])
        assert result.exit_code == 2

    def test_fields_invalid_json_content_exits_2(self) -> None:
        """spec ファイルが JSON として不正な場合は exit 2。"""
        import tempfile
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
            f.write("{ invalid json !!!")
            tmp_path = f.name
        result = runner.invoke(app, ["fields", "--spec", tmp_path])
        assert result.exit_code == 2

    def test_fields_error_message_in_output(self) -> None:
        result = runner.invoke(app, ["fields", "--spec", "/nonexistent/spec.json"])
        assert result.exit_code != 0
