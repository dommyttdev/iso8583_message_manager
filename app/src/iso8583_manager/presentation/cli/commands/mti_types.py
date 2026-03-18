"""mti-types コマンド (実装予定)。"""
from typing import Annotated

import typer


def mti_types_command(
    output: Annotated[
        str, typer.Option("--output", "-o", help="出力形式: table / json")
    ] = "table",
) -> None:
    """サポートされている MTI 種別一覧を表示します。"""
    raise NotImplementedError("mti-types コマンドは未実装です")
