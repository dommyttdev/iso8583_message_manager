"""
ISO 8583 ドメイン例外 → HTTP レスポンス変換ハンドラー。

登録順序は MRO（Method Resolution Order）に依存するため、
より具体的な例外を先に登録する。
"""
import logging

from fastapi import Request
from fastapi.responses import JSONResponse

from iso8583_types.core.exceptions import (
    Iso8583Error,
    InvalidMtiError,
    MessageDecodeError,
    MessageEncodeError,
    SpecError,
)

logger = logging.getLogger(__name__)


async def invalid_mti_handler(request: Request, exc: InvalidMtiError) -> JSONResponse:
    """InvalidMtiError → 400 INVALID_MTI。"""
    logger.warning("無効な MTI リクエスト: %s", exc)
    return JSONResponse(
        status_code=400,
        content={
            "error_code": "INVALID_MTI",
            "message": "無効な MTI です。",
            "detail": str(exc),
        },
    )


async def message_encode_error_handler(
    request: Request, exc: MessageEncodeError
) -> JSONResponse:
    """MessageEncodeError → 400 MESSAGE_ENCODE_ERROR。"""
    logger.error("メッセージエンコードエラー: %s", exc)
    return JSONResponse(
        status_code=400,
        content={
            "error_code": "MESSAGE_ENCODE_ERROR",
            "message": "メッセージのエンコードに失敗しました。",
            "detail": str(exc),
        },
    )


async def message_decode_error_handler(
    request: Request, exc: MessageDecodeError
) -> JSONResponse:
    """MessageDecodeError → 400 MESSAGE_DECODE_ERROR。"""
    logger.error("メッセージデコードエラー: %s", exc)
    return JSONResponse(
        status_code=400,
        content={
            "error_code": "MESSAGE_DECODE_ERROR",
            "message": "メッセージのデコードに失敗しました。",
            "detail": str(exc),
        },
    )


async def spec_error_handler(request: Request, exc: SpecError) -> JSONResponse:
    """SpecError → 500 SPEC_ERROR。"""
    logger.error("スペックファイルエラー: %s", exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error_code": "SPEC_ERROR",
            "message": "スペックファイルの処理中にエラーが発生しました。",
            "detail": str(exc),
        },
    )


async def iso8583_error_handler(request: Request, exc: Iso8583Error) -> JSONResponse:
    """その他の Iso8583Error → 500 INTERNAL_ERROR。"""
    logger.error("内部エラー: %s", exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error_code": "INTERNAL_ERROR",
            "message": "内部エラーが発生しました。",
            "detail": str(exc),
        },
    )


async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    """ValueError（フォーマット不正） → 400 INVALID_FORMAT。

    InvalidMtiError は ValueError も継承するが、MRO により先に登録した
    invalid_mti_handler が優先されるため、ここには純粋な ValueError のみが到達する。
    """
    logger.warning("フォーマットエラー: %s", exc)
    return JSONResponse(
        status_code=400,
        content={
            "error_code": "INVALID_FORMAT",
            "message": "入力フォーマットが不正です。",
            "detail": str(exc),
        },
    )
