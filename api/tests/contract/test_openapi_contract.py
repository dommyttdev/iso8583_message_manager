"""
OpenAPI 契約テスト。

shared/openapi/iso8583-api.yaml が:
1. 有効な OpenAPI 3.x スペックである
2. api/ の実際のエンドポイントと一致している
"""
from pathlib import Path

import pytest

SHARED_OPENAPI = Path(__file__).parent.parent.parent.parent / "shared" / "openapi" / "iso8583-api.yaml"


class TestOpenApiContractFileExists:
    def test_shared_openapi_yaml_exists(self):
        """shared/openapi/iso8583-api.yaml が存在すること。"""
        assert SHARED_OPENAPI.exists(), f"契約ファイルが見つかりません: {SHARED_OPENAPI}"

    def test_shared_openapi_yaml_is_not_empty(self):
        content = SHARED_OPENAPI.read_text(encoding="utf-8")
        assert len(content) > 0


class TestOpenApiContractValidity:
    def test_openapi_spec_is_valid(self):
        """OpenAPI スペックが有効な形式であること。"""
        pytest.importorskip("openapi_spec_validator", reason="openapi-spec-validator が必要")
        import yaml
        from openapi_spec_validator import validate

        content = SHARED_OPENAPI.read_text(encoding="utf-8")
        spec = yaml.safe_load(content)
        validate(spec)  # 例外が出なければ合格

    def test_openapi_has_required_endpoints(self):
        """必須エンドポイントが定義されていること。"""
        pytest.importorskip("yaml", reason="PyYAML が必要")
        import yaml

        content = SHARED_OPENAPI.read_text(encoding="utf-8")
        spec = yaml.safe_load(content)
        paths = spec.get("paths", {})

        assert "/api/v1/health" in paths
        assert "/api/v1/messages/generate" in paths
        assert "/api/v1/messages/parse" in paths

    def test_openapi_matches_api_routes(self):
        """api/ の実ルートと shared/openapi/iso8583-api.yaml のパスが一致すること。"""
        pytest.importorskip("yaml", reason="PyYAML が必要")
        import yaml
        from fastapi.testclient import TestClient
        from iso8583_api.app import app

        content = SHARED_OPENAPI.read_text(encoding="utf-8")
        spec = yaml.safe_load(content)
        spec_paths = set(spec.get("paths", {}).keys())

        client = TestClient(app)
        openapi_response = client.get("/openapi.json")
        assert openapi_response.status_code == 200
        actual_paths = set(openapi_response.json().get("paths", {}).keys())

        assert spec_paths == actual_paths, (
            f"スペックと実装のパスが一致しません\n"
            f"  スペックのみ: {spec_paths - actual_paths}\n"
            f"  実装のみ: {actual_paths - spec_paths}"
        )
