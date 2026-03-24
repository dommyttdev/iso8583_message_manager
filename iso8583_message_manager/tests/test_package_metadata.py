"""
pyproject.toml のパッケージメタデータ検証テスト。

依存関係の分割が正しく定義されていることを検証する。
"""
import importlib.metadata


class TestPackageMetadata:
    def test_pm_01_package_name(self) -> None:
        """パッケージ名が iso8583_manager であること"""
        meta = importlib.metadata.metadata("iso8583_manager")
        assert meta["Name"] == "iso8583_manager"

    def test_pm_02_entry_point_is_unified(self) -> None:
        """エントリポイントが iso8583-msg 単一であること"""
        eps = importlib.metadata.entry_points(group="console_scripts")
        names = [ep.name for ep in eps if ep.value.startswith("iso8583_manager")]
        assert "iso8583-msg" in names, "iso8583-msg エントリポイントが未登録"
        assert "iso8583-msg-cli" not in names, "旧エントリポイント iso8583-msg-cli が残存"

    def test_pm_03_api_optional_dep_defined(self) -> None:
        """[api] optional-dependencies が定義されていること"""
        meta = importlib.metadata.metadata("iso8583_manager")
        requires = meta.get_all("Requires-Dist") or []
        # api extra には fastapi が含まれること
        api_deps = [r for r in requires if "extra == 'api'" in r]
        assert any("fastapi" in d for d in api_deps), \
            f"[api] に fastapi が含まれない: {api_deps}"

    def test_pm_04_web_optional_dep_defined(self) -> None:
        """[web] optional-dependencies が定義されていること"""
        meta = importlib.metadata.metadata("iso8583_manager")
        requires = meta.get_all("Requires-Dist") or []
        web_deps = [r for r in requires if "extra == 'web'" in r]
        assert any("fastapi" in d for d in web_deps), \
            f"[web] に fastapi が含まれない: {web_deps}"

    def test_pm_05_fastapi_not_in_core_deps(self) -> None:
        """fastapi / uvicorn がコア必須依存に含まれないこと"""
        meta = importlib.metadata.metadata("iso8583_manager")
        requires = meta.get_all("Requires-Dist") or []
        # extra 条件なしの依存のみ抽出
        core_deps = [r for r in requires if "; extra ==" not in r and "extra ==" not in r]
        assert not any("fastapi" in d for d in core_deps), \
            f"fastapi がコア依存に含まれている: {core_deps}"
        assert not any("uvicorn" in d for d in core_deps), \
            f"uvicorn がコア依存に含まれている: {core_deps}"
