"""
__main__.py（統合エントリポイント）のユニットテスト。

iso8583-msg cli|api|web サブコマンドが正しく登録されていることを検証する。
"""
import importlib

import pytest
from typer.testing import CliRunner


class TestMainModule:
    def test_main_01_module_importable(self) -> None:
        """iso8583_manager.__main__ がインポートできること"""
        mod = importlib.import_module("iso8583_manager.__main__")
        assert mod is not None

    def test_main_02_main_function_exists(self) -> None:
        """main() 関数が存在すること"""
        mod = importlib.import_module("iso8583_manager.__main__")
        assert hasattr(mod, "main")
        assert callable(mod.main)

    def test_main_03_app_object_exists(self) -> None:
        """Typer app オブジェクトが存在すること"""
        import typer
        mod = importlib.import_module("iso8583_manager.__main__")
        assert hasattr(mod, "app")
        assert isinstance(mod.app, typer.Typer)


class TestMainSubcommands:
    @pytest.fixture(autouse=True)
    def runner(self) -> CliRunner:
        return CliRunner()

    def test_main_04_no_args_shows_help(self, runner: CliRunner) -> None:
        """引数なしでヘルプが表示されること（exit_code は 0 または 2 を許容）"""
        from iso8583_manager.__main__ import app
        result = runner.invoke(app, [])
        assert result.exit_code in (0, 2)
        assert "cli" in result.output
        assert "api" in result.output
        assert "web" in result.output

    def test_main_05_help_flag_shows_subcommands(self, runner: CliRunner) -> None:
        """--help でサブコマンド一覧が表示されること"""
        from iso8583_manager.__main__ import app
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "cli" in result.output
        assert "api" in result.output
        assert "web" in result.output

    def test_main_06_cli_subcommand_shows_help(self, runner: CliRunner) -> None:
        """cli --help で既存 CLI コマンドが表示されること"""
        from iso8583_manager.__main__ import app
        result = runner.invoke(app, ["cli", "--help"])
        assert result.exit_code == 0
        assert "generate" in result.output
        assert "parse" in result.output

    def test_main_07_api_subcommand_accepts_host_port(self, runner: CliRunner) -> None:
        """api --help で --host / --port オプションが表示されること"""
        from iso8583_manager.__main__ import app
        result = runner.invoke(app, ["api", "--help"])
        assert result.exit_code == 0
        assert "--host" in result.output
        assert "--port" in result.output

    def test_main_08_web_subcommand_accepts_host_port(self, runner: CliRunner) -> None:
        """web --help で --host / --port オプションが表示されること"""
        from iso8583_manager.__main__ import app
        result = runner.invoke(app, ["web", "--help"])
        assert result.exit_code == 0
        assert "--host" in result.output
        assert "--port" in result.output

    def test_main_09_api_missing_dep_shows_helpful_error(
        self, runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """fastapi 未インストール時に有用なエラーメッセージが表示されること"""
        import builtins
        real_import = builtins.__import__

        def mock_import(name: str, *args, **kwargs):  # type: ignore[no-untyped-def]
            if name == "uvicorn":
                raise ImportError("uvicorn not installed")
            return real_import(name, *args, **kwargs)

        from iso8583_manager.__main__ import app
        monkeypatch.setattr(builtins, "__import__", mock_import)
        result = runner.invoke(app, ["api"])
        assert result.exit_code != 0
        assert "iso8583_manager[api]" in result.output
