"""
FastAPI アプリケーション定義。

Presentation 層の API エントリポイント。
クリーンアーキテクチャの依存方向を維持し、
Use Case 層以外には依存しない。
"""
import logging

from fastapi import FastAPI

from iso8583_types.core.exceptions import (
    Iso8583Error,
    InvalidMtiError,
    MessageDecodeError,
    MessageEncodeError,
    SpecError,
)
from iso8583_api.error_handler import (
    invalid_mti_handler,
    iso8583_error_handler,
    message_decode_error_handler,
    message_encode_error_handler,
    spec_error_handler,
    value_error_handler,
)
from iso8583_api.routers import health, messages, metadata

logger = logging.getLogger(__name__)

app = FastAPI(
    title="ISO 8583 Message Generator API",
    description=(
        "ISO 8583 財務トランザクションメッセージの生成・解析を行う REST API。\n"
        "カード決済プロトコルの標準規格である ISO 8583 のメッセージを HTTP 経由で\n"
        "エンコード・デコードできます。"
    ),
    version="1.0.0",
)

# --- ルーター登録 ---
app.include_router(health.router)
app.include_router(metadata.router)
app.include_router(messages.router)

# --- 例外ハンドラー登録（MRO に従い具体的な例外を先に登録）---
# InvalidMtiError は Iso8583Error と ValueError の両方を継承するため最初に登録する
app.add_exception_handler(InvalidMtiError, invalid_mti_handler)  # type: ignore[arg-type]
app.add_exception_handler(MessageEncodeError, message_encode_error_handler)  # type: ignore[arg-type]
app.add_exception_handler(MessageDecodeError, message_decode_error_handler)  # type: ignore[arg-type]
app.add_exception_handler(SpecError, spec_error_handler)  # type: ignore[arg-type]
app.add_exception_handler(Iso8583Error, iso8583_error_handler)  # type: ignore[arg-type]
app.add_exception_handler(ValueError, value_error_handler)  # type: ignore[arg-type]

logger.info("ISO 8583 Message Generator API を起動しました。")
