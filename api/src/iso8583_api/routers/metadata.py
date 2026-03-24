"""
メタデータルーター。

GET /api/v1/fields    — 利用可能な ISO 8583 フィールド一覧
GET /api/v1/mti-types — MTI タイプ一覧
"""
import json
import logging
from typing import Any, Dict, List

from fastapi import APIRouter, Depends

from iso8583_types.core.models.mti import MtiClass, MtiFunction, MtiOrigin, MtiVersion
from iso8583_api.container import _resolve_spec_path

logger = logging.getLogger(__name__)
router = APIRouter(tags=["metadata"])


def _get_fields_data() -> Dict[str, Any]:
    """iso8583_fields.json からフィールドデータを読み込む。"""
    spec_path = _resolve_spec_path(None)
    with open(spec_path, encoding="utf-8") as f:
        return json.load(f)  # type: ignore[no-any-return]


@router.get(
    "/api/v1/fields",
    response_model=Dict[str, Any],
    operation_id="list_fields",
)
def list_fields(
    fields_data: Dict[str, Any] = Depends(_get_fields_data),
) -> Dict[str, List[Dict[str, Any]]]:
    """利用可能な ISO 8583 フィールドの一覧を返します。"""
    field_list = [
        {
            "field_id": field_id,
            "name": meta["name"],
            "description": meta["description"],
            "data_type": meta["data_type"],
            "len_type": "variable" if meta.get("len_type", 0) > 0 else "fixed",
            "max_len": meta["max_len"],
        }
        for field_id, meta in sorted(fields_data.items(), key=lambda kv: int(kv[0]))
    ]
    return {"fields": field_list}


@router.get(
    "/api/v1/mti-types",
    response_model=Dict[str, Any],
    operation_id="list_mti_types",
)
def list_mti_types() -> Dict[str, List[Dict[str, str]]]:
    """MTI を構成する 4 コンポーネントの選択肢と説明を返します。"""

    def enum_to_list(enum_cls: type) -> List[Dict[str, str]]:
        return [
            {"code": str(member.value), "description": member.description}  # type: ignore[attr-defined]
            for member in enum_cls  # type: ignore[attr-defined]
        ]

    return {
        "versions": enum_to_list(MtiVersion),
        "classes": enum_to_list(MtiClass),
        "functions": enum_to_list(MtiFunction),
        "origins": enum_to_list(MtiOrigin),
    }
