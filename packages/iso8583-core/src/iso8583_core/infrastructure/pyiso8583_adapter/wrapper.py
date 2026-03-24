import copy
import json
import logging
from typing import Any, Type

import iso8583
from iso8583.specs import default_ascii

from iso8583_types.core.exceptions import MessageDecodeError, MessageEncodeError, SpecError
from iso8583_types.core.interfaces.iso_ports import IIso8583Model, IMessageGenerator
from iso8583_types.core.models.mti import Mti

logger = logging.getLogger(__name__)


class PyIso8583Adapter(IMessageGenerator):
    def __init__(self, spec_json_path: str):
        self.spec_json_path = spec_json_path
        self.spec = self._build_spec()
        logger.info("PyIso8583Adapter initialized with spec: %s", spec_json_path)

    def _build_spec(self) -> dict[str, Any]:
        """iso8583_fields.jsonからpyiso8583対応のspecを構築する"""
        try:
            with open(self.spec_json_path, "r", encoding="utf-8") as f:
                fields = json.load(f)
        except FileNotFoundError as e:
            logger.error("スペックファイルが見つかりません: %s", self.spec_json_path)
            raise SpecError(f"スペックファイルが見つかりません: {self.spec_json_path}") from e
        except json.JSONDecodeError as e:
            logger.error("スペックファイルの形式が正しくありません: %s", self.spec_json_path)
            raise SpecError(f"スペックファイルの形式が正しくありません: {self.spec_json_path}") from e

        spec = copy.deepcopy(default_ascii)

        for field_id, meta in fields.items():
            spec[field_id] = {
                "data_enc": meta.get("data_enc", "ascii"),
                "len_enc": meta.get("len_enc", "ascii"),
                "len_type": meta.get("len_type", 0),
                "max_len": meta.get("max_len", 999),
            }

        return spec

    def generate(self, mti: Mti, model_data: IIso8583Model) -> bytearray:
        mti_str = mti.to_str()
        logger.info("Generating ISO 8583 message for MTI: %s", mti_str)
        
        try:
            decoded = {"t": mti_str}
            # モデルから辞書に変換されたデータエレメントを取得・マージ
            iso_dict = model_data.to_iso_dict()
            decoded.update(iso_dict)
            logger.debug("ISO dict to encode: %s", decoded)

            # pyiso8583でバイト列にエンコード
            encoded_raw, _ = iso8583.encode(decoded, self.spec)
            logger.info("Successfully encoded ISO 8583 message (length: %d)", len(encoded_raw))
            return encoded_raw
        except Exception as e:
            logger.error("ISO 8583 メッセージのエンコードに失敗しました: %s", str(e), exc_info=True)
            raise MessageEncodeError(f"エンコードに失敗しました: {str(e)}") from e

    def parse(self, raw_message: bytes, model_cls: Type[IIso8583Model]) -> tuple[str, IIso8583Model]:
        logger.info("Parsing ISO 8583 message (length: %d)", len(raw_message))

        try:
            # pyiso8583でバイト列から辞書にパース
            decoded, _ = iso8583.decode(raw_message, self.spec)
            logger.debug("Decoded ISO dict: %s", decoded)

            mti_str: str = decoded.get("t", "")
            # 不要な 't', 'p' などは from_iso_dict 側で対応付けがなければスキップされる
            model = model_cls.from_iso_dict(decoded)
            logger.info("Successfully parsed ISO 8583 message into %s (MTI: %s)", model_cls.__name__, mti_str)
            return mti_str, model
        except Exception as e:
            logger.error("ISO 8583 メッセージのデコードに失敗しました: %s", str(e), exc_info=True)
            raise MessageDecodeError(f"デコードに失敗しました: {str(e)}") from e
