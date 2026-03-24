"""
fields コマンド: ISO 8583 フィールド定義一覧を表示する。

specファイルを直接読み込み、フィールドID・名前・説明・最大長・データ型を
rich テーブルとして表示する。ユースケース・アダプターは使用しない。
"""
import json
import logging
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from iso8583_types.core.exceptions import SpecError
from iso8583_manager.presentation.cli.error_handler import handle_error
from iso8583_manager.presentation.container import _DEFAULT_SPEC_PATH

logger = logging.getLogger(__name__)


def fields_command(
    spec: Optional[str] = typer.Option(None, "--spec", help="ISO 8583 spec JSONファイルのパス"),
) -> None:
    """ISO 8583 フィールド定義の一覧を表示します。"""
    spec_path = spec if spec is not None else str(_DEFAULT_SPEC_PATH)

    try:
        logger.info("fieldsコマンド実行: spec=%s", spec_path)
        _show_fields(spec_path)
    except Exception as exc:
        handle_error(exc)


def _show_fields(spec_path: str) -> None:
    """specファイルを読み込み、フィールド一覧をテーブル表示する。"""
    try:
        with open(spec_path, encoding="utf-8") as f:
            fields: dict[str, dict[str, object]] = json.load(f)
    except FileNotFoundError as e:
        raise SpecError(f"スペックファイルが見つかりません: {spec_path}") from e
    except json.JSONDecodeError as e:
        raise SpecError(f"スペックファイルの形式が正しくありません: {spec_path}") from e

    table = Table(title="ISO 8583 フィールド定義", show_header=True, header_style="bold cyan")
    table.add_column("フィールドID", style="bold", no_wrap=True)
    table.add_column("プロパティ名", no_wrap=True)
    table.add_column("説明", no_wrap=True)
    table.add_column("データ型", no_wrap=True)
    table.add_column("最大長", justify="right", no_wrap=True)

    for field_id, meta in sorted(fields.items(), key=lambda x: int(x[0])):
        table.add_row(
            field_id,
            str(meta.get("name", "")),
            str(meta.get("description", "")),
            str(meta.get("data_type", "")),
            str(meta.get("max_len", "")),
        )

    # width=200: CliRunner/CI環境でのターミナル幅検出失敗による値切り詰めを防ぐ
    console = Console(highlight=False, width=200)
    console.print(table)
    logger.info("fieldsコマンド完了: %d フィールドを表示", len(fields))
