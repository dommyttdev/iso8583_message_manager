"""
Iso8583MessageModel の境界値テスト。

Pydantic の Field(min_length, max_length) バリデーションが
各フィールドの極値（最小・最大・超過）で正しく機能することを検証する。
"""
import pytest
from pydantic import ValidationError

from iso8583_types.models.generated.iso_models import Iso8583MessageModel


# ==============================================================================
# primary_account_number (可変長: min=1, max=19)
# ==============================================================================

class TestPanBoundary:
    def test_bv_pan_01_min_length_accepted(self) -> None:
        """PAN 最小長 1 桁が受け入れられること"""
        model = Iso8583MessageModel(primary_account_number="1")
        assert model.primary_account_number == "1"

    def test_bv_pan_02_max_length_accepted(self) -> None:
        """PAN 最大長 19 桁が受け入れられること"""
        model = Iso8583MessageModel(primary_account_number="1234567890123456789")
        assert model.primary_account_number == "1234567890123456789"

    def test_bv_pan_03_empty_string_rejected(self) -> None:
        """PAN 空文字列（長さ 0）が拒否されること"""
        with pytest.raises(ValidationError):
            Iso8583MessageModel(primary_account_number="")

    def test_bv_pan_04_over_max_length_rejected(self) -> None:
        """PAN 20 桁（最大超過）が拒否されること"""
        with pytest.raises(ValidationError):
            Iso8583MessageModel(primary_account_number="12345678901234567890")

    def test_bv_pan_05_none_accepted(self) -> None:
        """PAN None（未設定）が受け入れられること（Optional フィールド）"""
        model = Iso8583MessageModel(primary_account_number=None)
        assert model.primary_account_number is None

    @pytest.mark.parametrize("length", [1, 10, 16, 19])
    def test_bv_pan_06_valid_lengths(self, length: int) -> None:
        """PAN の有効な長さ範囲が全て受け入れられること"""
        value = "1" * length
        model = Iso8583MessageModel(primary_account_number=value)
        assert model.primary_account_number == value


# ==============================================================================
# processing_code (固定長: min=max=6)
# ==============================================================================

class TestProcessingCodeBoundary:
    def test_bv_pc_01_exact_length_accepted(self) -> None:
        """processing_code 正確に 6 桁が受け入れられること"""
        model = Iso8583MessageModel(processing_code="123456")
        assert model.processing_code == "123456"

    def test_bv_pc_02_too_short_rejected(self) -> None:
        """processing_code 5 桁（最小未満）が拒否されること"""
        with pytest.raises(ValidationError):
            Iso8583MessageModel(processing_code="12345")

    def test_bv_pc_03_too_long_rejected(self) -> None:
        """processing_code 7 桁（最大超過）が拒否されること"""
        with pytest.raises(ValidationError):
            Iso8583MessageModel(processing_code="1234567")

    def test_bv_pc_04_empty_string_rejected(self) -> None:
        """processing_code 空文字列が拒否されること"""
        with pytest.raises(ValidationError):
            Iso8583MessageModel(processing_code="")


# ==============================================================================
# amount_transaction (固定長: min=max=12)
# ==============================================================================

class TestAmountTransactionBoundary:
    def test_bv_at_01_exact_length_accepted(self) -> None:
        """amount_transaction 正確に 12 桁が受け入れられること"""
        model = Iso8583MessageModel(amount_transaction="000000001000")
        assert model.amount_transaction == "000000001000"

    def test_bv_at_02_too_short_rejected(self) -> None:
        """amount_transaction 11 桁が拒否されること"""
        with pytest.raises(ValidationError):
            Iso8583MessageModel(amount_transaction="00000000100")

    def test_bv_at_03_too_long_rejected(self) -> None:
        """amount_transaction 13 桁が拒否されること"""
        with pytest.raises(ValidationError):
            Iso8583MessageModel(amount_transaction="0000000010000")

    def test_bv_at_04_zeros_accepted(self) -> None:
        """amount_transaction ゼロ値（000000000000）が受け入れられること"""
        model = Iso8583MessageModel(amount_transaction="000000000000")
        assert model.amount_transaction == "000000000000"

    def test_bv_at_05_max_value_accepted(self) -> None:
        """amount_transaction 最大値（999999999999）が受け入れられること"""
        model = Iso8583MessageModel(amount_transaction="999999999999")
        assert model.amount_transaction == "999999999999"


