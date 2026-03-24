"""
CLI エントリーポイント。

typer アプリケーションの定義とコマンド登録を行う。
`iso8583` コマンドのルートとして機能する。
"""
import typer

from iso8583_cli.commands.fields import fields_command
from iso8583_cli.commands.generate import generate_command
from iso8583_cli.commands.mti_types import mti_types_command
from iso8583_cli.commands.parse import parse_command

app = typer.Typer(
    name="iso8583",
    help="ISO 8583 メッセージの生成・解析ツール",
    no_args_is_help=True,
)

app.command("fields")(fields_command)
app.command("mti-types")(mti_types_command)
app.command("generate")(generate_command)
app.command("parse")(parse_command)


def main() -> None:
    """console_scripts エントリーポイント。"""
    app()
