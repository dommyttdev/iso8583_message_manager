"""
パフォーマンステスト (pytest-benchmark)。

ISO 8583 メッセージのエンコード・デコードスループットを計測する。
目標: 1,000 メッセージ/秒以上の処理能力。

NOTE: このテストは通常の pytest 実行には影響しない。
      ベンチマーク計測時のみ意味のある結果を得られる。
      CI では `--benchmark-disable` で実行されるため自動化と共存できる。
"""
from __future__ import annotations

from importlib.resources import files as _pkg_files
from typing import TYPE_CHECKING

import pytest

from iso8583_core.infrastructure.pyiso8583_adapter.wrapper import PyIso8583Adapter
from iso8583_core.use_cases.message_generation import GenerateMessageUseCase
from iso8583_types.models.generated.iso_models import Iso8583MessageModel
from iso8583_types.models.mti import Mti

if TYPE_CHECKING:
    from pytest_benchmark.fixture import BenchmarkFixture

_SPEC_PATH = str(_pkg_files("iso8583_core.data.schemas") / "iso8583_fields.json")


@pytest.fixture(scope="module")
def adapter() -> PyIso8583Adapter:
    return PyIso8583Adapter(spec_json_path=_SPEC_PATH)


@pytest.fixture(scope="module")
def use_case(adapter: PyIso8583Adapter) -> GenerateMessageUseCase:
    return GenerateMessageUseCase(message_generator=adapter)


@pytest.fixture(scope="module")
def mti_0200() -> Mti:
    return Mti.from_str("0200")


@pytest.fixture(scope="module")
def single_field_model() -> Iso8583MessageModel:
    return Iso8583MessageModel(primary_account_number="1234567890123456")


@pytest.fixture(scope="module")
def all_fields_model() -> Iso8583MessageModel:
    return Iso8583MessageModel(
        primary_account_number="1234567890123456",
        processing_code="000000",
        amount_transaction="000000010000",
        transmission_date_and_time="0319120000",
        systems_trace_audit_number="000001",
        response_code="00",
    )


@pytest.fixture(scope="module")
def encoded_single_field(adapter: PyIso8583Adapter, mti_0200: Mti) -> bytes:
    model = Iso8583MessageModel(primary_account_number="1234567890123456")
    return bytes(adapter.generate(mti_0200, model))


@pytest.fixture(scope="module")
def encoded_all_fields(
    adapter: PyIso8583Adapter, mti_0200: Mti, all_fields_model: Iso8583MessageModel
) -> bytes:
    return bytes(adapter.generate(mti_0200, all_fields_model))


# ==============================================================================
# エンコードベンチマーク
# ==============================================================================

class TestEncodePerformance:
    def test_perf_enc_01_single_field_encode(
        self,
        benchmark: "BenchmarkFixture",
        adapter: PyIso8583Adapter,
        mti_0200: Mti,
        single_field_model: Iso8583MessageModel,
    ) -> None:
        """単一フィールド（PAN のみ）のエンコード性能を計測する。"""
        result = benchmark(adapter.generate, mti_0200, single_field_model)
        assert isinstance(result, bytearray)
        assert len(result) > 0

    def test_perf_enc_02_all_fields_encode(
        self,
        benchmark: "BenchmarkFixture",
        adapter: PyIso8583Adapter,
        mti_0200: Mti,
        all_fields_model: Iso8583MessageModel,
    ) -> None:
        """全フィールドのエンコード性能を計測する。"""
        result = benchmark(adapter.generate, mti_0200, all_fields_model)
        assert isinstance(result, bytearray)
        assert len(result) > 0

    def test_perf_enc_03_use_case_execute(
        self,
        benchmark: "BenchmarkFixture",
        use_case: GenerateMessageUseCase,
        mti_0200: Mti,
        all_fields_model: Iso8583MessageModel,
    ) -> None:
        """ユースケース経由でのエンコード性能を計測する。"""
        result = benchmark(use_case.execute, mti=mti_0200, model_data=all_fields_model)
        assert isinstance(result, bytearray)


# ==============================================================================
# デコードベンチマーク
# ==============================================================================

class TestDecodePerformance:
    def test_perf_dec_01_single_field_decode(
        self,
        benchmark: "BenchmarkFixture",
        adapter: PyIso8583Adapter,
        encoded_single_field: bytes,
    ) -> None:
        """単一フィールドのデコード性能を計測する。"""
        mti_str, model = benchmark(
            adapter.parse, encoded_single_field, Iso8583MessageModel
        )
        assert mti_str == "0200"
        assert model.primary_account_number == "1234567890123456"

    def test_perf_dec_02_all_fields_decode(
        self,
        benchmark: "BenchmarkFixture",
        adapter: PyIso8583Adapter,
        encoded_all_fields: bytes,
    ) -> None:
        """全フィールドのデコード性能を計測する。"""
        mti_str, model = benchmark(
            adapter.parse, encoded_all_fields, Iso8583MessageModel
        )
        assert mti_str == "0200"
        assert model.primary_account_number == "1234567890123456"


# ==============================================================================
# ラウンドトリップベンチマーク
# ==============================================================================

class TestRoundtripPerformance:
    def test_perf_rt_01_single_field_roundtrip(
        self,
        benchmark: "BenchmarkFixture",
        adapter: PyIso8583Adapter,
        mti_0200: Mti,
    ) -> None:
        """単一フィールドの encode → decode 往復性能を計測する。"""
        def roundtrip() -> str:
            model = Iso8583MessageModel(primary_account_number="1234567890123456")
            raw = adapter.generate(mti_0200, model)
            mti_str, decoded = adapter.parse(bytes(raw), Iso8583MessageModel)
            return mti_str

        result = benchmark(roundtrip)
        assert result == "0200"

    def test_perf_rt_02_throughput_1000_messages(
        self,
        adapter: PyIso8583Adapter,
        mti_0200: Mti,
    ) -> None:
        """1,000 メッセージのエンコード→デコードが正常に完了すること（スループット検証）。"""
        model = Iso8583MessageModel(
            primary_account_number="1234567890123456",
            processing_code="000000",
            amount_transaction="000000010000",
            systems_trace_audit_number="000001",
        )
        for i in range(1000):
            raw = adapter.generate(mti_0200, model)
            mti_str, decoded = adapter.parse(bytes(raw), Iso8583MessageModel)
            assert mti_str == "0200"
            assert decoded.primary_account_number == "1234567890123456"

    def test_perf_rt_03_mti_parsing_performance(
        self,
        benchmark: "BenchmarkFixture",
    ) -> None:
        """MTI 文字列パース（Mti.from_str）の性能を計測する。"""
        result = benchmark(Mti.from_str, "0200")
        assert result.to_str() == "0200"
