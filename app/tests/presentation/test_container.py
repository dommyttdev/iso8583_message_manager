"""
container (DI ファクトリ) のユニットテスト。

TDD: Red Phase — テストを先に作成し、実装前に失敗することを確認する。
"""
import os
from pathlib import Path
from unittest.mock import patch

import pytest

from iso8583_manager.presentation.container import (
    build_generate_use_case,
    build_parse_use_case,
)
from iso8583_manager.use_cases.message_generation import GenerateMessageUseCase
from iso8583_manager.use_cases.message_parsing import ParseMessageUseCase

_REAL_SPEC_PATH = str(
    Path(__file__).parent.parent.parent / "data" / "schemas" / "iso8583_fields.json"
)


# ==============================================================================
# 戻り型の検証
# ==============================================================================

class TestBuildUseCaseReturnTypes:
    def test_build_generate_use_case_returns_correct_type(self) -> None:
        uc = build_generate_use_case(_REAL_SPEC_PATH)
        assert isinstance(uc, GenerateMessageUseCase)

    def test_build_parse_use_case_returns_correct_type(self) -> None:
        uc = build_parse_use_case(_REAL_SPEC_PATH)
        assert isinstance(uc, ParseMessageUseCase)


# ==============================================================================
# specパス解決の優先順位
# ==============================================================================

class TestSpecPathResolution:
    def test_cli_option_takes_priority_over_env_var(self) -> None:
        """CLIオプション > 環境変数 の優先順位を検証。"""
        with patch.dict(os.environ, {"ISO8583_SPEC_PATH": "/env/path.json"}):
            # CLIオプションを渡すと環境変数より優先される
            # 実際のspecファイルパスを渡して正常に生成できることを確認
            uc = build_generate_use_case(_REAL_SPEC_PATH)
        assert isinstance(uc, GenerateMessageUseCase)

    def test_env_var_overrides_default(self) -> None:
        """環境変数を設定すると、デフォルトパスより優先される。"""
        with patch.dict(os.environ, {"ISO8583_SPEC_PATH": _REAL_SPEC_PATH}):
            uc = build_generate_use_case(None)
        assert isinstance(uc, GenerateMessageUseCase)

    def test_default_path_resolves_to_existing_file(self) -> None:
        """CLIオプションも環境変数も未設定でもデフォルトパスが有効。"""
        env_without_spec = {k: v for k, v in os.environ.items() if k != "ISO8583_SPEC_PATH"}
        with patch.dict(os.environ, env_without_spec, clear=True):
            uc = build_generate_use_case(None)
        assert isinstance(uc, GenerateMessageUseCase)

    def test_invalid_spec_path_propagates_spec_error(self) -> None:
        """不正なspecパスはuse case実行時に SpecError を発生させる。"""
        from iso8583_manager.core.exceptions import SpecError
        from iso8583_manager.core.models.generated.iso_models import Iso8583MessageModel
        from iso8583_manager.core.models.mti import Mti

        with pytest.raises(SpecError):
            build_generate_use_case("/nonexistent/path/spec.json")