# ==============================================================================
# transmission_date_and_time (固定長: min=max=10)
# ==============================================================================

class TestTransmissionDateTimeBoundary:
    def test_bv_tdt_01_exact_length_accepted(self) -> None:
        """transmission_date_and_time 正確に 10 桁が受け入れられること"""
        model = Iso8583MessageModel(transmission_date_and_time="0319120000")
        assert model.transmission_date_and_time == "0319120000"

    def test_bv_tdt_02_too_short_rejected(self) -> None:
        """transmission_date_and_time 9 桁が拒否されること"""
        with pytest.raises(ValidationError):
            Iso8583MessageModel(transmission_date_and_time="031912000")

    def test_bv_tdt_03_too_long_rejected(self) -> None:
        """transmission_date_and_time 11 桁が拒否されること"""
        with pytest.raises(ValidationError):
            Iso8583MessageModel(transmission_date_and_time="03191200001")


# ==============================================================================
# systems_trace_audit_number (固定長: min=max=6)
# ==============================================================================

class TestSystemsTraceAuditNumberBoundary:
    def test_bv_stan_01_exact_length_accepted(self) -> None:
        """systems_trace_audit_number 正確に 6 桁が受け入れられること"""
        model = Iso8583MessageModel(systems_trace_audit_number="111222")
        assert model.systems_trace_audit_number == "111222"

    def test_bv_stan_02_leading_zeros_accepted(self) -> None:
        """systems_trace_audit_number 先頭ゼロ（000001）が受け入れられること"""
        model = Iso8583MessageModel(systems_trace_audit_number="000001")
        assert model.systems_trace_audit_number == "000001"

    def test_bv_stan_03_too_short_rejected(self) -> None:
        """systems_trace_audit_number 5 桁が拒否されること"""
        with pytest.raises(ValidationError):
            Iso8583MessageModel(systems_trace_audit_number="11122")

    def test_bv_stan_04_too_long_rejected(self) -> None:
        """systems_trace_audit_number 7 桁が拒否されること"""
        with pytest.raises(ValidationError):
            Iso8583MessageModel(systems_trace_audit_number="1112222")


# ==============================================================================
# response_code (固定長: min=max=2)
# ==============================================================================

class TestResponseCodeBoundary:
    def test_bv_rc_01_exact_length_accepted(self) -> None:
        """response_code 正確に 2 桁が受け入れられること"""
        model = Iso8583MessageModel(response_code="00")
        assert model.response_code == "00"

    def test_bv_rc_02_alphanumeric_accepted(self) -> None:
        """response_code 英数混在（AB）が受け入れられること（an 型）"""
        model = Iso8583MessageModel(response_code="AB")
        assert model.response_code == "AB"

    def test_bv_rc_03_too_short_rejected(self) -> None:
        """response_code 1 桁が拒否されること"""
        with pytest.raises(ValidationError):
            Iso8583MessageModel(response_code="0")

    def test_bv_rc_04_too_long_rejected(self) -> None:
        """response_code 3 桁が拒否されること"""
        with pytest.raises(ValidationError):
            Iso8583MessageModel(response_code="000")

    def test_bv_rc_05_empty_string_rejected(self) -> None:
        """response_code 空文字列が拒否されること"""
        with pytest.raises(ValidationError):
            Iso8583MessageModel(response_code="")

    @pytest.mark.parametrize("code", ["00", "05", "51", "14", "96", "ZZ", "AB"])
    def test_bv_rc_06_common_response_codes_accepted(self, code: str) -> None:
        """よく使われる 2 桁レスポンスコードが全て受け入れられること"""
        model = Iso8583MessageModel(response_code=code)
        assert model.response_code == code


# ==============================================================================
# extra フィールド禁止（model_config extra="forbid"）
# ==============================================================================

class TestExtraFieldsRejected:
    def test_bv_extra_01_unknown_field_rejected(self) -> None:
        """未定義フィールドが拒否されること（extra='forbid'）"""
        with pytest.raises(ValidationError):
            Iso8583MessageModel(unknown_field="value")  # type: ignore[call-arg]

    def test_bv_extra_02_all_none_accepted(self) -> None:
        """全フィールド未指定（全 None）が受け入れられること"""
        model = Iso8583MessageModel()
        assert model.primary_account_number is None
        assert model.processing_code is None
        assert model.amount_transaction is None
