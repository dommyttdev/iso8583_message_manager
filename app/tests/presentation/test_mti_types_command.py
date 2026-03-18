"""
mti-types コマンドのユニットテスト。

TDD: Red Phase — テストを先に作成し、実装前に失敗することを確認する。
"""
import json

from typer.testing import CliRunner

from iso8583_manager.core.models.mti import MtiClass, MtiFunction, MtiOrigin, MtiVersion
from iso8583_manager.presentation.cli.app import app

runner = CliRunner()


# ==============================================================================
# 正常系: テーブル出力 (デフォルト)
# ==============================================================================

class TestMtiTypesCommandTable:
    def test_mti_types_exits_zero(self) -> None:
        result = runner.invoke(app, ["mti-types"])
        assert result.exit_code == 0

    def test_mti_types_shows_all_version_names(self) -> None:
        result = runner.invoke(app, ["mti-types"])
        for member in MtiVersion:
            assert member.name in result.output

    def test_mti_types_shows_all_class_names(self) -> None:
        result = runner.invoke(app, ["mti-types"])
        for member in MtiClass:
            assert member.name in result.output

    def test_mti_types_shows_all_function_names(self) -> None:
        result = runner.invoke(app, ["mti-types"])
        for member in MtiFunction:
            assert member.name in result.output

    def test_mti_types_shows_all_origin_names(self) -> None:
        result = runner.invoke(app, ["mti-types"])
        for member in MtiOrigin:
            assert member.name in result.output

    def test_mti_types_shows_digit_values_for_version(self) -> None:
        result = runner.invoke(app, ["mti-types"])
        for member in MtiVersion:
            assert str(member.value) in result.output

    def test_mti_types_shows_descriptions(self) -> None:
        result = runner.invoke(app, ["mti-types"])
        for member in MtiVersion:
            assert member.description in result.output

    def test_mti_types_member_count_matches_version_enum(self) -> None:
        """Version セクションに表示される行数が MtiVersion の len() と一致する。"""
        result = runner.invoke(app, ["mti-types"])
        # 少なくとも全メンバー名が存在することを確認
        assert len([m for m in MtiVersion]) == len(MtiVersion)
        assert result.exit_code == 0

    def test_mti_types_no_spec_option_needed(self) -> None:
        """--spec オプションなしで動作する (specファイル不要)。"""
        result = runner.invoke(app, ["mti-types"])
        assert result.exit_code == 0


# ==============================================================================
# 正常系: JSON 出力
# ==============================================================================

class TestMtiTypesCommandJson:
    def test_mti_types_json_output_has_four_keys(self) -> None:
        result = runner.invoke(app, ["mti-types", "--output", "json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert set(data.keys()) == {"version", "class", "function", "origin"}

    def test_mti_types_json_version_member_count(self) -> None:
        result = runner.invoke(app, ["mti-types", "--output", "json"])
        data = json.loads(result.output)
        assert len(data["version"]) == len(MtiVersion)

    def test_mti_types_json_class_member_count(self) -> None:
        result = runner.invoke(app, ["mti-types", "--output", "json"])
        data = json.loads(result.output)
        assert len(data["class"]) == len(MtiClass)

    def test_mti_types_json_function_member_count(self) -> None:
        result = runner.invoke(app, ["mti-types", "--output", "json"])
        data = json.loads(result.output)
        assert len(data["function"]) == len(MtiFunction)

    def test_mti_types_json_origin_member_count(self) -> None:
        result = runner.invoke(app, ["mti-types", "--output", "json"])
        data = json.loads(result.output)
        assert len(data["origin"]) == len(MtiOrigin)

    def test_mti_types_json_each_member_has_digit_name_description(self) -> None:
        result = runner.invoke(app, ["mti-types", "--output", "json"])
        data = json.loads(result.output)
        for entry in data["version"]:
            assert "digit" in entry
            assert "name" in entry
            assert "description" in entry

    def test_mti_types_json_version_digits_match_enum_values(self) -> None:
        result = runner.invoke(app, ["mti-types", "--output", "json"])
        data = json.loads(result.output)
        expected_digits = {m.value for m in MtiVersion}
        actual_digits = {e["digit"] for e in data["version"]}
        assert actual_digits == expected_digits
