"""
ISO 8583 メッセージ生成エンドポイントのリクエスト/レスポンス スキーマ。
"""
from typing import Literal

from pydantic import BaseModel, Field

from iso8583_types.models.generated.iso_models import Iso8583MessageModel


class GenerateRequest(BaseModel):
    """POST /api/v1/messages/generate のリクエストボディ。"""

    mti: str = Field(
        ...,
        pattern=r"^[0-9]{4}$",
        description="MTI（Message Type Identifier）。4桁の数字文字列。例: '0200'",
        examples=["0200"],
    )
    fields: Iso8583MessageModel = Field(
        default_factory=Iso8583MessageModel,
        description="ISO 8583 フィールドの値マップ。キーはプロパティ名（スネークケース）。",
    )
    output_format: Literal["hex", "base64"] = Field(
        default="hex",
        description="エンコード済みメッセージの出力フォーマット。",
    )


class GenerateResponse(BaseModel):
    """POST /api/v1/messages/generate のレスポンスボディ。"""

    mti: str = Field(description="使用された MTI")
    encoded_message: str = Field(description="エンコードされたメッセージ（output_format に応じた形式）")
    output_format: Literal["hex", "base64"] = Field(description="出力フォーマット")
    byte_length: int = Field(description="エンコード後のバイト長")
