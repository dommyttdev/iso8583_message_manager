"""
parse コマンドのユニットテスト。

TDD: Red Phase — テストを先に作成し、実装前に失敗することを確認する。
"""
import json
from importlib.resources import files as _pkg_files
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from iso8583_types.core.models.generated.iso_models import Iso8583MessageModel
from iso8583_types.core.models.mti import Mti
from iso8583_manager.presentation.cli.app import app

runner = CliRunner()

_REAL_SPEC_PATH = str(_pkg_files("iso8583_core.data.schemas") / "iso8583_fields.json")

_SAMPLE_MTI = Mti.from_str("0200")
_SAMPLE_MODEL = Iso8583MessageModel(
    primary_account_number="1234567890123456",
    amount_transaction="000000001000",
)
# 実際のhexは generate テストで得たバイト列を模したダミー
_DUMMY_BYTES = bytearray(b"\x30\x32\x30\x30DUMMY")
_DUMMY_HEX = _DUMMY_BYTES.hex()


def _make_mock_use_case(mti: Mti = _SAMPLE_MTI, model: Iso8583MessageModel = _SAMPLE_MODEL) -> MagicMock:
    mock_uc = MagicMock()
    mock_uc.execute.return_value = (mti, model)
    return mock_uc


# ==============================================================================
# 正常系: JSON 出力 (デフォルト)
# ==============================================================================

class TestParseCommandJsonOutput:
    def test_parse_hex_arg_json_output(self) -> None:
        with patch("iso8583_manager.presentation.cli.commands.parse.build_parse_use_case") as mock_build:
            mock_build.return_value = _make_mock_use_case()
            result = runner.invoke(app, ["parse", _DUMMY_HEX, "--spec", _REAL_SPEC_PATH])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "mti" in data

    def test_parse_json_contains_mti(self) -> None:
        with patch("iso8583_manager.presentation.cli.commands.parse.build_parse_use_case") as mock_build:
            mock_build.return_value = _make_mock_use_case()
            result = runner.invoke(app, ["parse", _DUMMY_HEX, "--spec", _REAL_SPEC_PATH])
        data = json.loads(result.output)
        assert data["mti"] == "0200"

    def test_parse_json_contains_fields(self) -> None:
        with patch("iso8583_manager.presentation.cli.commands.parse.build_parse_use_case") as mock_build:
            mock_build.return_value = _make_mock_use_case()
            result = runner.invoke(app, ["parse", _DUMMY_HEX, "--spec", _REAL_SPEC_PATH])
        data = json.loads(result.output)
        assert "fields" in data

    def test_parse_json_fields_has_correct_values(self) -> None:
        with patch("iso8583_manager.presentation.cli.commands.parse.build_parse_use_case") as mock_build:
            mock_build.return_value = _make_mock_use_case()
            result = runner.invoke(app, ["parse", _DUMMY_HEX, "--spec", _REAL_SPEC_PATH])
        data = json.loads(result.output)
        assert data["fields"]["primary_account_number"] == "1234567890123456"

    def test_parse_json_none_fields_omitted(self) -> None:
        """None フィールドは JSON 出力に含まれない。"""
        with patch("iso8583_manager.presentation.cli.commands.parse.build_parse_use_case") as mock_build:
            mock_build.return_value = _make_mock_use_case()
            result = runner.invoke(app, ["parse", _DUMMY_HEX, "--spec", _REAL_SPEC_PATH])
        data = json.loads(result.output)
        # response_code はサンプルモデルに設定していないので含まれない
        assert "response_code" not in data["fields"]

    def test_parse_exits_zero_on_success(self) -> None:
        with patch("iso8583_manager.presentation.cli.commands.parse.build_parse_use_case") as mock_build:
            mock_build.return_value = _make_mock_use_case()
            result = runner.invoke(app, ["parse", _DUMMY_HEX, "--spec", _REAL_SPEC_PATH])
        assert result.exit_code == 0

    def test_parse_help_exits_zero(self) -> None:
        result = runner.invoke(app, ["parse", "--help"])
        assert result.exit_code == 0


# ==============================================================================
# 正常系: テーブル出力
# ==============================================================================

