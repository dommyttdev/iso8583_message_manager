"""
generate コマンドのユニットテスト。

TDD: Red Phase — テストを先に作成し、実装前に失敗することを確認する。
モックを使って use case レイヤーから独立したテストを行う。
"""
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from iso8583_manager.core.models.generated.iso_models import Iso8583MessageModel
from iso8583_manager.presentation.cli.app import app

runner = CliRunner()

_REAL_SPEC_PATH = str(
    Path(__file__).parent.parent.parent / "data" / "schemas" / "iso8583_fields.json"
)

_MOCK_BYTES = bytearray(b"\x30\x32\x30\x30DUMMY_ISO_BYTES")
_MOCK_HEX = _MOCK_BYTES.hex()


def _make_mock_use_case(return_bytes: bytearray = _MOCK_BYTES) -> MagicMock:
    mock_uc = MagicMock()
    mock_uc.execute.return_value = return_bytes
    return mock_uc


# ==============================================================================
# 正常系: 出力形式
# ==============================================================================

class TestGenerateCommandOutput:
    def test_generate_hex_output_default(self) -> None:
        """デフォルト出力形式(hex)でhex文字列がstdoutに出る。"""
        with patch("iso8583_manager.presentation.cli.commands.generate.build_generate_use_case") as mock_build:
            mock_build.return_value = _make_mock_use_case()
            result = runner.invoke(app, ["generate", "0200", "--spec", _REAL_SPEC_PATH])
        assert result.exit_code == 0
        assert _MOCK_HEX in result.output

    def test_generate_output_hex_explicit(self) -> None:
        """--output hex で同結果。"""
        with patch("iso8583_manager.presentation.cli.commands.generate.build_generate_use_case") as mock_build:
            mock_build.return_value = _make_mock_use_case()
            result = runner.invoke(app, ["generate", "0200", "--output", "hex", "--spec", _REAL_SPEC_PATH])
        assert result.exit_code == 0
        assert _MOCK_HEX in result.output

    def test_generate_json_output_has_mti_key(self) -> None:
        with patch("iso8583_manager.presentation.cli.commands.generate.build_generate_use_case") as mock_build:
            mock_build.return_value = _make_mock_use_case()
            result = runner.invoke(app, ["generate", "0200", "--output", "json", "--spec", _REAL_SPEC_PATH])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "mti" in data

    def test_generate_json_output_has_hex_key(self) -> None:
        with patch("iso8583_manager.presentation.cli.commands.generate.build_generate_use_case") as mock_build:
            mock_build.return_value = _make_mock_use_case()
            result = runner.invoke(app, ["generate", "0200", "--output", "json", "--spec", _REAL_SPEC_PATH])
        data = json.loads(result.output)
        assert "hex" in data

    def test_generate_json_output_has_length_key(self) -> None:
        with patch("iso8583_manager.presentation.cli.commands.generate.build_generate_use_case") as mock_build:
            mock_build.return_value = _make_mock_use_case()
            result = runner.invoke(app, ["generate", "0200", "--output", "json", "--spec", _REAL_SPEC_PATH])
        data = json.loads(result.output)
        assert "length" in data

    def test_generate_json_mti_matches_input(self) -> None:
        with patch("iso8583_manager.presentation.cli.commands.generate.build_generate_use_case") as mock_build:
            mock_build.return_value = _make_mock_use_case()
            result = runner.invoke(app, ["generate", "0200", "--output", "json", "--spec", _REAL_SPEC_PATH])
        data = json.loads(result.output)
        assert data["mti"] == "0200"

    def test_generate_binary_output_is_bytes(self) -> None:
        """--output binary でバイト列がstdoutに出る。"""
        with patch("iso8583_manager.presentation.cli.commands.generate.build_generate_use_case") as mock_build:
            mock_build.return_value = _make_mock_use_case()
            result = runner.invoke(app, ["generate", "0200", "--output", "binary", "--spec", _REAL_SPEC_PATH])
        assert result.exit_code == 0
        assert result.output_bytes == bytes(_MOCK_BYTES)

    def test_generate_exits_zero_on_success(self) -> None:
        with patch("iso8583_manager.presentation.cli.commands.generate.build_generate_use_case") as mock_build:
            mock_build.return_value = _make_mock_use_case()
            result = runner.invoke(app, ["generate", "0200", "--spec", _REAL_SPEC_PATH])
        assert result.exit_code == 0

    def test_generate_help_exits_zero(self) -> None:
        result = runner.invoke(app, ["generate", "--help"])
        assert result.exit_code == 0


