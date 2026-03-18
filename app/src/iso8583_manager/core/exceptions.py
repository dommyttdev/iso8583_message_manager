"""
ISO 8583 マネージャー共通の例外定義。
"""

class Iso8583Error(Exception):
    """ISO 8583 マネージャーの基底例外クラス。"""
    pass

class SpecError(Iso8583Error):
    """スペックファイルの読み込みや形式に関するエラー。"""
    pass

class MessageEncodeError(Iso8583Error):
    """メッセージのエンコード処理中に発生したエラー。"""
    pass

class MessageDecodeError(Iso8583Error):
    """メッセージのデコード処理中に発生したエラー。"""
    pass

class InvalidMtiError(Iso8583Error, ValueError):
    """MTI の値が不正な場合のエラー。ValueError を継承して後方互換性を維持。"""
    pass
