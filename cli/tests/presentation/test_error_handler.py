"""
error_handler のユニットテスト。

TDD: Red Phase — テストを先に作成し、実装前に失敗することを確認する。
"""
import logging

import pytest
import typer

from iso8583_types.core.exceptions import (
    InvalidMtiError,
    MessageDecodeError,
    MessageEncodeError,
    SpecError,
)
from iso8583_cli.error_handler import (
    EXIT_DECODE_ERROR,
    EXIT_ENCODE_ERROR,
    EXIT_IO_ERROR,
    EXIT_SPEC_ERROR,
    EXIT_UNEXPECTED,
    EXIT_USER_ERROR,
    handle_error,
)


# ==============================================================================
# 終了コードマッピング
# ==============================================================================

class TestExitCodes:
    def test_invalid_mti_error_exits_1(self) -> None:
        with pytest.raises(typer.Exit) as exc_info:
            handle_error(InvalidMtiError("MTI不正"))
        assert exc_info.value.exit_code == EXIT_USER_ERROR

    def test_value_error_exits_1(self) -> None:
        with pytest.raises(typer.Exit) as exc_info:
            handle_error(ValueError("不明フィールド"))
        assert exc_info.value.exit_code == EXIT_USER_ERROR

    def test_spec_error_exits_2(self) -> None:
        with pytest.raises(typer.Exit) as exc_info:
            handle_error(SpecError("spec不正"))
        assert exc_info.value.exit_code == EXIT_SPEC_ERROR

    def test_message_encode_error_exits_3(self) -> None:
        with pytest.raises(typer.Exit) as exc_info:
            handle_error(MessageEncodeError("エンコード失敗"))
        assert exc_info.value.exit_code == EXIT_ENCODE_ERROR

    def test_message_decode_error_exits_4(self) -> None:
        with pytest.raises(typer.Exit) as exc_info:
            handle_error(MessageDecodeError("デコード失敗"))
        assert exc_info.value.exit_code == EXIT_DECODE_ERROR

    def test_os_error_exits_5(self) -> None:
        with pytest.raises(typer.Exit) as exc_info:
            handle_error(OSError("IO失敗"))
        assert exc_info.value.exit_code == EXIT_IO_ERROR

    def test_unexpected_error_exits_10(self) -> None:
        with pytest.raises(typer.Exit) as exc_info:
            handle_error(RuntimeError("予期しないエラー"))
        assert exc_info.value.exit_code == EXIT_UNEXPECTED


# ==============================================================================
# エラーメッセージ出力
# ==============================================================================

class TestErrorOutput:
    def test_error_message_written_to_stderr(self, capsys: pytest.CaptureFixture[str]) -> None:
        with pytest.raises(typer.Exit):
            handle_error(SpecError("specエラー"))
        captured = capsys.readouterr()
        assert "specエラー" in captured.err
        assert captured.out == ""

    def test_invalid_mti_message_in_stderr(self, capsys: pytest.CaptureFixture[str]) -> None:
        with pytest.raises(typer.Exit):
            handle_error(InvalidMtiError("MTIが不正です"))
        captured = capsys.readouterr()
        assert "MTIが不正です" in captured.err

    def test_stdout_empty_on_error(self, capsys: pytest.CaptureFixture[str]) -> None:
        with pytest.raises(typer.Exit):
            handle_error(MessageEncodeError("エラー"))
        captured = capsys.readouterr()
        assert captured.out == ""


# ==============================================================================
# ロギング
# ==============================================================================

class TestErrorLogging:
    def test_unexpected_error_logged_with_exc_info(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        exc = RuntimeError("予期しないエラー")
        with caplog.at_level(logging.ERROR):
            with pytest.raises(typer.Exit):
                handle_error(exc)
        error_records = [r for r in caplog.records if r.levelno == logging.ERROR]
        assert len(error_records) > 0
        assert error_records[0].exc_info is not None

    def test_known_error_not_logged_with_exc_info(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """既知の例外（SpecError等）はスタックトレース不要でERRORログは記録しない。"""
        with caplog.at_level(logging.DEBUG):
            with pytest.raises(typer.Exit):
                handle_error(SpecError("spec不正"))
        error_records = [r for r in caplog.records if r.levelno == logging.ERROR]
        assert len(error_records) == 0


# ==============================================================================
# typer.Exit の raise 保証
# ==============================================================================

class TestRaisesTyperExit:
    def test_always_raises_typer_exit_for_known_errors(self) -> None:
        for exc in [
            InvalidMtiError("x"),
            SpecError("x"),
            MessageEncodeError("x"),
            MessageDecodeError("x"),
            OSError("x"),
        ]:
            with pytest.raises(typer.Exit):
                handle_error(exc)

    def test_always_raises_typer_exit_for_unexpected_error(self) -> None:
        with pytest.raises(typer.Exit):
            handle_error(RuntimeError("x"))
