"""generate コマンド (実装予定)。"""
from typing import Annotated, List, Optional

import typer


def generate_command(
    mti: Annotated[str, typer.Argument(help="4桁のMTI文字列 (例: 0200)")],
    fields: Annotated[
        Optional[List[str]],
        typer.Argument(help="フィールド指定 name=value 形式"),
    ] = None,
    output: Annotated[
        str, typer.Option("--output", "-o", help="出力形式: hex / json / binary")
    ] = "hex",
    spec: Annotated[Optional[str], typer.Option("--spec", help="spec JSONファイルのパス")] = None,
) -> None:
    """ISO 8583 メッセージをエンコードして出力します。"""
    raise NotImplementedError("generate コマンドは未実装です")
