"""
ISO 8583 メッセージ解析エンドポイントのリクエスト/レスポンス スキーマ。
"""
from typing import Dict, Literal

from pydantic import BaseModel, Field


class ParseRequest(BaseModel):
    """POST /api/v1/messages/parse のリクエストボディ。"""

    encoded_message: str = Field(
        ...,
        description="エンコードされた ISO 8583 メッセージ（hex または base64 文字列）",
    )
    input_format: Literal["hex", "base64"] = Field(
        default="hex",
        description="入力メッセージのフォーマット。",
    )


class ParseResponse(BaseModel):
    """POST /api/v1/messages/parse のレスポンスボディ。"""

    mti: str = Field(description="解析された MTI（4桁文字列）")
    mti_description: Dict[str, str] = Field(
        description="MTI の各コンポーネント説明（version / class / function / origin）"
    )
    fields: Dict[str, str] = Field(
        description="デコードされたフィールドの値マップ（プロパティ名→値）"
    )
