"""
生成された openapi.yaml の OpenAPI 仕様準拠検証テスト。

テスト戦略 doc/test_strategy.md §4.4 OA-VAL-01〜05 に対応。
テスト実行前に openapi.yaml が存在しない場合は自動生成する。
"""
import json
import sys
from pathlib import Path

import pytest

APP_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(APP_DIR / "src"))
sys.path.insert(0, str(APP_DIR / "scripts" / "code_generator"))

_OUTPUT_YAML = APP_DIR / "src" / "iso8583_manager" / "data" / "schemas" / "generated" / "openapi.yaml"
_FIELDS_JSON = APP_DIR / "src" / "iso8583_manager" / "data" / "schemas" / "iso8583_fields.json"


@pytest.fixture(scope="module")
def openapi_spec() -> dict:
    """openapi.yaml を読み込む。存在しない場合は生成してから読み込む。"""
    pytest.importorskip("openapi_spec_validator", reason="openapi-spec-validator が必要")
    import yaml

    if not _OUTPUT_YAML.exists():
        import generate_openapi as gen_mod  # type: ignore[import]

        gen_mod.generate_openapi()

    with open(_OUTPUT_YAML, encoding="utf-8") as f:
        return yaml.safe_load(f)  # type: ignore[no-any-return]


@pytest.fixture(scope="module")
def fields() -> dict:
    with open(_FIELDS_JSON, encoding="utf-8") as f:
        return json.load(f)


class TestOpenApiValidity:
    def test_oa_val_01_valid_openapi_spec(self, openapi_spec: dict) -> None:
        """OA-VAL-01: 生成された openapi.yaml が有効な OpenAPI 3.1.0 スキーマ。"""
        from openapi_spec_validator import validate

        validate(openapi_spec)  # 有効でなければ例外を送出する

    def test_oa_val_02_all_refs_resolvable(self, openapi_spec: dict) -> None:
        """OA-VAL-02: 全 $ref 参照が解決可能（validate が包括的に検証）。"""
        from openapi_spec_validator import validate

        validate(openapi_spec)

    def test_oa_val_03_all_endpoints_have_operation_id(
        self, openapi_spec: dict
    ) -> None:
        """OA-VAL-03: 全エンドポイントに operationId が存在。"""
        http_methods = {"get", "post", "put", "patch", "delete", "head", "options"}
        for path, methods in openapi_spec.get("paths", {}).items():
            for method, operation in methods.items():
                if method in http_methods and isinstance(operation, dict):
                    assert "operationId" in operation, (
                        f"{method.upper()} {path} に operationId がありません"
                    )

    def test_oa_val_04_message_fields_has_additional_properties_false(
        self, openapi_spec: dict
    ) -> None:
        """OA-VAL-04: MessageFields に additionalProperties: false が存在。"""
        schemas = openapi_spec.get("components", {}).get("schemas", {})
        message_fields = schemas.get("MessageFields", {})
        assert message_fields.get("additionalProperties") is False

    def test_oa_val_05_message_fields_count_matches_json(
        self, openapi_spec: dict, fields: dict
    ) -> None:
        """OA-VAL-05: MessageFields.properties 数が JSON スキーマのフィールド数と一致。"""
        schemas = openapi_spec.get("components", {}).get("schemas", {})
        message_fields = schemas.get("MessageFields", {})
        properties = message_fields.get("properties", {})
        assert len(properties) == len(fields)
