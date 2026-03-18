"""
generate コマンド: ISO 8583 メッセージをエンコードして出力する。

MTI (4桁文字列) とフィールド値 (name=value 形式) を受け取り、
バイナリメッセージを hex / json / binary のいずれかで出力する。
"""
import logging
from typing import Annotated, List, Optional

import typer

from iso8583_manager.core.models.generated.iso_models import Iso8583MessageModel
from iso8583_manager.core.models.mti import Mti
from iso8583_manager.presentation.cli.error_handler import handle_error
from iso8583_manager.presentation.cli.formatters.generate_formatter import (
    print_binary,
    print_hex,
    print_json,
)
from iso8583_manager.presentation.container import build_generate_use_case

logger = logging.getLogger(__name__)


def generate_command(
    mti: Annotated[str, typer.Argument(help="4桁のMTI文字列 (例: 0200)")],
    fields: Annotated[
        Optional[List[str]],
        typer.Argument(help="フィールド指定 name=value 形式 (例: primary_account_number=1234567890123456)"),
    ] = None,
    output: Annotated[
        str, typer.Option("--output", "-o", help="出力形式: hex / json / binary")
    ] = "hex",
    spec: Annotated[Optional[str], typer.Option("--spec", help="spec JSONファイルのパス")] = None,
) -> None:
    """ISO 8583 メッセージをエンコードして出力します。"""
    try:
        logger.info("generateコマンド実行: mti=%s output=%s", mti, output)

        # MTI パース (InvalidMtiError は handle_error → exit 1)
        mti_obj = Mti.from_str(mti)

        # フィールド引数を dict に変換
        field_dict = _parse_fields(fields or [])

        # モデル構築 (ValidationError / ValueError は handle_error → exit 1)
        model = _build_model(field_dict)

        # use case 実行
        use_case = build_generate_use_case(spec)
        raw = use_case.execute(mti=mti_obj, model_data=model)

        # 出力
        if output == "json":
            print_json(mti, raw)
        elif output == "binary":
            print_binary(raw)
        else:
            print_hex(mti, raw)

        logger.info("generateコマンド完了: %d bytes", len(raw))

    except Exception as exc:
        handle_error(exc)


def _parse_fields(field_args: List[str]) -> dict[str, str]:
    """
    'name=value' 形式の引数リストを dict に変換する。

    値に '=' が含まれる場合は最初の '=' のみで分割する。
    不正な形式 (key がない) の場合は ValueError を raise する。
    """
    result: dict[str, str] = {}
    for arg in field_args:
        if "=" not in arg:
            raise ValueError(f"フィールド指定の形式が不正です (name=value 形式で指定してください): '{arg}'")
        key, _, value = arg.partition("=")
        if not key:
            raise ValueError(f"フィールド名が空です: '{arg}'")
        result[key] = value
    return result


def _build_model(field_dict: dict[str, str]) -> Iso8583MessageModel:
    """
    フィールド dict から Iso8583MessageModel を構築する。

    不明なフィールド名の場合は ValueError を raise する。
    max_length 超過は Pydantic の ValidationError として自動的に検出される。
    """
    valid_fields = set(Iso8583MessageModel.model_fields.keys())
    for key in field_dict:
        if key not in valid_fields:
            raise ValueError(
                f"不明なフィールド名: '{key}'\n"
                f"利用可能なフィールド一覧は 'iso8583 fields' コマンドで確認できます。"
            )
    return Iso8583MessageModel(**field_dict)
