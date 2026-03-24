"""
iso8583_types.models.mti のユニットテスト。

既存の iso8583_message_manager テストをベースに
新パッケージのインポートパスへ移行。
"""
import dataclasses
import pytest
from iso8583_types.models.mti import (
    Mti,
    MtiClass,
    MtiFunction,
    MtiOrigin,
    MtiVersion,
)
from iso8583_types.exceptions import InvalidMtiError


class TestMtiVersionEnum:
    def test_v1987_digit_is_0(self):
        assert MtiVersion.V1987.value == 0

    def test_v1993_digit_is_1(self):
        assert MtiVersion.V1993.value == 1

    def test_v2003_digit_is_2(self):
        assert MtiVersion.V2003.value == 2

    def test_private_digit_is_9(self):
        assert MtiVersion.PRIVATE.value == 9


class TestMtiClassEnum:
    def test_authorization_digit_is_1(self):
        assert MtiClass.AUTHORIZATION.value == 1

    def test_financial_digit_is_2(self):
        assert MtiClass.FINANCIAL.value == 2

    def test_reversal_digit_is_4(self):
        assert MtiClass.REVERSAL.value == 4

    def test_network_management_digit_is_8(self):
        assert MtiClass.NETWORK_MANAGEMENT.value == 8


class TestMtiConstruction:
    def test_to_str_authorization_request(self):
        mti = Mti(
            version=MtiVersion.V1987,
            cls=MtiClass.AUTHORIZATION,
            function=MtiFunction.REQUEST,
            origin=MtiOrigin.ACQUIRER,
        )
        assert mti.to_str() == "0100"

    def test_to_str_financial_request(self):
        mti = Mti(
            version=MtiVersion.V1987,
            cls=MtiClass.FINANCIAL,
            function=MtiFunction.REQUEST,
            origin=MtiOrigin.ACQUIRER,
        )
        assert mti.to_str() == "0200"


KNOWN_MTI_CASES = [
    ("0100", MtiVersion.V1987, MtiClass.AUTHORIZATION,      MtiFunction.REQUEST,  MtiOrigin.ACQUIRER),
    ("0200", MtiVersion.V1987, MtiClass.FINANCIAL,          MtiFunction.REQUEST,  MtiOrigin.ACQUIRER),
    ("0210", MtiVersion.V1987, MtiClass.FINANCIAL,          MtiFunction.RESPONSE, MtiOrigin.ACQUIRER),
    ("0400", MtiVersion.V1987, MtiClass.REVERSAL,           MtiFunction.REQUEST,  MtiOrigin.ACQUIRER),
    ("0800", MtiVersion.V1987, MtiClass.NETWORK_MANAGEMENT, MtiFunction.REQUEST,  MtiOrigin.ACQUIRER),
    ("0810", MtiVersion.V1987, MtiClass.NETWORK_MANAGEMENT, MtiFunction.RESPONSE, MtiOrigin.ACQUIRER),
]


class TestMtiFromStr:
    @pytest.mark.parametrize(
        "mti_str, expected_version, expected_cls, expected_function, expected_origin",
        KNOWN_MTI_CASES,
    )
    def test_from_str_parses_known_mti(
        self, mti_str, expected_version, expected_cls, expected_function, expected_origin
    ):
        mti = Mti.from_str(mti_str)
        assert mti.version == expected_version
        assert mti.cls == expected_cls
        assert mti.function == expected_function
        assert mti.origin == expected_origin

    @pytest.mark.parametrize("mti_str", [c[0] for c in KNOWN_MTI_CASES])
    def test_round_trip(self, mti_str: str):
        assert Mti.from_str(mti_str).to_str() == mti_str


class TestMtiValueObjectProperties:
    def test_equal_instances_are_equal(self):
        assert Mti.from_str("0100") == Mti.from_str("0100")

    def test_hashable(self):
        mti = Mti.from_str("0100")
        assert {mti: "ok"}[mti] == "ok"

    def test_immutable_raises_on_assignment(self):
        mti = Mti.from_str("0100")
        with pytest.raises((dataclasses.FrozenInstanceError, AttributeError)):
            mti.version = MtiVersion.V1993  # type: ignore[misc]


