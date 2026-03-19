"""
generate コマンドの出力フォーマッタ。

hex / json / binary の各形式でエンコード結果を出力する。
"""
import json

import typer


def print_hex(mti_str: str, raw: bytearray) -> None:
    """hex 文字列として標準出力に出力する。"""
    typer.echo(raw.hex())


def print_json(mti_str: str, raw: bytearray) -> None:
    """JSON 形式で標準出力に出力する。"""
    typer.echo(json.dumps({
        "mti": mti_str,
        "hex": raw.hex(),
        "length": len(raw),
    }, ensure_ascii=False))


def print_binary(raw: bytearray) -> None:
    """生バイト列を標準出力に書き込む。"""
    import sys
    sys.stdout.buffer.write(bytes(raw))
    sys.stdout.buffer.flush()
