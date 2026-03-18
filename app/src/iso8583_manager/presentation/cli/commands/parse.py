"""parse コマンド (実装予定)。"""
from typing import Annotated, Optional

import typer


def parse_command(
    hex_message: Annotated[Optional[str], typer.Argument(help="hexエンコードされたISO 8583メッセージ")] = None,
    output: Annotated[
        str, typer.Option("--output", "-o", help="出力形式: json / table")
    ] = "json",
    spec: Annotated[Optional[str], typer.Option("--spec", help="spec JSONファイルのパス")] = None,
) -> None:
    """ISO 8583 メッセージをデコードして出力します。"""
    raise NotImplementedError("parse コマンドは未実装です")
