import json
import sys
from pathlib import Path

# Paths
ROOT_DIR = Path(__file__).parent.parent.parent
SCHEMAS_DIR = ROOT_DIR / "data" / "schemas"
GENERATED_DIR = ROOT_DIR / "src" / "iso8583_manager" / "core" / "models" / "generated"

JSON_FILE = SCHEMAS_DIR / "iso8583_fields.json"
MODELS_FILE = GENERATED_DIR / "iso_models.py"


def generate_models() -> None:
    """
    iso8583_fields.json を読み込み、Pydantic モデルを iso_models.py に生成する。

    固定長フィールド (len_type=0): min_length == max_length == N
    可変長フィールド (len_type>0): min_length=1, max_length=N
    """
    if not JSON_FILE.exists():
        print(f"[ERROR] スキーマファイルが見つかりません: {JSON_FILE}", file=sys.stderr)
        sys.exit(1)

    with open(JSON_FILE, "r", encoding="utf-8") as f:
        fields: dict = json.load(f)

    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    (GENERATED_DIR / "__init__.py").touch(exist_ok=True)

    header = '''\
"""
このファイルは scripts/code_generator/generate_models.py により自動生成されます。
直接編集しないでください。iso8583_fields.json を編集して再生成してください。
"""

from pydantic import BaseModel, ConfigDict, Field
from typing import Any, ClassVar, Dict, Optional

from iso8583_manager.core.interfaces.iso_ports import IIso8583Model


class Iso8583MessageModel(BaseModel):
    """ISO 8583 データエレメントの自動生成 Pydantic モデル。"""

    model_config = ConfigDict(extra="forbid")

'''

    field_mapping_lines: list[str] = []

    field_defs: list[str] = []
    for field_id, metadata in sorted(fields.items(), key=lambda kv: int(kv[0])):
        prop_name: str = metadata["name"]
        desc: str = metadata.get("description", "")
        max_len: int = metadata["max_len"]
        len_type: int = metadata.get("len_type", 0)
        variable: bool = len_type > 0

        min_len = 1 if variable else max_len
        field_defs.append(
            f'    {prop_name}: Optional[str] = Field('
            f'default=None, description="{desc}", '
            f'min_length={min_len}, max_length={max_len})\n'
        )
        field_mapping_lines.append(f'        "{prop_name}": "{field_id}",\n')

    field_mapping_block = (
        "    # プロパティ名 → ISO フィールド番号のマッピング\n"
        "    field_mapping: ClassVar[Dict[str, str]] = {\n"
        + "".join(field_mapping_lines)
        + "    }\n\n"
    )

    methods = '''\
    def to_iso_dict(self) -> Dict[str, Any]:
        """設定済みフィールドを pyiso8583 用の {フィールド番号: 値} 辞書に変換する。"""
        result: Dict[str, Any] = {}
        dumped = self.model_dump(exclude_unset=True, exclude_none=True)
        for key, value in dumped.items():
            if key in self.field_mapping:
                iso_id = self.field_mapping[key]
                result[iso_id] = str(value)
        return result

    @classmethod
    def from_iso_dict(cls, data: Dict[str, Any]) -> "IIso8583Model":
        """pyiso8583 がデコードした辞書からモデルインスタンスを生成する。未知のキーは無視する。"""
        reverse_map = {v: k for k, v in cls.field_mapping.items()}
        kwargs: Dict[str, Any] = {}
        for k, v in data.items():
            if k in reverse_map:
                kwargs[reverse_map[k]] = v
        return cls(**kwargs)
'''

    with open(MODELS_FILE, "w", encoding="utf-8") as out:
        out.write(header)
        out.writelines(field_defs)
        out.write("\n")
        out.write(field_mapping_block)
        out.write(methods)

    print(f"[OK] モデルを生成しました: {MODELS_FILE}")
    print(f"     フィールド数: {len(fields)}")


if __name__ == "__main__":
    generate_models()
