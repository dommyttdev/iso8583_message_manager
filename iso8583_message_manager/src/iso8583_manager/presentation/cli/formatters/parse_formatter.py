"""
parse コマンドの出力フォーマッタ。

json / table の各形式でデコード結果を出力する。
"""
import json

import typer
from rich.console import Console
from rich.table import Table

from iso8583_manager.core.models.generated.iso_models import Iso8583MessageModel
from iso8583_manager.core.models.mti import Mti


def print_json(mti: Mti, model: Iso8583MessageModel) -> None:
    """JSON 形式で標準出力に出力する。None フィールドは除外する。"""
    fields = {
        k: v
        for k, v in model.model_dump().items()
        if v is not None
    }
    typer.echo(json.dumps({"mti": mti.to_str(), "fields": fields}, ensure_ascii=False))


def print_table(mti: Mti, model: Iso8583MessageModel) -> None:
    """テーブル形式で標準出力に出力する。None フィールドは除外する。"""
    console = Console(highlight=False, width=200)

    table = Table(title=f"MTI: {mti.to_str()}", show_header=True, header_style="bold cyan")
    table.add_column("フィールド名", no_wrap=True)
    table.add_column("値", no_wrap=True)

    for field_name, value in model.model_dump().items():
        if value is not None:
            table.add_row(field_name, str(value))

    console.print(table)