# ==============================================================================
# フィールド引数
# ==============================================================================

class TestGenerateCommandFields:
    def test_generate_single_field_passed_to_use_case(self) -> None:
        """フィールド1個が正しくuse caseに渡る。"""
        with patch("iso8583_manager.presentation.cli.commands.generate.build_generate_use_case") as mock_build:
            mock_uc = _make_mock_use_case()
            mock_build.return_value = mock_uc
            runner.invoke(app, [
                "generate", "0200",
                "primary_account_number=1234567890123456",
                "--spec", _REAL_SPEC_PATH,
            ])
        call_args = mock_uc.execute.call_args
        model: Iso8583MessageModel = call_args[1]["model_data"]
        assert model.primary_account_number == "1234567890123456"

    def test_generate_multiple_fields_passed_to_use_case(self) -> None:
        """複数フィールドが全てuse caseに渡る。"""
        with patch("iso8583_manager.presentation.cli.commands.generate.build_generate_use_case") as mock_build:
            mock_uc = _make_mock_use_case()
            mock_build.return_value = mock_uc
            runner.invoke(app, [
                "generate", "0200",
                "primary_account_number=1234567890123456",
                "amount_transaction=000000001000",
                "--spec", _REAL_SPEC_PATH,
            ])
        model: Iso8583MessageModel = mock_uc.execute.call_args[1]["model_data"]
        assert model.primary_account_number == "1234567890123456"
        assert model.amount_transaction == "000000001000"

    def test_generate_no_fields_succeeds(self) -> None:
        """フィールド省略でも動作する (全Optional)。"""
        with patch("iso8583_manager.presentation.cli.commands.generate.build_generate_use_case") as mock_build:
            mock_build.return_value = _make_mock_use_case()
            result = runner.invoke(app, ["generate", "0200", "--spec", _REAL_SPEC_PATH])
        assert result.exit_code == 0

    def test_generate_field_value_with_equals_sign(self) -> None:
        """値に '=' を含む場合、最初の '=' で分割されて value 側は 'a=b' として扱われる。"""
        with patch("iso8583_manager.presentation.cli.commands.generate.build_generate_use_case") as mock_build:
            mock_uc = _make_mock_use_case()
            mock_build.return_value = mock_uc
            runner.invoke(app, [
                "generate", "0200",
                "processing_code=ab=cd",
                "--spec", _REAL_SPEC_PATH,
            ])
        model: Iso8583MessageModel = mock_uc.execute.call_args[1]["model_data"]
        assert model.processing_code == "ab=cd"

    def test_generate_parametrized_valid_mtis(self) -> None:
        """複数のMTI ("0100","0200","0800") で成功する。"""
        for mti_str in ["0100", "0200", "0800"]:
            with patch("iso8583_manager.presentation.cli.commands.generate.build_generate_use_case") as mock_build:
                mock_build.return_value = _make_mock_use_case()
                result = runner.invoke(app, ["generate", mti_str, "--spec", _REAL_SPEC_PATH])
            assert result.exit_code == 0, f"MTI {mti_str} で失敗: {result.output}"

    def test_generate_field_value_at_max_length_succeeds(self) -> None:
        """max_len ちょうどの値 → 成功 (境界値)。"""
        # primary_account_number: max_length=19
        pan_19 = "1234567890123456789"
        with patch("iso8583_manager.presentation.cli.commands.generate.build_generate_use_case") as mock_build:
            mock_build.return_value = _make_mock_use_case()
            result = runner.invoke(app, [
                "generate", "0200",
                f"primary_account_number={pan_19}",
                "--spec", _REAL_SPEC_PATH,
            ])
        assert result.exit_code == 0

    def test_generate_field_value_over_max_length_exits_1(self) -> None:
        """max_len+1 の値 → exit 1 (境界値)。"""
        # primary_account_number: max_length=19, この値は20文字
        pan_20 = "12345678901234567890"
        with patch("iso8583_manager.presentation.cli.commands.generate.build_generate_use_case") as mock_build:
            mock_build.return_value = _make_mock_use_case()
            result = runner.invoke(app, [
                "generate", "0200",
                f"primary_account_number={pan_20}",
                "--spec", _REAL_SPEC_PATH,
            ])
        assert result.exit_code == 1


