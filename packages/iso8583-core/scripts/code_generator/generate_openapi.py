"""
iso8583_fields.json および mti.py を読み込み、openapi.yaml の以下3セクションを自動生成する。

  1. components/schemas/MessageFields                               ← iso8583_fields.json
     - 明示的なプロパティ定義（data_type・len_type から minLength/maxLength/pattern を導出）
     - additionalProperties: false で未定義キーを拒否

  2. paths./api/v1/fields.get.responses.200.content.application/json.example
     - フィールド一覧の具体的なレスポンス例                          ← iso8583_fields.json

  3. paths./api/v1/mti-types.get.responses.200.content.application/json.example
     - MTI タイプ一覧の具体的なレスポンス例                          ← mti.py の enum

使い方:
    cd iso8583_message_manager
    python scripts/code_generator/generate_openapi.py

入力:  src/iso8583_manager/data/schemas/iso8583_fields.json   (フィールド定義)
       src/iso8583_manager/data/schemas/openapi_base.yaml    (手動管理のベース YAML)
       src/iso8583_manager/core/models/mti.py  (MTI enum 定義)
出力:  src/iso8583_manager/data/schemas/generated/openapi.yaml   (生成済み最終成果物)
"""

import json
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("PyYAML が見つかりません。`pip install pyyaml` を実行してください。", file=sys.stderr)
    sys.exit(1)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT_DIR = Path(__file__).parent.parent.parent.parent.parent  # d:/Projects/Cards/

# mti.py を直接インポートするため src/ をパスに追加（venv 不要）
sys.path.insert(0, str(ROOT_DIR / "packages" / "iso8583-types" / "src"))
from iso8583_types.core.models.mti import MtiVersion, MtiClass, MtiFunction, MtiOrigin  # noqa: E402
SCHEMAS_DIR = ROOT_DIR / "packages" / "iso8583-core" / "src" / "iso8583_core" / "data" / "schemas"
FIELDS_JSON = SCHEMAS_DIR / "iso8583_fields.json"
BASE_YAML = SCHEMAS_DIR / "openapi_base.yaml"
OUTPUT_YAML = SCHEMAS_DIR / "generated" / "openapi.yaml"
# api/web の契約として shared/openapi/ にも出力する
SHARED_OUTPUT_YAML = ROOT_DIR / "shared" / "openapi" / "iso8583-api.yaml"

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_DATA_TYPE_LABEL: dict[str, str] = {
    "n":   "数値 (numeric)",
    "a":   "アルファベット (alpha)",
    "an":  "英数字 (alphanumeric)",
    "ans": "英数字・特殊文字 (alphanumeric special)",
    "b":   "バイナリ (binary)",
}

_PLACEHOLDER = "x-auto-generated"


# ---------------------------------------------------------------------------
# Schema builders
# ---------------------------------------------------------------------------

def _is_variable(len_type: int) -> bool:
    """len_type > 0 は可変長（LVAR/LLVAR/LLLVAR）。"""
    return len_type > 0


def _build_property(field_id: str, meta: dict) -> dict:
    """フィールド1件分の OpenAPI property オブジェクトを生成する。"""
    max_len: int = meta["max_len"]
    len_type: int = meta.get("len_type", 0)
    data_type: str = meta["data_type"]
    description: str = meta["description"]
    variable = _is_variable(len_type)

    type_label = _DATA_TYPE_LABEL.get(data_type, data_type)
    len_label = "可変長" if variable else "固定長"

    prop: dict = {
        "type": "string",
        "description": (
            f"{description} "
            f"[フィールド {field_id}, {type_label}, {len_label}, 最大{max_len}桁]"
        ),
        "maxLength": max_len,
        "minLength": 1 if variable else max_len,
    }

    # data_type から正規表現パターンを導出（ans / b は文字セットが広いため省略）
    char_class: str | None = {
        "n":  "[0-9]",
        "a":  "[A-Za-z]",
        "an": "[A-Za-z0-9]",
    }.get(data_type)

    if char_class:
        quantifier = f"{{1,{max_len}}}" if variable else f"{{{max_len}}}"
        prop["pattern"] = f"^{char_class}{quantifier}$"

    return prop


def build_message_fields_schema(fields: dict) -> dict:
    """
    MessageFields OpenAPI スキーマを生成する。

    additionalProperties: false とすることで、iso8583_fields.json に定義されていない
    フィールド名をリクエスト時に拒否できる。
    """
    properties = {
        meta["name"]: _build_property(field_id, meta)
        for field_id, meta in sorted(fields.items(), key=lambda kv: int(kv[0]))
    }

    return {
        "type": "object",
        "description": (
            "ISO 8583 フィールドの値マップ。\n"
            "キーはフィールドのプロパティ名（スネークケース）、値は文字列。\n"
            "利用可能なキーは `GET /api/v1/fields` で確認できます。\n"
            "このスキーマは iso8583_fields.json から自動生成されます。"
        ),
        "additionalProperties": False,
        "properties": properties,
    }


