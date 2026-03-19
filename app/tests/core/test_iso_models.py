"""
Iso8583MessageModel のユニットテスト。

テスト戦略 doc/test_strategy.md §4.2 MODEL-01〜11 に対応。
"""
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from iso8583_manager.core.models.generated.iso_models import Iso8583MessageModel

_FIELDS_JSON = (
    Path(__file__).parent.parent.parent / "data" / "schemas" / "iso8583_fields.json"
)


class TestFieldConstraints:
    """MODEL-01〜05: フィールド制約のテスト。"""

    def test_model_01_all_fields_optional(self) -> None:
        """MODEL-01: 全フィールド省略可能（すべて None でインスタンス化）。"""
        model = Iso8583MessageModel()
        assert model.primary_account_number is None
        assert model.processing_code is None
        assert model.amount_transaction is None
        assert model.transmission_date_and_time is None
        assert model.systems_trace_audit_number is None
        assert model.response_code is None

    def test_model_02_max_length_valid(self) -> None:
        """MODEL-02: 各フィールドの最大長ちょうどで正常（Pydantic max_length 境界値）。"""
        model = Iso8583MessageModel(
            primary_account_number="1234567890123456789",  # 可変長 max=19
            processing_code="123456",                      # 固定長 6
            amount_transaction="123456789012",             # 固定長 12
            transmission_date_and_time="0101120000",       # 固定長 10
            systems_trace_audit_number="123456",           # 固定長 6
            response_code="AB",                            # 固定長 2 (an型)
        )
        assert model.primary_account_number == "1234567890123456789"
        assert model.response_code == "AB"

    def test_model_03_max_length_plus1_raises(self) -> None:
        """MODEL-03: 各フィールドの最大長+1で ValidationError。"""
        with pytest.raises(ValidationError):
            Iso8583MessageModel(processing_code="1234567")  # max=6、7桁はNG

    def test_model_04_pan_min_length_1_valid(self) -> None:
        """MODEL-04: 可変長フィールド（PAN）の最小長 1 で正常（min_length=1 の確認）。"""
        model = Iso8583MessageModel(primary_account_number="1")
        assert model.primary_account_number == "1"

    def test_model_05_pan_empty_string_raises(self) -> None:
        """MODEL-05: 可変長フィールド（PAN）の空文字列で ValidationError（min_length 検出）。"""
        with pytest.raises(ValidationError):
            Iso8583MessageModel(primary_account_number="")

    def test_model_extra_field_raises(self) -> None:
        """extra="forbid" により未定義フィールドで ValidationError が発生する。"""
        with pytest.raises(ValidationError):
            Iso8583MessageModel(unknown_field="xxx")  # type: ignore[call-arg]


class TestToIsoDict:
    """MODEL-06〜08: to_iso_dict() のテスト。"""

    def test_model_06_exclude_unset(self) -> None:
        """MODEL-06: to_iso_dict() — 設定フィールドのみを返す（exclude_unset 動作）。"""
        model = Iso8583MessageModel(processing_code="000000")
        result = model.to_iso_dict()
        assert "3" in result
        assert "2" not in result
        assert "4" not in result

    def test_model_07_exclude_none(self) -> None:
        """MODEL-07: to_iso_dict() — None フィールドを含まない（exclude_none 動作）。"""
        model = Iso8583MessageModel(primary_account_number="1234567890")
        result = model.to_iso_dict()
        assert None not in result.values()
        assert "4" not in result  # amount_transaction は未設定

    def test_model_08_key_is_iso_field_number_string(self) -> None:
        """MODEL-08: to_iso_dict() — キーが ISO フィールド番号文字列（"2","4" 形式）。"""
        model = Iso8583MessageModel(
            primary_account_number="1234567890",
            amount_transaction="000000010000",
        )
        result = model.to_iso_dict()
        assert "2" in result
        assert "4" in result
        assert result["2"] == "1234567890"
        assert result["4"] == "000000010000"


class TestFromIsoDict:
    """MODEL-09〜10: from_iso_dict() のテスト。"""

    def test_model_09_roundtrip(self) -> None:
        """MODEL-09: from_iso_dict() — 全フィールドの往復変換（encode → decode の一致）。"""
        original = Iso8583MessageModel(
            primary_account_number="4111111111111111",
            processing_code="000000",
            amount_transaction="000000010000",
        )
        iso_dict = original.to_iso_dict()
        restored = Iso8583MessageModel.from_iso_dict(iso_dict)
        assert restored.primary_account_number == original.primary_account_number
        assert restored.processing_code == original.processing_code
        assert restored.amount_transaction == original.amount_transaction

    def test_model_10_unknown_key_ignored(self) -> None:
        """MODEL-10: from_iso_dict() — 未知のキー（"999"）は無視（KeyError 非発生）。"""
        data = {"2": "1234567890", "999": "unknown_value"}
        model = Iso8583MessageModel.from_iso_dict(data)
        assert model.primary_account_number == "1234567890"


class TestFieldMapping:
    """MODEL-11: field_mapping の完全性検証。"""

    def test_model_11_field_mapping_count_matches_json(self) -> None:
        """MODEL-11: field_mapping が JSON の全フィールド数と一致（スキーマとモデルの同期）。"""
        with open(_FIELDS_JSON, encoding="utf-8") as f:
            fields = json.load(f)
        assert len(Iso8583MessageModel.field_mapping) == len(fields)

    def test_model_11_field_mapping_ids_match_json(self) -> None:
        """MODEL-11 補足: field_mapping の全フィールド ID が JSON に存在する。"""
        with open(_FIELDS_JSON, encoding="utf-8") as f:
            fields = json.load(f)
        json_ids = set(fields.keys())
        model_ids = set(Iso8583MessageModel.field_mapping.values())
        assert model_ids == json_ids
