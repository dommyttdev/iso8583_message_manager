"""
DI コンテナ（ファクトリ関数）。

このモジュールのみが PyIso8583Adapter を直接 import する。
CLI コマンドはこのファクトリを通じてユースケースを取得し、
インフラ層の具体的な実装を知らなくて済む（Clean Architecture の Composition Root）。
"""
import logging
import os
from importlib.resources import files
from pathlib import Path

from iso8583_manager.infrastructure.pyiso8583_adapter.wrapper import PyIso8583Adapter
from iso8583_manager.use_cases.message_generation import GenerateMessageUseCase
from iso8583_manager.use_cases.message_parsing import ParseMessageUseCase

logger = logging.getLogger(__name__)

# importlib.resources 経由でパッケージデータを参照（インストール後も正しく動作）
_DEFAULT_SPEC_PATH: Path = Path(
    str(files("iso8583_manager.data.schemas") / "iso8583_fields.json")
)


def _resolve_spec_path(cli_option: str | None) -> str:
    """
    spec ファイルパスを優先順位に従って解決する。

    優先順位: CLIオプション > 環境変数 ISO8583_SPEC_PATH > パッケージ相対デフォルト
    """
    if cli_option is not None:
        logger.debug("specパスにCLIオプションを使用: %s", cli_option)
        return cli_option

    env_path = os.environ.get("ISO8583_SPEC_PATH")
    if env_path:
        logger.debug("specパスに環境変数を使用: %s", env_path)
        return env_path

    logger.debug("specパスにデフォルト値を使用: %s", _DEFAULT_SPEC_PATH)
    return str(_DEFAULT_SPEC_PATH)


def build_generate_use_case(spec_path: str | None = None) -> GenerateMessageUseCase:
    """
    GenerateMessageUseCase を組み立てて返す。

    Args:
        spec_path: specファイルのパス。None の場合は環境変数またはデフォルトを使用。
    """
    resolved = _resolve_spec_path(spec_path)
    adapter = PyIso8583Adapter(spec_json_path=resolved)
    return GenerateMessageUseCase(message_generator=adapter)


def build_parse_use_case(spec_path: str | None = None) -> ParseMessageUseCase:
    """
    ParseMessageUseCase を組み立てて返す。

    Args:
        spec_path: specファイルのパス。None の場合は環境変数またはデフォルトを使用。
    """
    resolved = _resolve_spec_path(spec_path)
    adapter = PyIso8583Adapter(spec_json_path=resolved)
    return ParseMessageUseCase(message_generator=adapter)
