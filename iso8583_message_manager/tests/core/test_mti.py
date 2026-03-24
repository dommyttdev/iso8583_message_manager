"""
ISO 8583 MTI (Message Type Identifier) モデルのユニットテスト。

TDD Red Phase: すべてのテストが最初は失敗することを確認するために作成。
"""
import dataclasses
import pytest
from iso8583_manager.core.models.mti import (
    Mti,
    MtiClass,
    MtiFunction,
    MtiOrigin,
    MtiVersion,
)
from iso8583_manager.core.exceptions import InvalidMtiError


# ==============================================================================
# ① Enum 個別値テスト
#    仕様書 iso8583_specs.md に記載された digit 値と一致することを保証する。
# ==============================================================================

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

    def test_file_update_digit_is_3(self):
        assert MtiClass.FILE_UPDATE.value == 3

    def test_reversal_digit_is_4(self):
        assert MtiClass.REVERSAL.value == 4

    def test_reconciliation_digit_is_5(self):
        assert MtiClass.RECONCILIATION.value == 5

    def test_administrative_digit_is_6(self):
        assert MtiClass.ADMINISTRATIVE.value == 6

    def test_fee_digit_is_7(self):
        assert MtiClass.FEE.value == 7

    def test_network_management_digit_is_8(self):
        assert MtiClass.NETWORK_MANAGEMENT.value == 8


class TestMtiFunctionEnum:
    def test_request_digit_is_0(self):
        assert MtiFunction.REQUEST.value == 0

    def test_response_digit_is_1(self):
        assert MtiFunction.RESPONSE.value == 1

    def test_advice_digit_is_2(self):
        assert MtiFunction.ADVICE.value == 2

    def test_advice_response_digit_is_3(self):
        assert MtiFunction.ADVICE_RESPONSE.value == 3

    def test_notification_digit_is_4(self):
        assert MtiFunction.NOTIFICATION.value == 4

    def test_response_ack_digit_is_8(self):
        assert MtiFunction.RESPONSE_ACK.value == 8

    def test_negative_ack_digit_is_9(self):
        assert MtiFunction.NEGATIVE_ACK.value == 9


class TestMtiOriginEnum:
    def test_acquirer_digit_is_0(self):
        assert MtiOrigin.ACQUIRER.value == 0

    def test_acquirer_repeat_digit_is_1(self):
        assert MtiOrigin.ACQUIRER_REPEAT.value == 1

    def test_issuer_digit_is_2(self):
        assert MtiOrigin.ISSUER.value == 2

    def test_issuer_repeat_digit_is_3(self):
        assert MtiOrigin.ISSUER_REPEAT.value == 3

    def test_other_digit_is_4(self):
        assert MtiOrigin.OTHER.value == 4

    def test_other_repeat_digit_is_5(self):
        assert MtiOrigin.OTHER_REPEAT.value == 5


# ==============================================================================
# ② コンポーネントから組み立て → to_str()
#    コンストラクタで直接組み立て、to_str() が正しい4桁文字列を返すことを保証する。
# ==============================================================================

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

    def test_to_str_network_management_request(self):
        mti = Mti(
            version=MtiVersion.V1987,
            cls=MtiClass.NETWORK_MANAGEMENT,
            function=MtiFunction.REQUEST,
            origin=MtiOrigin.ACQUIRER,
        )
        assert mti.to_str() == "0800"

    def test_to_str_authorization_advice_repeat(self):
        mti = Mti(
            version=MtiVersion.V1987,
            cls=MtiClass.AUTHORIZATION,
            function=MtiFunction.ADVICE,
            origin=MtiOrigin.ACQUIRER_REPEAT,
        )
        assert mti.to_str() == "0121"


# ==============================================================================
# ③ from_str → プロパティ解析 → ラウンドトリップ
#    仕様書 iso8583_specs.md の「MTI一覧」に記載された全17値を網羅する。
# ==============================================================================

