"""
iso8583_cli コマンドのユニットテスト。
"""
import pytest
from typer.testing import CliRunner
from unittest.mock import patch, MagicMock

from iso8583_cli.app import app


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


class TestGenerateCommand:
    def test_generate_exits_successfully_with_valid_input(self, runner: CliRunner):
        mock_uc = MagicMock()
        mock_uc.execute.return_value = bytearray(b"\x00\x01\x02")
        with patch("iso8583_cli.commands.generate.build_generate_use_case", return_value=mock_uc):
            result = runner.invoke(app, ["generate", "0200"])
        assert result.exit_code == 0

    def test_generate_fails_with_invalid_mti(self, runner: CliRunner):
        result = runner.invoke(app, ["generate", "XXXX"])
        assert result.exit_code != 0


class TestFieldsCommand:
    def test_fields_command_exits_successfully(self, runner: CliRunner):
        result = runner.invoke(app, ["fields"])
        assert result.exit_code == 0


class TestMtiTypesCommand:
    def test_mti_types_exits_successfully(self, runner: CliRunner):
        result = runner.invoke(app, ["mti-types"])
        assert result.exit_code == 0
