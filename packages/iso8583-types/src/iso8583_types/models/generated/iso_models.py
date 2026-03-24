"""
このファイルは scripts/code_generator/generate_models.py により自動生成されます。
直接編集しないでください。iso8583_fields.json を編集して再生成してください。
"""

from pydantic import BaseModel, ConfigDict, Field
from typing import Any, ClassVar, Dict, Optional

from iso8583_types.interfaces.iso_ports import IIso8583Model


class Iso8583MessageModel(BaseModel):
    """ISO 8583 データエレメントの自動生成 Pydantic モデル。"""

    model_config = ConfigDict(extra="forbid")

    primary_account_number: Optional[str] = Field(default=None, description="Primary Account Number (PAN)", min_length=1, max_length=19)
    processing_code: Optional[str] = Field(default=None, description="Processing Code", min_length=6, max_length=6)
    amount_transaction: Optional[str] = Field(default=None, description="Amount, Transaction", min_length=12, max_length=12)
    transmission_date_and_time: Optional[str] = Field(default=None, description="Transmission Date and Time", min_length=10, max_length=10)
    systems_trace_audit_number: Optional[str] = Field(default=None, description="Systems Trace Audit Number", min_length=6, max_length=6)
    response_code: Optional[str] = Field(default=None, description="Response Code", min_length=2, max_length=2)

    # プロパティ名 → ISO フィールド番号のマッピング
    field_mapping: ClassVar[Dict[str, str]] = {
        "primary_account_number": "2",
        "processing_code": "3",
        "amount_transaction": "4",
        "transmission_date_and_time": "7",
        "systems_trace_audit_number": "11",
        "response_code": "39",
    }

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
