"""
CLI 境界値テスト。

ISO 8583 フィールドの最小・最大・超過値が CLI コマンドを通じて
正しく受け入れ / 拒否されることを検証する。
実際の PyIso8583Adapter と実 spec ファイルを使用する（モックなし）。
"""
import pytest
from importlib.resources import files as _pkg_files
from typer.testing import CliRunner

from iso8583_cli.app import app

runner = CliRunner()
_SPEC = str(_pkg_files("iso8583_core.data.schemas") / "iso8583_fields.json")


# ==============================================================================
# PAN (primary_account_number) 境界値
# ==============================================================================

class TestCliPanBoundary:
    def test_bv_cli_pan_01_min_length_1_accepted(self) -> None:
        """PAN 1 桁（最小）が exit_code 0 で生成されること"""
        result = runner.invoke(app, [
            "generate", "0200",
            "primary_account_number=1",
            "--spec", _SPEC,
        ])
        assert result.exit_code == 0, result.output
        bytes.fromhex(result.output.strip())  # 有効な hex であることを確認

    def test_bv_cli_pan_02_max_length_19_accepted(self) -> None:
        """PAN 19 桁（最大）が exit_code 0 で生成されること"""
        result = runner.invoke(app, [
            "generate", "0200",
            "primary_account_number=1234567890123456789",
            "--spec", _SPEC,
        ])
        assert result.exit_code == 0, result.output

    def test_bv_cli_pan_03_over_max_rejected(self) -> None:
        """PAN 20 桁（最大超過）が exit_code != 0 で拒否されること"""
        result = runner.invoke(app, [
            "generate", "0200",
            "primary_account_number=12345678901234567890",
            "--spec", _SPEC,
        ])
        assert result.exit_code != 0

    def test_bv_cli_pan_04_roundtrip_min_length(self) -> None:
        """PAN 1 桁のラウンドトリップが正確に一致すること"""
        gen = runner.invoke(app, [
            "generate", "0200",
            "primary_account_number=1",
            "--spec", _SPEC,
        ])
        assert gen.exit_code == 0
        import json
        parse = runner.invoke(app, ["parse", gen.output.strip(), "--spec", _SPEC])
        assert parse.exit_code == 0
        data = json.loads(parse.output)
        assert data["fields"]["primary_account_number"] == "1"

    def test_bv_cli_pan_05_roundtrip_max_length(self) -> None:
        """PAN 19 桁のラウンドトリップが正確に一致すること"""
        gen = runner.invoke(app, [
            "generate", "0200",
            "primary_account_number=1234567890123456789",
            "--spec", _SPEC,
        ])
        assert gen.exit_code == 0
        import json
        parse = runner.invoke(app, ["parse", gen.output.strip(), "--spec", _SPEC])
        assert parse.exit_code == 0
        data = json.loads(parse.output)
        assert data["fields"]["primary_account_number"] == "1234567890123456789"


# ==============================================================================
# 固定長フィールドの CLI 境界値
# ==============================================================================

class TestCliFixedLengthBoundary:
    @pytest.mark.parametrize("field,valid_value,invalid_short,invalid_long", [
        ("processing_code",            "123456",       "12345",        "1234567"),
        ("amount_transaction",         "000000001000", "00000000100",  "0000000010000"),
        ("transmission_date_and_time", "1234567890",   "123456789",    "12345678901"),
        ("systems_trace_audit_number", "111222",       "11122",        "1112222"),
        ("response_code",              "00",           "0",            "000"),
    ])
    def test_bv_cli_fixed_01_exact_length_accepted(
        self, field: str, valid_value: str, invalid_short: str, invalid_long: str
    ) -> None:
        """固定長フィールドの正確な長さが exit_code 0 で生成されること"""
        result = runner.invoke(app, [
            "generate", "0200",
            f"{field}={valid_value}",
            "--spec", _SPEC,
        ])
        assert result.exit_code == 0, f"{field}={valid_value!r}: {result.output}"

    @pytest.mark.parametrize("field,valid_value,invalid_short,invalid_long", [
        ("processing_code",            "123456",       "12345",        "1234567"),
        ("amount_transaction",         "000000001000", "00000000100",  "0000000010000"),
        ("transmission_date_and_time", "1234567890",   "123456789",    "12345678901"),
        ("systems_trace_audit_number", "111222",       "11122",        "1112222"),
        ("response_code",              "00",           "0",            "000"),
    ])
    def test_bv_cli_fixed_02_too_short_rejected(
        self, field: str, valid_value: str, invalid_short: str, invalid_long: str
    ) -> None:
        """固定長フィールドの短い値が拒否されること"""
        result = runner.invoke(app, [
            "generate", "0200",
            f"{field}={invalid_short}",
            "--spec", _SPEC,
        ])
        assert result.exit_code != 0, f"{field}={invalid_short!r}: exit != 0 expected"

    @pytest.mark.parametrize("field,valid_value,invalid_short,invalid_long", [
        ("processing_code",            "123456",       "12345",        "1234567"),
        ("amount_transaction",         "000000001000", "00000000100",  "0000000010000"),
        ("transmission_date_and_time", "1234567890",   "123456789",    "12345678901"),
        ("systems_trace_audit_number", "111222",       "11122",        "1112222"),
        ("response_code",              "00",           "0",            "000"),
    ])
    def test_bv_cli_fixed_03_too_long_rejected(
        self, field: str, valid_value: str, invalid_short: str, invalid_long: str
    ) -> None:
        """固定長フィールドの長い値が拒否されること"""
        result = runner.invoke(app, [
            "generate", "0200",
            f"{field}={invalid_long}",
            "--spec", _SPEC,
        ])
        assert result.exit_code != 0, f"{field}={invalid_long!r}: exit != 0 expected"


# ==============================================================================
# MTI なし / フィールドなし
# ==============================================================================

class TestCliMinimalMessage:
    def test_bv_cli_mti_only_message_generated(self) -> None:
        """フィールド未指定でも MTI のみのメッセージが生成されること"""
        result = runner.invoke(app, [
            "generate", "0200",
            "--spec", _SPEC,
        ])
        assert result.exit_code == 0
        hex_str = result.output.strip()
        raw = bytes.fromhex(hex_str)
        assert len(raw) > 0
