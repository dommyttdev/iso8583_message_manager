"""
統合エントリポイント。

iso8583-msg cli|api|web コマンドでモードを選択する。
python -m iso8583_manager でも起動可能。
"""
import logging

import typer

from iso8583_cli.app import app as _cli_app

logger = logging.getLogger(__name__)

app = typer.Typer(
    name="iso8583-msg",
    help="ISO 8583 メッセージツール。CLI・REST API・Web UI の各モードで起動できます。",
    no_args_is_help=True,
)

app.add_typer(_cli_app, name="cli", help="対話型 CLI モードを起動する")


@app.command("api")
def run_api(
    host: str = typer.Option("127.0.0.1", help="バインドするホスト"),
    port: int = typer.Option(8000, help="リッスンするポート番号"),
) -> None:
    """REST API サーバーを起動する"""
    try:
        import uvicorn
    except ImportError:
        typer.echo(
            "エラー: REST API の起動には追加パッケージが必要です。\n"
            "  pip install iso8583_manager[api]",
            err=True,
        )
        raise typer.Exit(code=1)

    logger.info("REST API サーバーを起動します: %s:%d", host, port)
    uvicorn.run(
        "iso8583_api.app:app",
        host=host,
        port=port,
    )


@app.command("web")
def run_web(
    host: str = typer.Option("127.0.0.1", help="バインドするホスト"),
    port: int = typer.Option(8080, help="リッスンするポート番号"),
) -> None:
    """Web UI を起動する（将来実装予定）"""
    try:
        import uvicorn
    except ImportError:
        typer.echo(
            "エラー: Web UI の起動には追加パッケージが必要です。\n"
            "  pip install iso8583_manager[web]",
            err=True,
        )
        raise typer.Exit(code=1)

    logger.info("Web UI を起動します: %s:%d", host, port)
    uvicorn.run(
        "iso8583_manager.presentation.web.app:app",
        host=host,
        port=port,
    )


def main() -> None:
    """console_scripts エントリポイント。"""
    app()


if __name__ == "__main__":
    main()
