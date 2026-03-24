"""
generate_openapi.py のユニットテスト。

テスト戦略 doc/test_strategy.md §4.1 GEN-OA-01〜11 に対応。
"""
import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

APP_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(APP_DIR / "src"))

# generate_openapi モジュールを scripts パッケージ外から直接インポート
_SCRIPTS_DIR = APP_DIR / "scripts" / "code_generator"
sys.path.insert(0, str(_SCRIPTS_DIR))
import generate_openapi as gen_mod  # noqa: E402
from generate_openapi import (  # noqa: E402
    _build_property,
    build_fields_example,
    build_message_fields_schema,
    build_mti_types_example,
    generate_openapi,
)

ROOT_DIR = APP_DIR.parent  # d:/Projects/Cards/
_CORE_SCHEMAS = ROOT_DIR / "packages" / "iso8583-core" / "src" / "iso8583_core" / "data" / "schemas"
_FIELDS_JSON = _CORE_SCHEMAS / "iso8583_fields.json"
_BASE_YAML = _CORE_SCHEMAS / "openapi_base.yaml"


@pytest.fixture(scope="module")
def fields() -> dict:
    with open(_FIELDS_JSON, encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# GEN-OA-01〜05: build_message_fields_schema()
# ---------------------------------------------------------------------------


class TestBuildMessageFieldsSchema:
    def test_gen_oa_01_all_field_names_present(self, fields: dict) -> None:
        """GEN-OA-01: 標準 JSON から MessageFields 生成 → properties に全フィールド名が存在。"""
        schema = build_message_fields_schema(fields)
        for _field_id, meta in fields.items():
            assert meta["name"] in schema["properties"], (
                f"プロパティ '{meta['name']}' が schema['properties'] に存在しない"
            )

    def test_gen_oa_02_variable_field_constraints(self, fields: dict) -> None:
        """GEN-OA-02: 可変長フィールド（len_type=2）の制約: minLength=1, maxLength=N, pattern。"""
        schema = build_message_fields_schema(fields)
        # primary_account_number: len_type=2, data_type=n, max_len=19
        prop = schema["properties"]["primary_account_number"]
        assert prop["minLength"] == 1
        assert prop["maxLength"] == 19
        assert prop["pattern"] == "^[0-9]{1,19}$"

    def test_gen_oa_03_fixed_field_constraints(self, fields: dict) -> None:
        """GEN-OA-03: 固定長フィールド（len_type=0）の制約: minLength == maxLength。"""
        schema = build_message_fields_schema(fields)
        # processing_code: len_type=0, data_type=n, max_len=6
        prop = schema["properties"]["processing_code"]
        assert prop["minLength"] == prop["maxLength"]
        assert prop["minLength"] == 6
        assert prop["pattern"] == "^[0-9]{6}$"

    def test_gen_oa_04_additional_properties_false(self, fields: dict) -> None:
        """GEN-OA-04: additionalProperties: false が生成される（未定義フィールド名を拒否）。"""
        schema = build_message_fields_schema(fields)
        assert schema.get("additionalProperties") is False

    def test_gen_oa_05_ans_field_no_pattern(self) -> None:
        """GEN-OA-05: ans 型フィールドに pattern が生成されない（文字セットが広すぎるため）。"""
        synthetic_fields = {
            "99": {
                "name": "card_holder_name",
                "description": "Cardholder Name",
                "data_type": "ans",
                "len_type": 0,
                "max_len": 26,
            }
        }
        schema = build_message_fields_schema(synthetic_fields)
        prop = schema["properties"]["card_holder_name"]
        assert "pattern" not in prop


# ---------------------------------------------------------------------------
# GEN-OA-06: build_fields_example()
# ---------------------------------------------------------------------------


class TestBuildFieldsExample:
    def test_gen_oa_06_all_fields_in_example(self, fields: dict) -> None:
        """GEN-OA-06: FieldsExample が JSON の全フィールドを含む（フィールド数と ID が一致）。"""
        example = build_fields_example(fields)
        assert "fields" in example
        field_ids_in_example = {item["field_id"] for item in example["fields"]}
        assert field_ids_in_example == set(fields.keys())


# ---------------------------------------------------------------------------
# GEN-OA-07〜08: build_mti_types_example()
# ---------------------------------------------------------------------------


class TestBuildMtiTypesExample:
    def test_gen_oa_07_enum_counts(self) -> None:
        """GEN-OA-07: MtiTypesExample が mti.py の全 enum を含む（各グループの件数）。"""
        example = build_mti_types_example()
        assert len(example["versions"]) == 4    # V1987, V1993, V2003, PRIVATE
        assert len(example["classes"]) == 8
        assert len(example["functions"]) == 7
        assert len(example["origins"]) == 6

    def test_gen_oa_08_description_matches_enum(self) -> None:
        """GEN-OA-08: MtiTypesExample の description が mti.py の .description と一致。"""
        from iso8583_types.core.models.mti import (
            MtiClass,
            MtiFunction,
            MtiOrigin,
            MtiVersion,
        )

        example = build_mti_types_example()
        for entry, member in zip(example["versions"], MtiVersion):
            assert entry["description"] == member.description
        for entry, member in zip(example["classes"], MtiClass):
            assert entry["description"] == member.description
        for entry, member in zip(example["functions"], MtiFunction):
            assert entry["description"] == member.description
        for entry, member in zip(example["origins"], MtiOrigin):
            assert entry["description"] == member.description


# ---------------------------------------------------------------------------
# GEN-OA-09〜11: generate_openapi() 統合テスト
# ---------------------------------------------------------------------------


class TestGenerateOpenapiIntegration:
    def test_gen_oa_09_new_field_reflected(self, fields: dict) -> None:
        """GEN-OA-09: フィールドを追加して再生成 → properties に反映（単一真実の連携検証）。"""
        extra_fields = dict(fields)
        extra_fields["99"] = {
            "name": "test_extra_field",
            "description": "Test Extra Field",
            "data_type": "n",
            "len_type": 0,
            "max_len": 4,
        }
        schema = build_message_fields_schema(extra_fields)
        assert "test_extra_field" in schema["properties"]
        assert len(schema["properties"]) == len(extra_fields)

    def test_gen_oa_10_missing_base_yaml_exits(self, tmp_path: Path) -> None:
        """GEN-OA-10: openapi_base.yaml が存在しない場合 → sys.exit(1)。"""
        with (
            patch.object(gen_mod, "FIELDS_JSON", _FIELDS_JSON),
            patch.object(gen_mod, "BASE_YAML", tmp_path / "nonexistent.yaml"),
            pytest.raises(SystemExit) as exc_info,
        ):
            generate_openapi()
        assert exc_info.value.code == 1

    def test_gen_oa_11_generated_yaml_is_valid_openapi(self, tmp_path: Path) -> None:
        """GEN-OA-11: 生成された openapi.yaml が有効な OpenAPI 3.1.0 スキーマ。"""
        pytest.importorskip("openapi_spec_validator", reason="openapi-spec-validator が必要")
        from openapi_spec_validator import validate

        output_yaml = tmp_path / "openapi.yaml"
        with (
            patch.object(gen_mod, "FIELDS_JSON", _FIELDS_JSON),
            patch.object(gen_mod, "BASE_YAML", _BASE_YAML),
            patch.object(gen_mod, "OUTPUT_YAML", output_yaml),
        ):
            generate_openapi()

        import yaml

        with open(output_yaml, encoding="utf-8") as f:
            spec = yaml.safe_load(f)
        validate(spec)  # 有効でなければ例外を送出する
