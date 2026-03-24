"""
GET /api/v1/fields, GET /api/v1/mti-types のルーターユニットテスト。

テスト戦略 doc/api/api_design.md §9.3 API-META-01〜05 に対応。
"""
import json
from importlib.resources import files as _pkg_files
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from iso8583_api.app import app
from iso8583_api.routers.metadata import _get_fields_data

_FIELDS_JSON = _pkg_files("iso8583_core.data.schemas") / "iso8583_fields.json"


@pytest.fixture(autouse=True)
def override_fields_dep() -> None:
    """テスト用に iso8583_fields.json の実データを返す依存をオーバーライド。"""
    with open(_FIELDS_JSON, encoding="utf-8") as f:
        real_fields = json.load(f)

    app.dependency_overrides[_get_fields_data] = lambda: real_fields
    yield
    app.dependency_overrides.clear()


client = TestClient(app)


class TestFieldsEndpoint:
    def test_api_meta_01_fields_returns_200(self) -> None:
        """API-META-01: GET /api/v1/fields → 200、フィールド数が JSON スキーマと一致。"""
        with open(_FIELDS_JSON, encoding="utf-8") as f:
            expected_count = len(json.load(f))

        response = client.get("/api/v1/fields")
        assert response.status_code == 200
        data = response.json()
        assert len(data["fields"]) == expected_count

    def test_api_meta_02_field_definition_schema(self) -> None:
        """API-META-02: 各フィールドが FieldDefinition スキーマに準拠。"""
        response = client.get("/api/v1/fields")
        assert response.status_code == 200
        required_keys = {"field_id", "name", "description", "data_type", "len_type", "max_len"}
        for field in response.json()["fields"]:
            assert required_keys.issubset(field.keys()), (
                f"フィールド {field.get('field_id')} に必須キーが不足: {required_keys - field.keys()}"
            )


class TestMtiTypesEndpoint:
    def test_api_meta_03_mti_types_returns_200_with_4_keys(self) -> None:
        """API-META-03: GET /api/v1/mti-types → 200、4 キー（versions/classes/functions/origins）存在。"""
        response = client.get("/api/v1/mti-types")
        assert response.status_code == 200
        data = response.json()
        assert "versions" in data
        assert "classes" in data
        assert "functions" in data
        assert "origins" in data

    def test_api_meta_04_mti_entry_schema(self) -> None:
        """API-META-04: 各エントリが MtiCodeEntry スキーマ（code, description）に準拠。"""
        response = client.get("/api/v1/mti-types")
        data = response.json()
        for group in ["versions", "classes", "functions", "origins"]:
            for entry in data[group]:
                assert "code" in entry, f"{group} のエントリに 'code' がありません"
                assert "description" in entry, f"{group} のエントリに 'description' がありません"

    def test_api_meta_05_versions_count_matches_enum(self) -> None:
        """API-META-05: versions の件数が MtiVersion enum 数と一致（mti.py との同期保証）。"""
        from iso8583_types.models.mti import MtiVersion

        response = client.get("/api/v1/mti-types")
        data = response.json()
        assert len(data["versions"]) == len(MtiVersion)
