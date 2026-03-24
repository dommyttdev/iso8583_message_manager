"""
DI コンテナ（container.py）のユニットテスト。

_resolve_spec_path の優先順位:
  CLIオプション > 環境変数 ISO8583_SPEC_PATH > パッケージ相対デフォルト

build_generate_use_case / build_parse_use_case の生成を検証する。
"""
import pytest

from iso8583_core.use_cases.message_generation import GenerateMessageUseCase
from iso8583_core.use_cases.message_parsing import ParseMessageUseCase
from iso8583_api.container import _resolve_spec_path, build_generate_use_case, build_parse_use_case


class TestResolveSpecPath:
    def test_container_01_cli_option_takes_priority(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """CLIオプションが環境変数より優先されること"""
        monkeypatch.setenv("ISO8583_SPEC_PATH", "/env/path.json")
        result = _resolve_spec_path("/cli/path.json")
        assert result == "/cli/path.json"

    def test_container_02_env_var_used_when_no_cli_option(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """CLIオプションが None のとき環境変数が使われること"""
        monkeypatch.setenv("ISO8583_SPEC_PATH", "/env/path.json")
        result = _resolve_spec_path(None)
        assert result == "/env/path.json"

    def test_container_03_default_path_when_no_env_var(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """環境変数も CLIオプションもない場合はデフォルトパスが返ること"""
        monkeypatch.delenv("ISO8583_SPEC_PATH", raising=False)
        result = _resolve_spec_path(None)
        assert result.endswith("iso8583_fields.json")

    def test_container_04_empty_env_var_falls_through_to_default(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """空文字の環境変数はデフォルトパスにフォールスルーすること"""
        monkeypatch.setenv("ISO8583_SPEC_PATH", "")
        result = _resolve_spec_path(None)
        assert result.endswith("iso8583_fields.json")


class TestBuildUseCases:
    def test_container_05_build_generate_use_case_returns_correct_type(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """build_generate_use_case が GenerateMessageUseCase を返すこと"""
        monkeypatch.delenv("ISO8583_SPEC_PATH", raising=False)
        use_case = build_generate_use_case()
        assert isinstance(use_case, GenerateMessageUseCase)

    def test_container_06_build_parse_use_case_returns_correct_type(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """build_parse_use_case が ParseMessageUseCase を返すこと"""
        monkeypatch.delenv("ISO8583_SPEC_PATH", raising=False)
        use_case = build_parse_use_case()
        assert isinstance(use_case, ParseMessageUseCase)

    def test_container_07_build_generate_uses_cli_option(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """build_generate_use_case が spec_path オプションを受け入れること"""
        monkeypatch.delenv("ISO8583_SPEC_PATH", raising=False)
        # デフォルトパスと同じパスを渡して正常に生成できることを確認
        from iso8583_api.container import _DEFAULT_SPEC_PATH
        use_case = build_generate_use_case(str(_DEFAULT_SPEC_PATH))
        assert isinstance(use_case, GenerateMessageUseCase)

    def test_container_08_build_parse_uses_env_var(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """build_parse_use_case が環境変数パスを使用すること"""
        from iso8583_api.container import _DEFAULT_SPEC_PATH
        monkeypatch.setenv("ISO8583_SPEC_PATH", str(_DEFAULT_SPEC_PATH))
        use_case = build_parse_use_case()
        assert isinstance(use_case, ParseMessageUseCase)