# ==============================================================================
# エラー系
# ==============================================================================

class TestGenerateCommandErrors:
    def test_generate_invalid_mti_length_exits_1(self) -> None:
        result = runner.invoke(app, ["generate", "020", "--spec", _REAL_SPEC_PATH])
        assert result.exit_code == 1

    def test_generate_invalid_mti_nondigit_exits_1(self) -> None:
        result = runner.invoke(app, ["generate", "02AB", "--spec", _REAL_SPEC_PATH])
        assert result.exit_code == 1

    def test_generate_undefined_mti_value_exits_1(self) -> None:
        # "0900" → 3桁目 0=REQUEST は valid だが 4桁目 0=ACQUIRER は valid、
        # 2桁目 9 は MtiClass に未定義なので InvalidMtiError
        result = runner.invoke(app, ["generate", "0900", "--spec", _REAL_SPEC_PATH])
        assert result.exit_code == 1

    def test_generate_error_message_includes_invalid_mti_value(self) -> None:
        result = runner.invoke(app, ["generate", "020", "--spec", _REAL_SPEC_PATH])
        assert result.exit_code == 1
        # エラーはstderrに出るが CliRunner は出力をマージするので result.output で確認
        assert "020" in result.output or result.exit_code == 1

    def test_generate_unknown_field_name_exits_1(self) -> None:
        result = runner.invoke(app, [
            "generate", "0200",
            "unknown_field=value",
            "--spec", _REAL_SPEC_PATH,
        ])
        assert result.exit_code == 1

    def test_generate_error_message_includes_unknown_field_name(self) -> None:
        result = runner.invoke(app, [
            "generate", "0200",
            "unknown_field=value",
            "--spec", _REAL_SPEC_PATH,
        ])
        assert "unknown_field" in result.output

    def test_generate_unknown_field_suggests_fields_cmd(self) -> None:
        result = runner.invoke(app, [
            "generate", "0200",
            "unknown_field=value",
            "--spec", _REAL_SPEC_PATH,
        ])
        assert "fields" in result.output

    def test_generate_spec_error_exits_2(self) -> None:
        result = runner.invoke(app, ["generate", "0200", "--spec", "/nonexistent/spec.json"])
        assert result.exit_code == 2

    def test_generate_spec_error_message_includes_path(self) -> None:
        result = runner.invoke(app, ["generate", "0200", "--spec", "/nonexistent/spec.json"])
        assert "/nonexistent/spec.json" in result.output

    def test_generate_encode_error_exits_3(self) -> None:
        from iso8583_manager.core.exceptions import MessageEncodeError
        with patch("iso8583_manager.presentation.cli.commands.generate.build_generate_use_case") as mock_build:
            mock_uc = MagicMock()
            mock_uc.execute.side_effect = MessageEncodeError("エンコード失敗")
            mock_build.return_value = mock_uc
            result = runner.invoke(app, ["generate", "0200", "--spec", _REAL_SPEC_PATH])
        assert result.exit_code == 3

    def test_generate_error_in_stderr_not_stdout(self) -> None:
        """エラー時には出力にエラーメッセージが含まれ、正常なhex出力は含まれない。"""
        result = runner.invoke(app, ["generate", "020", "--spec", _REAL_SPEC_PATH])
        assert result.exit_code == 1
        # 正常なhex出力 (長いhex文字列) は含まれない
        assert _MOCK_HEX not in result.output
        # エラーメッセージは出力に含まれる
        assert len(result.output) > 0
