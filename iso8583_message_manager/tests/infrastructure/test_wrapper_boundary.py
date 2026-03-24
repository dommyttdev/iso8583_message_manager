"""
PyIso8583Adapter の境界値テスト。

テスト戦略 doc/test_strategy.md §4.3 INF-BV-01〜07 に対応。
"""
from importlib.resources import files as _pkg_files

import pytest

from iso8583_types.core.models.generated.iso_models import Iso8583MessageModel
from iso8583_types.core.models.mti import Mti
from iso8583_manager.infrastructure.pyiso8583_adapter.wrapper import PyIso8583Adapter

_SPEC_PATH = str(_pkg_files("iso8583_manager.data.schemas") / "iso8583_fields.json")


@pytest.fixture(scope="module")
def adapter() -> PyIso8583Adapter:
    return PyIso8583Adapter(spec_json_path=_SPEC_PATH)


@pytest.fixture
def mti_0200() -> Mti:
    return Mti.from_str("0200")


class TestPyIso8583AdapterBoundaryValues:
    def test_inf_bv_01_pan_min_length(
        self, adapter: PyIso8583Adapter, mti_0200: Mti
    ) -> None:
        """INF-BV-01: PAN 1桁（最小）のエンコード→デコード往復（可変長最小値）。"""
        model = Iso8583MessageModel(primary_account_number="1")
        raw = adapter.generate(mti_0200, model)
        _mti_str, decoded = adapter.parse(bytes(raw), Iso8583MessageModel)
        assert decoded.primary_account_number == "1"

    def test_inf_bv_02_pan_max_length(
        self, adapter: PyIso8583Adapter, mti_0200: Mti
    ) -> None:
        """INF-BV-02: PAN 19桁（最大）のエンコード→デコード往復（可変長最大値）。"""
        model = Iso8583MessageModel(primary_account_number="1234567890123456789")
        raw = adapter.generate(mti_0200, model)
        _mti_str, decoded = adapter.parse(bytes(raw), Iso8583MessageModel)
        assert decoded.primary_account_number == "1234567890123456789"

    def test_inf_bv_03_amount_fixed_length(
        self, adapter: PyIso8583Adapter, mti_0200: Mti
    ) -> None:
        """INF-BV-03: amount_transaction 12桁（固定長ちょうど）のエンコード。"""
        model = Iso8583MessageModel(amount_transaction="123456789012")
        raw = adapter.generate(mti_0200, model)
        assert isinstance(raw, bytearray)
        assert len(raw) > 0

    def test_inf_bv_04_single_field(
        self, adapter: PyIso8583Adapter, mti_0200: Mti
    ) -> None:
        """INF-BV-04: 1 フィールドのみ指定（他は None）のエンコード→デコード（疎なメッセージ）。"""
        model = Iso8583MessageModel(systems_trace_audit_number="000001")
        raw = adapter.generate(mti_0200, model)
        _mti_str, decoded = adapter.parse(bytes(raw), Iso8583MessageModel)
        assert decoded.systems_trace_audit_number == "000001"
        assert decoded.primary_account_number is None

    def test_inf_bv_05_all_none_fields(
        self, adapter: PyIso8583Adapter, mti_0200: Mti
    ) -> None:
        """INF-BV-05: 全フィールド None のエンコード（MTI のみの最小メッセージ）。"""
        model = Iso8583MessageModel()
        raw = adapter.generate(mti_0200, model)
        assert isinstance(raw, bytearray)
        mti_str, _decoded = adapter.parse(bytes(raw), Iso8583MessageModel)
        assert mti_str == "0200"

    def test_inf_bv_06_all_fields_roundtrip(
        self, adapter: PyIso8583Adapter, mti_0200: Mti
    ) -> None:
        """INF-BV-06: 全フィールド指定のエンコード→デコード往復（密なメッセージ）。"""
        model = Iso8583MessageModel(
            primary_account_number="4111111111111111",
            processing_code="000000",
            amount_transaction="000000010000",
            transmission_date_and_time="0319120000",
            systems_trace_audit_number="000001",
            response_code="00",
        )
        raw = adapter.generate(mti_0200, model)
        _mti_str, decoded = adapter.parse(bytes(raw), Iso8583MessageModel)
        assert decoded.primary_account_number == "4111111111111111"
        assert decoded.processing_code == "000000"
        assert decoded.amount_transaction == "000000010000"
        assert decoded.transmission_date_and_time == "0319120000"
        assert decoded.systems_trace_audit_number == "000001"
        assert decoded.response_code == "00"

    def test_inf_bv_07_response_code_alphanumeric(
        self, adapter: PyIso8583Adapter, mti_0200: Mti
    ) -> None:
        """INF-BV-07: response_code が an 型（英数混在）のエンコード（データ型検証）。"""
        model = Iso8583MessageModel(response_code="AB")
        raw = adapter.generate(mti_0200, model)
        assert isinstance(raw, bytearray)
        _mti_str, decoded = adapter.parse(bytes(raw), Iso8583MessageModel)
        assert decoded.response_code == "AB"
