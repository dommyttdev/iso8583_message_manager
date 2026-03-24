"""
parse コマンド: ISO 8583 メッセージをデコードして出力する。

hex エンコードされたメッセージ (引数または stdin) を受け取り、
デコード結果を json / table のいずれかで出力する。
"""
import logging
import sys
from enum import Enum
from typing import Annotated, Optional

import typer

from iso8583_types.models.generated.iso_models import Iso8583MessageModel
from iso8583_cli.container import build_parse_use_case
from iso8583_cli.error_handler import handle_error
from iso8583_cli.formatters.parse_formatter import (
    print_json,
    print_table,
)


class ParseOutput(str, Enum):
    json = "json"
    table = "table"

logger = logging.getLogger(__name__)


def parse_command(
    hex_message: Annotated[
        Optional[str], typer.Argument(help="hexエンコードされたISO 8583メッセージ")
    ] = None,
    output: Annotated[
        ParseOutput, typer.Option("--output", "-o", help="出力形式: json / table")
    ] = ParseOutput.json,
    spec: Annotated[Optional[str], typer.Option("--spec", help="spec JSONファイルのパス")] = None,
) -> None:
    """ISO 8583 メッセージをデコードして出力します。"""
    try:
        logger.info("parseコマンド実行: output=%s", output)

        # hex 文字列の取得 (引数 > stdin)
        raw_hex = _resolve_hex_input(hex_message)

        # hex → bytes 変換
        raw_bytes = _hex_to_bytes(raw_hex)

        # use case 実行
        use_case = build_parse_use_case(spec)
        mti, model = use_case.execute(raw_message=raw_bytes, model_cls=Iso8583MessageModel)

        # 出力
        if output == ParseOutput.table:
            print_table(mti, model)
        else:
            print_json(mti, model)

        logger.info("parseコマンド完了: MTI=%s", mti.to_str())

    except Exception as exc:
        handle_error(exc)


def _resolve_hex_input(hex_arg: Optional[str]) -> str:
    """引数またはstdinからhex文字列を取得する。どちらもなければ ValueError を raise する。"""
    if hex_arg is not None:
        stripped = hex_arg.strip()
        if not stripped:
            raise ValueError("hex メッセージを引数または標準入力で指定してください。")
        return stripped

    if not sys.stdin.isatty():
        data = sys.stdin.read().strip()
        if data:
            return data

    raise ValueError("hex メッセージを引数または標準入力で指定してください。")


def _hex_to_bytes(hex_str: str) -> bytes:
    """hex 文字列を bytes に変換する。不正な形式は ValueError を raise する。"""
    if len(hex_str) % 2 != 0:
        raise ValueError(f"hex 文字列の長さが奇数です (長さ: {len(hex_str)}): '{hex_str}'")
    try:
        return bytes.fromhex(hex_str)
    except ValueError:
        raise ValueError(f"不正な hex 文字列です: '{hex_str}'")
