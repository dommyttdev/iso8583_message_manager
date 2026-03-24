"""
mti-types コマンド: サポートされている MTI 種別一覧を表示する。

MtiVersion / MtiClass / MtiFunction / MtiOrigin の各 enum メンバーから
桁値・名前・説明を動的に読み取る。specファイルや外部依存は不要。
"""
import json
import logging
from enum import Enum
from typing import Annotated, Any

import typer
from rich.console import Console
from rich.table import Table

from iso8583_types.models.mti import MtiClass, MtiFunction, MtiOrigin, MtiVersion


class MtiOutput(str, Enum):
    table = "table"
    json = "json"

logger = logging.getLogger(__name__)

_ENUM_GROUPS: list[tuple[str, str, Any]] = [
    ("version", "Version (第1桁: バージョン)", MtiVersion),
    ("class", "Class (第2桁: クラス)", MtiClass),
    ("function", "Function (第3桁: 機能)", MtiFunction),
    ("origin", "Origin (第4桁: 発生源)", MtiOrigin),
]


def mti_types_command(
    output: Annotated[
        MtiOutput, typer.Option("--output", "-o", help="出力形式: table / json")
    ] = MtiOutput.table,
) -> None:
    """サポートされている MTI 種別一覧を表示します。"""
    logger.info("mti-typesコマンド実行: output=%s", output)

    if output == MtiOutput.json:
        _print_json()
    else:
        _print_table()

    logger.info("mti-typesコマンド完了")


def _build_entries(enum_cls: Any) -> list[dict[str, Any]]:
    """enum クラスからエントリリストを構築する。ハードコードなし。"""
    return [
        {"digit": int(member.value), "name": member.name, "description": member.description}
        for member in enum_cls
    ]


def _print_table() -> None:
    """全 enum グループをテーブル形式で出力する。"""
    # width=200: CliRunner/CI環境でのターミナル幅検出失敗による値切り詰めを防ぐ
    console = Console(highlight=False, width=200)

    for _key, title, enum_cls in _ENUM_GROUPS:
        table = Table(title=title, show_header=True, header_style="bold cyan")
        table.add_column("桁値", justify="right", no_wrap=True, width=4)
        table.add_column("名前", no_wrap=True)
        table.add_column("説明", no_wrap=True)

        for entry in _build_entries(enum_cls):
            table.add_row(str(entry["digit"]), entry["name"], entry["description"])

        console.print(table)


def _print_json() -> None:
    """全 enum グループを JSON 形式で出力する。"""
    data = {key: _build_entries(enum_cls) for key, _title, enum_cls in _ENUM_GROUPS}
    typer.echo(json.dumps(data, ensure_ascii=False, indent=2))
