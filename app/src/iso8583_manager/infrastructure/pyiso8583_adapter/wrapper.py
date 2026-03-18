from typing import Type
import copy
import json
import iso8583
from iso8583.specs import default_ascii
from iso8583_manager.core.interfaces.iso_ports import IMessageGenerator, IIso8583Model
from iso8583_manager.core.models.mti import Mti

class PyIso8583Adapter(IMessageGenerator):
    def __init__(self, spec_json_path: str):
        self.spec_json_path = spec_json_path
        self.spec = self._build_spec()

    def _build_spec(self) -> dict:
        """iso8583_fields.jsonからpyiso8583対応のspecを構築する"""
        with open(self.spec_json_path, 'r', encoding='utf-8') as f:
            fields = json.load(f)
            
        spec = copy.deepcopy(default_ascii)
        
        for field_id, meta in fields.items():
            spec[field_id] = {
                'data_enc': meta.get('data_enc', 'ascii'),
                'len_enc': meta.get('len_enc', 'ascii'),
                'len_type': meta.get('len_type', 0),
                'max_len': meta.get('max_len', 999),
            }
            
        return spec

    def generate(self, mti: Mti, model_data: IIso8583Model) -> bytearray:
        decoded = {'t': mti.to_str()}
        # モデルから辞書に変換されたデータエレメントを取得・マージ
        decoded.update(model_data.to_iso_dict())

        # pyiso8583でバイト列にエンコード
        encoded_raw, _ = iso8583.encode(decoded, self.spec)
        return encoded_raw

    def parse(self, raw_message: bytes, model_cls: Type[IIso8583Model]) -> IIso8583Model:
        # pyiso8583でバイト列から辞書にパース
        decoded, _ = iso8583.decode(raw_message, self.spec)
        
        # 不要な 't', 'p' などは from_iso_dict 側で対応付けがなければスキップされる
        return model_cls.from_iso_dict(decoded)
