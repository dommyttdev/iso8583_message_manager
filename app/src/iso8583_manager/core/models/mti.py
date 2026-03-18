"""
ISO 8583 MTI (Message Type Identifier) の Value Object モデル。

MTI は4桁の数値フィールドで構成され、各桁に以下の意味を持つ:
  1桁目: ISO 8583のバージョン
  2桁目: メッセージクラス
  3桁目: メッセージ機能
  4桁目: メッセージ発生源

参照: doc/domain/iso8583/iso8583_specs.md
"""
from __future__ import annotations

import dataclasses
from enum import IntEnum


class MtiVersion(IntEnum):
    """
    MTI 1桁目: ISO 8583 のバージョン。

    仕様書「ISO 8583の版」セクション参照。
    """
    V1987   = 0  # ISO 8583-1:1987年版
    V1993   = 1  # ISO 8583-2:1993年版
    V2003   = 2  # ISO 8583-1:2003年版
    PRIVATE = 9  # 個社使用


class MtiClass(IntEnum):
    """
    MTI 2桁目: メッセージクラス（全体的な目的）。

    仕様書「メッセージクラス」セクション参照。
    """
    AUTHORIZATION      = 1  # オーソリ
    FINANCIAL          = 2  # ファイナンシャル
    FILE_UPDATE        = 3  # ファイル更新
    REVERSAL           = 4  # 取消
    RECONCILIATION     = 5  # 交換
    ADMINISTRATIVE     = 6  # 管理
    FEE                = 7  # 課金
    NETWORK_MANAGEMENT = 8  # ネットワーク管理


class MtiFunction(IntEnum):
    """
    MTI 3桁目: メッセージ機能（保証範囲の指定）。

    仕様書「メッセージ機能」セクション参照。
    """
    REQUEST         = 0  # 要求
    RESPONSE        = 1  # 要求に対する応答
    ADVICE          = 2  # アドバイス
    ADVICE_RESPONSE = 3  # アドバイスに対する応答
    NOTIFICATION    = 4  # 通知
    RESPONSE_ACK    = 8  # 応答の認証
    NEGATIVE_ACK    = 9  # ネガティブな認証


class MtiOrigin(IntEnum):
    """
    MTI 4桁目: メッセージ発生源。

    仕様書「メッセージ発生源」セクション参照。
    """
    ACQUIRER        = 0  # アクワイアラ
    ACQUIRER_REPEAT = 1  # アクワイアラ（リピート）
    ISSUER          = 2  # イシュア
    ISSUER_REPEAT   = 3  # イシュア（リピート）
    OTHER           = 4  # その他
    OTHER_REPEAT    = 5  # その他（リピート）


@dataclasses.dataclass(frozen=True)
class Mti:
    """
    ISO 8583 MTI の Value Object。

    4桁のMTIを Enum コンポーネントで表現し、不変・等価比較・ハッシュ可能。

    Example:
        >>> mti = Mti.from_str("0200")
        >>> mti.cls
        <MtiClass.FINANCIAL: 2>
        >>> mti.to_str()
        '0200'
    """
    version:  MtiVersion
    cls:      MtiClass
    function: MtiFunction
    origin:   MtiOrigin

    def to_str(self) -> str:
        """4桁の MTI 文字列を生成する。"""
        return (
            f"{self.version.value}"
            f"{self.cls.value}"
            f"{self.function.value}"
            f"{self.origin.value}"
        )

    @classmethod
    def from_str(cls, mti_str: str) -> "Mti":
        """
        4桁の MTI 文字列から Mti インスタンスを生成する。

        Args:
            mti_str: 4桁の数字文字列（例: "0200"）

        Returns:
            Mti インスタンス

        Raises:
            ValueError: 文字列が4桁の数字でない場合、またはいずれかの桁が未定義の場合
        """
        if len(mti_str) != 4:
            raise ValueError(
                f"MTI は4桁の数字文字列でなければなりません。受信値: '{mti_str}'"
            )
        if not mti_str.isdigit():
            raise ValueError(
                f"MTI は数字のみで構成されなければなりません。受信値: '{mti_str}'"
            )

        version_digit, class_digit, function_digit, origin_digit = (
            int(d) for d in mti_str
        )

        try:
            version = MtiVersion(version_digit)
        except ValueError:
            raise ValueError(
                f"MTI 1桁目（バージョン）の値 '{version_digit}' は定義されていません。"
            )

        try:
            mti_class = MtiClass(class_digit)
        except ValueError:
            raise ValueError(
                f"MTI 2桁目（クラス）の値 '{class_digit}' は定義されていません。"
            )

        try:
            function = MtiFunction(function_digit)
        except ValueError:
            raise ValueError(
                f"MTI 3桁目（機能）の値 '{function_digit}' は定義されていません。"
            )

        try:
            origin = MtiOrigin(origin_digit)
        except ValueError:
            raise ValueError(
                f"MTI 4桁目（発生源）の値 '{origin_digit}' は定義されていません。"
            )

        return cls(version=version, cls=mti_class, function=function, origin=origin)
