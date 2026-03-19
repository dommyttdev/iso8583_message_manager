"""
メッセージルーター。

POST /api/v1/messages/generate — ISO 8583 メッセージ生成（エンコード）
POST /api/v1/messages/parse    — ISO 8583 メッセージ解析（デコード）
"""
import base64
import binascii
import logging

from fastapi import APIRouter, Depends

from iso8583_manager.core.models.generated.iso_models import Iso8583MessageModel
from iso8583_manager.core.models.mti import Mti
from iso8583_manager.presentation.api.schemas.generate import (
    GenerateRequest,
    GenerateResponse,
)
from iso8583_manager.presentation.api.schemas.parse import ParseRequest, ParseResponse
from iso8583_manager.presentation.container import (
    build_generate_use_case,
    build_parse_use_case,
)
from iso8583_manager.use_cases.message_generation import GenerateMessageUseCase
from iso8583_manager.use_cases.message_parsing import ParseMessageUseCase

logger = logging.getLogger(__name__)
router = APIRouter(tags=["messages"])


def get_generate_use_case() -> GenerateMessageUseCase:
    """GenerateMessageUseCase の DI プロバイダー。"""
    return build_generate_use_case()


def get_parse_use_case() -> ParseMessageUseCase:
    """ParseMessageUseCase の DI プロバイダー。"""
    return build_parse_use_case()


@router.post(
    "/api/v1/messages/generate",
    response_model=GenerateResponse,
    operation_id="generate_message",
)
def generate_message(
    request: GenerateRequest,
    use_case: GenerateMessageUseCase = Depends(get_generate_use_case),
) -> GenerateResponse:
    """MTI とフィールド値から ISO 8583 バイナリメッセージを生成します。"""
    logger.info("POST /api/v1/messages/generate MTI=%s", request.mti)

    # InvalidMtiError が発生した場合は error_handler が 400 に変換する
    mti = Mti.from_str(request.mti)

    # MessageEncodeError が発生した場合は error_handler が 400 に変換する
    raw: bytearray = use_case.execute(mti, request.fields)

    if request.output_format == "hex":
        encoded = raw.hex()
    else:
        encoded = base64.b64encode(raw).decode("ascii")

    return GenerateResponse(
        mti=mti.to_str(),
        encoded_message=encoded,
        output_format=request.output_format,
        byte_length=len(raw),
    )


@router.post(
    "/api/v1/messages/parse",
    response_model=ParseResponse,
    operation_id="parse_message",
)
def parse_message(
    request: ParseRequest,
    use_case: ParseMessageUseCase = Depends(get_parse_use_case),
) -> ParseResponse:
    """ISO 8583 バイナリメッセージを解析して MTI とフィールド値を返します。"""
    logger.info("POST /api/v1/messages/parse format=%s", request.input_format)

    # フォーマット変換エラー → ValueError → error_handler が 400 INVALID_FORMAT に変換
    try:
        if request.input_format == "hex":
            raw = bytes.fromhex(request.encoded_message)
        else:
            raw = base64.b64decode(request.encoded_message, validate=True)
    except (ValueError, binascii.Error) as exc:
        raise ValueError(
            f"入力フォーマット '{request.input_format}' として解釈できませんでした: {exc}"
        ) from exc

    # MessageDecodeError が発生した場合は error_handler が 400 に変換する
    mti, model = use_case.execute(raw, Iso8583MessageModel)

    fields_dict = {
        k: v
        for k, v in model.model_dump(exclude_none=True).items()
        if v is not None
    }

    return ParseResponse(
        mti=mti.to_str(),
        mti_description={
            "version": mti.version.description,
            "class": mti.cls.description,
            "function": mti.function.description,
            "origin": mti.origin.description,
        },
        fields=fields_dict,
    )