# from_str() の解析結果を (version, cls, function, origin) のタプルで期待値を定義
KNOWN_MTI_CASES = [
    ("0100", MtiVersion.V1987, MtiClass.AUTHORIZATION,      MtiFunction.REQUEST,         MtiOrigin.ACQUIRER),
    ("0110", MtiVersion.V1987, MtiClass.AUTHORIZATION,      MtiFunction.RESPONSE,        MtiOrigin.ACQUIRER),
    ("0120", MtiVersion.V1987, MtiClass.AUTHORIZATION,      MtiFunction.ADVICE,          MtiOrigin.ACQUIRER),
    ("0121", MtiVersion.V1987, MtiClass.AUTHORIZATION,      MtiFunction.ADVICE,          MtiOrigin.ACQUIRER_REPEAT),
    ("0130", MtiVersion.V1987, MtiClass.AUTHORIZATION,      MtiFunction.ADVICE_RESPONSE, MtiOrigin.ACQUIRER),
    ("0200", MtiVersion.V1987, MtiClass.FINANCIAL,          MtiFunction.REQUEST,         MtiOrigin.ACQUIRER),
    ("0210", MtiVersion.V1987, MtiClass.FINANCIAL,          MtiFunction.RESPONSE,        MtiOrigin.ACQUIRER),
    ("0220", MtiVersion.V1987, MtiClass.FINANCIAL,          MtiFunction.ADVICE,          MtiOrigin.ACQUIRER),
    ("0221", MtiVersion.V1987, MtiClass.FINANCIAL,          MtiFunction.ADVICE,          MtiOrigin.ACQUIRER_REPEAT),
    ("0230", MtiVersion.V1987, MtiClass.FINANCIAL,          MtiFunction.ADVICE_RESPONSE, MtiOrigin.ACQUIRER),
    ("0400", MtiVersion.V1987, MtiClass.REVERSAL,           MtiFunction.REQUEST,         MtiOrigin.ACQUIRER),
    ("0420", MtiVersion.V1987, MtiClass.REVERSAL,           MtiFunction.ADVICE,          MtiOrigin.ACQUIRER),
    ("0421", MtiVersion.V1987, MtiClass.REVERSAL,           MtiFunction.ADVICE,          MtiOrigin.ACQUIRER_REPEAT),
    ("0430", MtiVersion.V1987, MtiClass.REVERSAL,           MtiFunction.ADVICE_RESPONSE, MtiOrigin.ACQUIRER),
    ("0800", MtiVersion.V1987, MtiClass.NETWORK_MANAGEMENT, MtiFunction.REQUEST,         MtiOrigin.ACQUIRER),
    ("0810", MtiVersion.V1987, MtiClass.NETWORK_MANAGEMENT, MtiFunction.RESPONSE,        MtiOrigin.ACQUIRER),
    ("0820", MtiVersion.V1987, MtiClass.NETWORK_MANAGEMENT, MtiFunction.ADVICE,          MtiOrigin.ACQUIRER),
]


class TestMtiFromStr:
    @pytest.mark.parametrize(
        "mti_str, expected_version, expected_cls, expected_function, expected_origin",
        KNOWN_MTI_CASES,
    )
    def test_from_str_parses_known_mti(
        self,
        mti_str,
        expected_version,
        expected_cls,
        expected_function,
        expected_origin,
    ):
        mti = Mti.from_str(mti_str)
        assert mti.version == expected_version
        assert mti.cls == expected_cls
        assert mti.function == expected_function
        assert mti.origin == expected_origin

    @pytest.mark.parametrize("mti_str", [case[0] for case in KNOWN_MTI_CASES])
    def test_round_trip(self, mti_str: str):
        """from_str() してから to_str() すると元の文字列に戻る。"""
        assert Mti.from_str(mti_str).to_str() == mti_str


# ==============================================================================
# ④ Value Object 特性テスト（frozen dataclass としての振る舞い）
# ==============================================================================

class TestMtiValueObjectProperties:
    def test_equal_instances_are_equal(self):
        assert Mti.from_str("0100") == Mti.from_str("0100")

    def test_different_instances_are_not_equal(self):
        assert Mti.from_str("0100") != Mti.from_str("0200")

    def test_hashable_for_use_as_dict_key(self):
        mti = Mti.from_str("0100")
        d = {mti: "authorization_request"}
        assert d[mti] == "authorization_request"

    def test_immutable_raises_on_assignment(self):
        mti = Mti.from_str("0100")
        with pytest.raises((dataclasses.FrozenInstanceError, AttributeError)):
            mti.version = MtiVersion.V1993  # type: ignore[misc]