def build_mti_types_example() -> dict:
    """
    GET /api/v1/mti-types レスポンスの example オブジェクトを mti.py の enum から生成する。

    mti.py を直接インポートすることで、enum の変更が自動的にここへ反映される。
    """
    def enum_to_list(enum_cls: type) -> list[dict]:
        return [
            {"code": str(member.value), "description": member.description}
            for member in enum_cls
        ]

    return {
        "versions":  enum_to_list(MtiVersion),
        "classes":   enum_to_list(MtiClass),
        "functions": enum_to_list(MtiFunction),
        "origins":   enum_to_list(MtiOrigin),
    }


def build_fields_example(fields: dict) -> dict:
    """
    GET /api/v1/fields レスポンスの example オブジェクトを生成する。
    """
    field_list = [
        {
            "field_id": field_id,
            "name": meta["name"],
            "description": meta["description"],
            "data_type": meta["data_type"],
            "len_type": "variable" if _is_variable(meta.get("len_type", 0)) else "fixed",
            "max_len": meta["max_len"],
        }
        for field_id, meta in sorted(fields.items(), key=lambda kv: int(kv[0]))
    ]
    return {"fields": field_list}


# ---------------------------------------------------------------------------
# YAML patching
# ---------------------------------------------------------------------------

def _find_and_replace_placeholder(node: object, generated: dict) -> None:
    """
    YAML ドキュメントツリーを再帰的に走査し、
    {_PLACEHOLDER: <説明>} というプレースホルダーを generated の値で置き換える。

    generated のキー: セクション識別子（"MessageFields" | "FieldsExample"）
    """
    if not isinstance(node, dict):
        return

    for key, value in list(node.items()):
        if isinstance(value, dict) and _PLACEHOLDER in value:
            section = value[_PLACEHOLDER]
            if section in generated:
                node[key] = generated[section]
        else:
            _find_and_replace_placeholder(value, generated)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def generate_openapi() -> None:
    for path, label in [(FIELDS_JSON, "フィールド JSON"), (BASE_YAML, "ベース YAML")]:
        if not path.exists():
            print(f"[ERROR] {label} が見つかりません: {path}", file=sys.stderr)
            sys.exit(1)

    with FIELDS_JSON.open(encoding="utf-8") as f:
        fields: dict = json.load(f)

    with BASE_YAML.open(encoding="utf-8") as f:
        spec: dict = yaml.safe_load(f)

    generated_sections = {
        "MessageFields":  build_message_fields_schema(fields),
        "FieldsExample":  build_fields_example(fields),
        "MtiTypesExample": build_mti_types_example(),
    }

    _find_and_replace_placeholder(spec, generated_sections)

    with OUTPUT_YAML.open("w", encoding="utf-8") as f:
        f.write(
            "# このファイルは generate_openapi.py により自動生成されます。\n"
            "# 直接編集せず、openapi_base.yaml を編集して再生成してください。\n"
            "#\n"
            "#   cd iso8583_message_manager\n"
            "#   python scripts/code_generator/generate_openapi.py\n\n"
        )
        yaml.dump(
            spec,
            f,
            allow_unicode=True,
            default_flow_style=False,
            sort_keys=False,
            indent=2,
            width=120,
        )

    # api/web の契約として shared/openapi/ にも同一内容を出力する
    SHARED_OUTPUT_YAML.parent.mkdir(parents=True, exist_ok=True)
    import shutil
    shutil.copy2(OUTPUT_YAML, SHARED_OUTPUT_YAML)
    print(f"[OK] 契約ファイルをコピーしました: {SHARED_OUTPUT_YAML}")

    mti_example = generated_sections["MtiTypesExample"]
    print(f"[OK] OpenAPI スキーマを生成しました: {OUTPUT_YAML}")
    print(f"     フィールド数: {len(fields)}")
    for field_id, meta in sorted(fields.items(), key=lambda kv: int(kv[0])):
        len_type = meta.get("len_type", 0)
        kind = "可変長" if _is_variable(len_type) else "固定長"
        print(f"       フィールド {field_id:>3}: {meta['name']} ({kind}, 最大{meta['max_len']}桁)")
    print(f"     MTI タイプ: versions={len(mti_example['versions'])}, "
          f"classes={len(mti_example['classes'])}, "
          f"functions={len(mti_example['functions'])}, "
          f"origins={len(mti_example['origins'])}")


if __name__ == "__main__":
    generate_openapi()