class TestParseCommandTableOutput:
    def test_parse_table_output_shows_field_names(self) -> None:
        with patch("iso8583_manager.presentation.cli.commands.parse.build_parse_use_case") as mock_build:
            mock_build.return_value = _make_mock_use_case()
            result = runner.invoke(app, ["parse", _DUMMY_HEX, "--output", "table", "--spec", _REAL_SPEC_PATH])
        assert result.exit_code == 0
        assert "primary_account_number" in result.output

    def test_parse_table_output_shows_field_values(self) -> None:
        with patch("iso8583_manager.presentation.cli.commands.parse.build_parse_use_case") as mock_build:
            mock_build.return_value = _make_mock_use_case()
            result = runner.invoke(app, ["parse", _DUMMY_HEX, "--output", "table", "--spec", _REAL_SPEC_PATH])
        assert "1234567890123456" in result.output

    def test_parse_table_shows_mti(self) -> None:
        with patch("iso8583_manager.presentation.cli.commands.parse.build_parse_use_case") as mock_build:
            mock_build.return_value = _make_mock_use_case()
            result = runner.invoke(app, ["parse", _DUMMY_HEX, "--output", "table", "--spec", _REAL_SPEC_PATH])
        assert "0200" in result.output

    def test_parse_table_partial_fields_no_crash(self) -> None:
        """一部フィールドのみのモデルでもテーブルが崩れない。"""
        model = Iso8583MessageModel(response_code="00")
        with patch("iso8583_manager.presentation.cli.commands.parse.build_parse_use_case") as mock_build:
            mock_build.return_value = _make_mock_use_case(model=model)
            result = runner.invoke(app, ["parse", _DUMMY_HEX, "--output", "table", "--spec", _REAL_SPEC_PATH])
        assert result.exit_code == 0
        assert "response_code" in result.output


# ==============================================================================
# 正常系: stdin 入力
# ==============================================================================

class TestParseCommandStdinInput:
    def test_parse_stdin_hex_input(self) -> None:
        """hex 文字列を stdin から読み込む。"""
        with patch("iso8583_manager.presentation.cli.commands.parse.build_parse_use_case") as mock_build:
            mock_build.return_value = _make_mock_use_case()
            result = runner.invoke(app, ["parse", "--spec", _REAL_SPEC_PATH], input=_DUMMY_HEX)
        assert result.exit_code == 0

    def test_parse_stdin_hex_with_newline(self) -> None:
        """末尾に改行があっても正常に処理される。"""
        with patch("iso8583_manager.presentation.cli.commands.parse.build_parse_use_case") as mock_build:
            mock_build.return_value = _make_mock_use_case()
            result = runner.invoke(app, ["parse", "--spec", _REAL_SPEC_PATH], input=_DUMMY_HEX + "\n")
        assert result.exit_code == 0

    def test_parse_bytes_passed_to_use_case(self) -> None:
        """use case に正しい bytes が渡される。"""
        with patch("iso8583_manager.presentation.cli.commands.parse.build_parse_use_case") as mock_build:
            mock_uc = _make_mock_use_case()
            mock_build.return_value = mock_uc
            runner.invoke(app, ["parse", _DUMMY_HEX, "--spec", _REAL_SPEC_PATH])
        called_bytes = mock_uc.execute.call_args[1]["raw_message"]
        assert called_bytes == bytes(_DUMMY_BYTES)


# ==============================================================================
# エラー系
# ==============================================================================

class TestParseCommandErrors:
    def test_parse_invalid_hex_chars_exits_1(self) -> None:
        result = runner.invoke(app, ["parse", "ZZZZ", "--spec", _REAL_SPEC_PATH])
        assert result.exit_code == 1

    def test_parse_odd_length_hex_exits_1(self) -> None:
        result = runner.invoke(app, ["parse", "abc", "--spec", _REAL_SPEC_PATH])
        assert result.exit_code == 1

    def test_parse_no_input_exits_1(self) -> None:
        """引数もstdinもなし → exit 1。"""
        result = runner.invoke(app, ["parse", "--spec", _REAL_SPEC_PATH], input="")
        assert result.exit_code == 1

    def test_parse_decode_error_exits_4(self) -> None:
        from iso8583_types.core.exceptions import MessageDecodeError
        with patch("iso8583_manager.presentation.cli.commands.parse.build_parse_use_case") as mock_build:
            mock_uc = MagicMock()
            mock_uc.execute.side_effect = MessageDecodeError("デコード失敗")
            mock_build.return_value = mock_uc
            result = runner.invoke(app, ["parse", _DUMMY_HEX, "--spec", _REAL_SPEC_PATH])
        assert result.exit_code == 4

    def test_parse_spec_error_exits_2(self) -> None:
        result = runner.invoke(app, ["parse", _DUMMY_HEX, "--spec", "/nonexistent/spec.json"])
        assert result.exit_code == 2

    def test_parse_error_in_output_not_empty(self) -> None:
        """エラー時には出力にメッセージが含まれる。"""
        result = runner.invoke(app, ["parse", "ZZZZ", "--spec", _REAL_SPEC_PATH])
        assert result.exit_code == 1
        assert len(result.output) > 0