# ==============================================================================
# ⑤ from_str バリデーション（異常系）
# ==============================================================================

class TestMtiFromStrValidation:
    def test_empty_string_raises_value_error(self):
        with pytest.raises(InvalidMtiError):
            Mti.from_str("")

    def test_too_short_raises_value_error(self):
        with pytest.raises(InvalidMtiError):
            Mti.from_str("200")

    def test_too_long_raises_value_error(self):
        with pytest.raises(InvalidMtiError):
            Mti.from_str("00200")

    def test_non_digit_all_raises_value_error(self):
        with pytest.raises(InvalidMtiError):
            Mti.from_str("AAAA")

    def test_non_digit_first_char_raises_value_error(self):
        with pytest.raises(InvalidMtiError):
            Mti.from_str("A100")

    def test_non_digit_second_char_raises_value_error(self):
        with pytest.raises(InvalidMtiError):
            Mti.from_str("0A00")

    def test_undefined_class_digit_zero_raises_value_error(self):
        """MtiClass=0 は仕様上未定義。"""
        with pytest.raises(InvalidMtiError):
            Mti.from_str("0000")

    def test_undefined_version_digit_raises_invalid_mti_error(self):
        """MtiVersion=3 は仕様上未定義。"""
        with pytest.raises(InvalidMtiError):
            Mti.from_str("3100")

    def test_undefined_function_digit_raises_invalid_mti_error(self):
        """MTI 3桁目（機能）の未定義値。"""
        with pytest.raises(InvalidMtiError) as excinfo:
            Mti.from_str("0150")  # 5 is undefined for MtiFunction
        assert "MTI 3桁目（機能）" in str(excinfo.value)

    def test_undefined_origin_digit_raises_invalid_mti_error(self):
        """MTI 4桁目（発生源）の未定義値。"""
        with pytest.raises(InvalidMtiError) as excinfo:
            Mti.from_str("0106")  # 6 is undefined for MtiOrigin
        assert "MTI 4桁目（発生源）" in str(excinfo.value)


# ==============================================================================
# ⑥ description プロパティテスト
#    各 Enum メンバーが日本語の説明文字列を返すことを保証する。
# ==============================================================================

class TestMtiVersionDescription:
    def test_all_members_have_description(self):
        """全 MtiVersion メンバーが非空の description を持つ。"""
        for member in MtiVersion:
            assert isinstance(member.description, str)
            assert len(member.description) > 0

    def test_description_count_matches_member_count(self):
        """description の数がメンバー数と一致する。"""
        descriptions = {member.description for member in MtiVersion}
        assert len(descriptions) == len(MtiVersion)

    def test_v1987_description_is_str(self):
        """V1987 の description が str 型。"""
        assert isinstance(MtiVersion.V1987.description, str)


class TestMtiClassDescription:
    def test_all_members_have_description(self):
        """全 MtiClass メンバーが非空の description を持つ。"""
        for member in MtiClass:
            assert isinstance(member.description, str)
            assert len(member.description) > 0

    def test_description_count_matches_member_count(self):
        """description の数がメンバー数と一致する。"""
        descriptions = {member.description for member in MtiClass}
        assert len(descriptions) == len(MtiClass)


class TestMtiFunctionDescription:
    def test_all_members_have_description(self):
        """全 MtiFunction メンバーが非空の description を持つ。"""
        for member in MtiFunction:
            assert isinstance(member.description, str)
            assert len(member.description) > 0

    def test_description_count_matches_member_count(self):
        """description の数がメンバー数と一致する。"""
        descriptions = {member.description for member in MtiFunction}
        assert len(descriptions) == len(MtiFunction)


class TestMtiOriginDescription:
    def test_all_members_have_description(self):
        """全 MtiOrigin メンバーが非空の description を持つ。"""
        for member in MtiOrigin:
            assert isinstance(member.description, str)
            assert len(member.description) > 0

    def test_description_count_matches_member_count(self):
        """description の数がメンバー数と一致する。"""
        descriptions = {member.description for member in MtiOrigin}
        assert len(descriptions) == len(MtiOrigin)
