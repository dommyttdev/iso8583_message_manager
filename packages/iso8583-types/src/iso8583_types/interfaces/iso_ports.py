from typing import Protocol, Any, Dict, Type
from iso8583_types.models.mti import Mti

class IIso8583Model(Protocol):
    """
    ISO8583メッセージモデルが満たすべきインターフェース。
    エンコーダーが必要とする情報を提供できる構造を強制する。
    """
    
    def to_iso_dict(self) -> Dict[str, Any]:
        """
        pyiso8583 が要求する 'フィールドID (str)' -> '値 (str/bytes)' 形式の辞書を返す。
        """
        ...
    
    @classmethod
    def from_iso_dict(cls, data: Dict[str, Any]) -> "IIso8583Model":
        """
        pyiso8583 がパースした辞書データから、モデルのインスタンスを生成する。
        """
        ...

class IMessageGenerator(Protocol):
    """
    ISO8583メッセージジェネレータ（パーサー）のインターフェース。
    外部ライブラリ（pyiso8583等）に直接依存せずに扱うためのポート。
    """
    
    def generate(self, mti: Mti, model_data: IIso8583Model) -> bytearray:
        """
        モデルデータからISO8583バイナリを生成する。

        Args:
            mti: メッセージタイプID（Value Object）
            model_data: データエレメントを保持するモデル
        """
        ...
        
    def parse(self, raw_message: bytes, model_cls: Type[IIso8583Model]) -> tuple[str, IIso8583Model]:
        """
        ISO8583バイナリをパースし、MTI文字列とモデルインスタンスのタプルを返す。

        Returns:
            (mti_str, model): MTI の4桁文字列と、指定されたモデルのインスタンス。
            mti_str から Mti への変換は呼び出し側（ユースケース）が Mti.from_str() で行う。
        """
        ...
