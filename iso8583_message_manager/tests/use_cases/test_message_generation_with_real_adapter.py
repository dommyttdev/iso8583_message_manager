"""
GenerateMessageUseCase / ParseMessageUseCase の実アダプターを使った結合テスト。

テスト戦略 doc/test_strategy.md §4.5 UC-RA-01〜03 に対応。
モックを使わず実 PyIso8583Adapter を注入し、
現行統合テストより細粒度でユースケース層を検証する。
"""
from importlib.resources import files as _pkg_files

import pytest

from iso8583_types.core.models.generated.iso_models import Iso8583MessageModel
from iso8583_types.core.models.mti import Mti
from iso8583_manager.infrastructure.pyiso8583_adapter.wrapper import PyIso8583Adapter
from iso8583_manager.use_cases.message_generation import GenerateMessageUseCase
from iso8583_manager.use_cases.message_parsing import ParseMessageUseCase

_SPEC_PATH = str(_pkg_files("iso8583_manager.data.schemas") / "iso8583_fields.json")


@pytest.fixture(scope="module")
def adapter() -> PyIso8583Adapter:
    return PyIso8583Adapter(spec_json_path=_SPEC_PATH)


@pytest.fixture(scope="module")
def generate_use_case(adapter: PyIso8583Adapter) -> GenerateMessageUseCase:
    return GenerateMessageUseCase(message_generator=adapter)


@pytest.fixture(scope="module")
def parse_use_case(adapter: PyIso8583Adapter) -> ParseMessageUseCase:
    return ParseMessageUseCase(message_generator=adapter)


class TestUseCasesWithRealAdapter:
    def test_uc_ra_01_generate_returns_bytearray(
        self,
        generate_use_case: GenerateMessageUseCase,
    ) -> None:
        """UC-RA-01: 実アダプターで GenerateMessageUseCase を実行 → bytearray を返す。"""
        mti = Mti.from_str("0200")
        model = Iso8583MessageModel(
            primary_account_number="4111111111111111",
            processing_code="000000",
        )
        result = generate_use_case.execute(mti, model)
        assert isinstance(result, bytearray)
        assert len(result) > 0

    def test_uc_ra_02_parse_returns_mti_and_model(
        self,
        generate_use_case: GenerateMessageUseCase,
        parse_use_case: ParseMessageUseCase,
    ) -> None:
        """UC-RA-02: 実アダプターで ParseMessageUseCase を実行 → Mti と Iso8583MessageModel を返す。"""
        mti_original = Mti.from_str("0200")
        model_original = Iso8583MessageModel(primary_account_number="4111111111111111")
        raw = generate_use_case.execute(mti_original, model_original)

        mti_parsed, model_parsed = parse_use_case.execute(bytes(raw), Iso8583MessageModel)

        assert isinstance(mti_parsed, Mti)
        assert isinstance(model_parsed, Iso8583MessageModel)

    def test_uc_ra_03_generate_parse_roundtrip(
        self,
        generate_use_case: GenerateMessageUseCase,
        parse_use_case: ParseMessageUseCase,
    ) -> None:
        """UC-RA-03: 生成→解析の往復で全フィールド値が一致。"""
        mti_original = Mti.from_str("0100")
        model_original = Iso8583MessageModel(
            primary_account_number="5500005555555559",
            processing_code="000000",
            amount_transaction="000000050000",
            systems_trace_audit_number="000042",
        )

        raw = generate_use_case.execute(mti_original, model_original)
        mti_parsed, model_parsed = parse_use_case.execute(bytes(raw), Iso8583MessageModel)

        assert mti_parsed.to_str() == mti_original.to_str()
        assert model_parsed.primary_account_number == model_original.primary_account_number
        assert model_parsed.processing_code == model_original.processing_code
        assert model_parsed.amount_transaction == model_original.amount_transaction
        assert model_parsed.systems_trace_audit_number == model_original.systems_trace_audit_number