class TestMtiFromStrValidation:
    def test_empty_string_raises(self):
        with pytest.raises(InvalidMtiError):
            Mti.from_str("")

    def test_too_short_raises(self):
        with pytest.raises(InvalidMtiError):
            Mti.from_str("200")

    def test_non_digit_raises(self):
        with pytest.raises(InvalidMtiError):
            Mti.from_str("AAAA")

    def test_undefined_class_zero_raises(self):
        with pytest.raises(InvalidMtiError):
            Mti.from_str("0000")

    def test_undefined_version_raises(self):
        """1桁目（バージョン）が未定義の場合に InvalidMtiError が発生すること"""
        with pytest.raises(InvalidMtiError):
            Mti.from_str("3100")  # バージョン 3 は未定義

    def test_undefined_function_raises(self):
        """3桁目（機能）が未定義の場合に InvalidMtiError が発生すること"""
        with pytest.raises(InvalidMtiError):
            Mti.from_str("0150")  # 機能 5 は未定義

    def test_undefined_origin_raises(self):
        """4桁目（発生源）が未定義の場合に InvalidMtiError が発生すること"""
        with pytest.raises(InvalidMtiError):
            Mti.from_str("0106")  # 発生源 6 は未定義


class TestMtiVersionDescription:
    @pytest.mark.parametrize("member,expected", [
        (MtiVersion.V1987,   "ISO 8583-1:1987年版"),
        (MtiVersion.V1993,   "ISO 8583-2:1993年版"),
        (MtiVersion.V2003,   "ISO 8583-1:2003年版"),
        (MtiVersion.PRIVATE, "個社使用"),
    ])
    def test_description_returns_expected(self, member: MtiVersion, expected: str):
        assert member.description == expected


class TestMtiClassDescription:
    @pytest.mark.parametrize("member,expected", [
        (MtiClass.AUTHORIZATION,      "オーソリゼーション"),
        (MtiClass.FINANCIAL,          "ファイナンシャル"),
        (MtiClass.FILE_UPDATE,        "ファイル更新"),
        (MtiClass.REVERSAL,           "取消"),
        (MtiClass.RECONCILIATION,     "交換"),
        (MtiClass.ADMINISTRATIVE,     "管理"),
        (MtiClass.FEE,                "課金"),
        (MtiClass.NETWORK_MANAGEMENT, "ネットワーク管理"),
    ])
    def test_description_returns_expected(self, member: MtiClass, expected: str):
        assert member.description == expected


class TestMtiFunctionDescription:
    @pytest.mark.parametrize("member,expected", [
        (MtiFunction.REQUEST,         "要求"),
        (MtiFunction.RESPONSE,        "要求に対する応答"),
        (MtiFunction.ADVICE,          "アドバイス"),
        (MtiFunction.ADVICE_RESPONSE, "アドバイスに対する応答"),
        (MtiFunction.NOTIFICATION,    "通知"),
        (MtiFunction.RESPONSE_ACK,    "応答の認証"),
        (MtiFunction.NEGATIVE_ACK,    "ネガティブな認証"),
    ])
    def test_description_returns_expected(self, member: MtiFunction, expected: str):
        assert member.description == expected


class TestMtiOriginDescription:
    @pytest.mark.parametrize("member,expected", [
        (MtiOrigin.ACQUIRER,        "アクワイアラ"),
        (MtiOrigin.ACQUIRER_REPEAT, "アクワイアラ（リピート）"),
        (MtiOrigin.ISSUER,          "イシュア"),
        (MtiOrigin.ISSUER_REPEAT,   "イシュア（リピート）"),
        (MtiOrigin.OTHER,           "その他"),
        (MtiOrigin.OTHER_REPEAT,    "その他（リピート）"),
    ])
    def test_description_returns_expected(self, member: MtiOrigin, expected: str):
        assert member.description == expected
