"""
CLI 例外ハンドラ。

各例外を定義済みの終了コードにマッピングし、stderrへエラーメッセージを出力してから
typer.Exit を raise する。すべての CLI コマンドはこのハンドラを通じてエラーを処理する。
"""
import logging

import typer

from iso8583_types.core.exceptions import (
    InvalidMtiError,
    MessageDecodeError,
    MessageEncodeError,
    SpecError,
)

logger = logging.getLogger(__name__)

# 終了コード定義
EXIT_SUCCESS: int = 0
EXIT_USER_ERROR: int = 1   # 不正なCLI引数、不明なMTI、不明なフィールド名
EXIT_SPEC_ERROR: int = 2   # specファイル不正・未検出
EXIT_ENCODE_ERROR: int = 3  # メッセージエンコード失敗
EXIT_DECODE_ERROR: int = 4  # メッセージデコード失敗
EXIT_IO_ERROR: int = 5     # stdin/stdout のI/Oエラー
EXIT_UNEXPECTED: int = 10  # 予期しない例外


def handle_error(exc: Exception) -> None:
    """
    例外を終了コードにマッピングし、stderrにメッセージを出力して typer.Exit を raise する。

    Args:
        exc: 処理対象の例外

    Raises:
        typer.Exit: 常に raise される
    """
    if isinstance(exc, (InvalidMtiError, ValueError)):
        typer.echo(f"エラー: {exc}", err=True)
        raise typer.Exit(code=EXIT_USER_ERROR)

    if isinstance(exc, SpecError):
        typer.echo(f"Specファイルエラー: {exc}", err=True)
        raise typer.Exit(code=EXIT_SPEC_ERROR)

    if isinstance(exc, MessageEncodeError):
        typer.echo(f"エンコードエラー: {exc}", err=True)
        raise typer.Exit(code=EXIT_ENCODE_ERROR)

    if isinstance(exc, MessageDecodeError):
        typer.echo(f"デコードエラー: {exc}", err=True)
        raise typer.Exit(code=EXIT_DECODE_ERROR)

    if isinstance(exc, OSError):
        typer.echo(f"I/Oエラー: {exc}", err=True)
        raise typer.Exit(code=EXIT_IO_ERROR)

    # 予期しない例外: スタックトレース付きでERRORログを記録
    logger.error("予期しない例外が発生しました: %s", exc, exc_info=True)
    typer.echo(f"予期しないエラー: {exc}", err=True)
    raise typer.Exit(code=EXIT_UNEXPECTED)
