"""
CLI 統合テスト。

実際の PyIso8583Adapter と実 spec ファイルを使い、CLI コマンド全体を End-to-End で検証する。
モックは一切使用しない。
"""
import json
from importlib.resources import files as _pkg_files

from typer.testing import CliRunner

from iso8583_types.models.mti import MtiClass, MtiFunction, MtiOrigin, MtiVersion
from iso8583_cli.app import app

runner = CliRunner()

_REAL_SPEC_PATH = str(_pkg_files("iso8583_core.data.schemas") / "iso8583_fields.json")

# generate → parse ラウンドトリップ用の共通フィールド
_ROUNDTRIP_FIELDS = [
    "primary_account_number=1234567890123456",
    "processing_code=123456",
    "amount_transaction=000000001000",
    "transmission_date_and_time=1234567890",
    "systems_trace_audit_number=111222",
]


# ==============================================================================
# generate → parse ラウンドトリップ
# ==============================================================================

class TestGenerateParseRoundtrip:
    def test_roundtrip_single_field(self) -> None:
        """1フィールドのエンコード→デコードが一致する。"""
        gen_result = runner.invoke(app, [
            "generate", "0200",
            "primary_account_number=1234567890123456",
            "--spec", _REAL_SPEC_PATH,
        ])
        assert gen_result.exit_code == 0
        hex_str = gen_result.output.strip()

        parse_result = runner.invoke(app, ["parse", hex_str, "--spec", _REAL_SPEC_PATH])
        assert parse_result.exit_code == 0
        data = json.loads(parse_result.output)
        assert data["fields"]["primary_account_number"] == "1234567890123456"

    def test_roundtrip_all_fields(self) -> None:
        """全フィールドが往復で一致する。"""
        gen_result = runner.invoke(app, [
            "generate", "0200",
            *_ROUNDTRIP_FIELDS,
            "--spec", _REAL_SPEC_PATH,
        ])
        assert gen_result.exit_code == 0
        hex_str = gen_result.output.strip()

        parse_result = runner.invoke(app, ["parse", hex_str, "--spec", _REAL_SPEC_PATH])
        assert parse_result.exit_code == 0
        data = json.loads(parse_result.output)
        assert data["fields"]["primary_account_number"] == "1234567890123456"
        assert data["fields"]["processing_code"] == "123456"
        assert data["fields"]["amount_transaction"] == "000000001000"
        assert data["fields"]["transmission_date_and_time"] == "1234567890"
        assert data["fields"]["systems_trace_audit_number"] == "111222"

    def test_roundtrip_mti_preserved(self) -> None:
        """generate 後の parse で MTI 文字列が元と一致する。"""
        gen_result = runner.invoke(app, [
            "generate", "0200",
            "primary_account_number=1234567890123456",
            "--spec", _REAL_SPEC_PATH,
        ])
        assert gen_result.exit_code == 0
        hex_str = gen_result.output.strip()

        parse_result = runner.invoke(app, ["parse", hex_str, "--spec", _REAL_SPEC_PATH])
        assert parse_result.exit_code == 0
        data = json.loads(parse_result.output)
        assert data["mti"] == "0200"

    def test_generate_hex_output_is_valid_hex(self) -> None:
        """generate の出力が有効な hex 文字列である。"""
        result = runner.invoke(app, [
            "generate", "0200",
            "primary_account_number=1234567890123456",
            "--spec", _REAL_SPEC_PATH,
        ])
        assert result.exit_code == 0
        hex_str = result.output.strip()
        assert len(hex_str) > 0
        # 有効な hex 文字列であることを確認
        bytes.fromhex(hex_str)

    def test_roundtrip_parametrized_mti_classes(self) -> None:
        """0100/0200/0800 の各 MTI でラウンドトリップが成功する。"""
        for mti_str in ["0100", "0200", "0800"]:
            gen_result = runner.invoke(app, [
                "generate", mti_str,
                "primary_account_number=1234567890123456",
                "--spec", _REAL_SPEC_PATH,
            ])
            assert gen_result.exit_code == 0, f"MTI {mti_str} でgenerate失敗: {gen_result.output}"
            hex_str = gen_result.output.strip()

            parse_result = runner.invoke(app, ["parse", hex_str, "--spec", _REAL_SPEC_PATH])
            assert parse_result.exit_code == 0, f"MTI {mti_str} でparse失敗: {parse_result.output}"
            data = json.loads(parse_result.output)
            assert data["mti"] == mti_str


# ==============================================================================
# fields コマンド
# ==============================================================================

class TestFieldsCommandIntegration:
    def test_fields_lists_all_spec_fields(self) -> None:
        """実 spec の全フィールドが出力に含まれる。"""
        result = runner.invoke(app, ["fields", "--spec", _REAL_SPEC_PATH])
        assert result.exit_code == 0
        # 既知のフィールド名を確認
        assert "primary_account_number" in result.output
        assert "processing_code" in result.output
        assert "amount_transaction" in result.output

    def test_fields_field_count_matches_spec(self) -> None:
        """出力フィールド数と spec 定義数が一致する。"""
        import json as _json
        spec_data = _json.loads(
            (_pkg_files("iso8583_core.data.schemas") / "iso8583_fields.json").read_text(encoding="utf-8")
        )

        result = runner.invoke(app, ["fields", "--spec", _REAL_SPEC_PATH])
        assert result.exit_code == 0
        # 各フィールドは表の行に含まれる; フィールドIDがすべて出力にあることを確認
        for field_id in spec_data:
            assert field_id in result.output, f"フィールドID {field_id} が出力に見つからない"


# ==============================================================================
# mti-types コマンド
# ==============================================================================

class TestMtiTypesCommandIntegration:
    def test_mti_types_shows_all_defined_enums(self) -> None:
        """全 4 enum グループが出力に含まれる。"""
        result = runner.invoke(app, ["mti-types"])
        assert result.exit_code == 0
        # 各グループのサンプルメンバーを確認
        assert "V1987" in result.output
        assert "AUTHORIZATION" in result.output
        assert "REQUEST" in result.output
        assert "ACQUIRER" in result.output

    def test_mti_types_member_count_matches_python_enums(self) -> None:
        """JSON 出力の各配列の要素数が Python の enum 定義数と完全一致する。"""
        result = runner.invoke(app, ["mti-types", "--output", "json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data["version"]) == len(MtiVersion)
        assert len(data["class"]) == len(MtiClass)
        assert len(data["function"]) == len(MtiFunction)
        assert len(data["origin"]) == len(MtiOrigin)


# ==============================================================================
# エラー系 (実 adapter 使用)
# ==============================================================================

class TestErrorHandlingIntegration:
    def test_generate_unknown_mti_exits_1(self) -> None:
        """不明 MTI → 実際の exit 1。"""
        result = runner.invoke(app, ["generate", "0900", "--spec", _REAL_SPEC_PATH])
        assert result.exit_code == 1

    def test_parse_corrupted_hex_exits_4(self) -> None:
        """ゴミ hex (文法は正しいが ISO 8583 として不正) → exit 4。"""
        # 有効な hex だが ISO 8583 デコードに失敗するバイト列
        corrupted_hex = "deadbeefdeadbeef"
        result = runner.invoke(app, ["parse", corrupted_hex, "--spec", _REAL_SPEC_PATH])
        assert result.exit_code == 4

    def test_missing_spec_exits_2(self) -> None:
        """存在しない spec → exit 2。"""
        result = runner.invoke(app, [
            "generate", "0200", "--spec", "/nonexistent/spec.json"
        ])
        assert result.exit_code == 2


# ==============================================================================
# 不正 MTI が全レイヤーで拒否されること（クロスレイヤー検証）
# ==============================================================================

class TestInvalidMtiRejectedCrossLayer:
    """不正 MTI が cli → core → types の全レイヤーで正しく拒否されることを検証する。"""

    def test_invalid_mti_version_exits_1(self) -> None:
        """未定義バージョン (3200) → types 層で拒否 → exit 1"""
        result = runner.invoke(app, [
            "generate", "3200", "--spec", _REAL_SPEC_PATH,
        ])
        assert result.exit_code == 1

    def test_invalid_mti_function_exits_1(self) -> None:
        """未定義機能 (0150) → types 層で拒否 → exit 1"""
        result = runner.invoke(app, [
            "generate", "0150", "--spec", _REAL_SPEC_PATH,
        ])
        assert result.exit_code == 1

    def test_invalid_mti_origin_exits_1(self) -> None:
        """未定義発生源 (0106) → types 層で拒否 → exit 1"""
        result = runner.invoke(app, [
            "generate", "0106", "--spec", _REAL_SPEC_PATH,
        ])
        assert result.exit_code == 1

    def test_all_invalid_mti_produce_no_hex_output(self) -> None:
        """不正 MTI では有効な hex メッセージが出力されないこと"""
        for mti_str in ["0900", "3200", "0150", "0106"]:
            result = runner.invoke(app, [
                "generate", mti_str, "--spec", _REAL_SPEC_PATH,
            ])
            assert result.exit_code == 1, f"MTI {mti_str}: exit_code が 1 でない"
            # 正常な hex メッセージ（偶数桁の純粋な hex 文字列）が出力されていないこと
            output = result.output.strip()
            try:
                bytes.fromhex(output)
                raise AssertionError(f"MTI {mti_str}: エラー時に有効な hex が出力された")
            except ValueError:
                pass  # 期待通り（hex としてパースできない = エラーメッセージが出力された）


# ==============================================================================
# 全フィールドを使用した最大メッセージの E2E
# ==============================================================================

class TestAllFieldsE2E:
    """全フィールドを同時使用した最大メッセージの CLI E2E 検証。"""

    def test_all_fields_generate_and_parse_roundtrip(self) -> None:
        """全フィールドが generate → parse で欠損なく往復すること"""
        all_fields = [
            "primary_account_number=1234567890123456",
            "processing_code=123456",
            "amount_transaction=000000001000",
            "transmission_date_and_time=1234567890",
            "systems_trace_audit_number=111222",
            "response_code=00",
        ]
        gen_result = runner.invoke(app, [
            "generate", "0200", *all_fields, "--spec", _REAL_SPEC_PATH,
        ])
        assert gen_result.exit_code == 0
        hex_str = gen_result.output.strip()

        parse_result = runner.invoke(app, ["parse", hex_str, "--spec", _REAL_SPEC_PATH])
        assert parse_result.exit_code == 0
        data = json.loads(parse_result.output)

        assert data["mti"] == "0200"
        assert data["fields"]["primary_account_number"] == "1234567890123456"
        assert data["fields"]["processing_code"] == "123456"
        assert data["fields"]["amount_transaction"] == "000000001000"
        assert data["fields"]["transmission_date_and_time"] == "1234567890"
        assert data["fields"]["systems_trace_audit_number"] == "111222"
        assert data["fields"]["response_code"] == "00"

    def test_all_fields_message_larger_than_single_field(self) -> None:
        """全フィールド使用時のメッセージが単一フィールドより大きいこと"""
        single = runner.invoke(app, [
            "generate", "0200",
            "primary_account_number=1234567890123456",
            "--spec", _REAL_SPEC_PATH,
        ])
        full = runner.invoke(app, [
            "generate", "0200",
            "primary_account_number=1234567890123456",
            "processing_code=123456",
            "amount_transaction=000000001000",
            "transmission_date_and_time=1234567890",
            "systems_trace_audit_number=111222",
            "response_code=00",
            "--spec", _REAL_SPEC_PATH,
        ])
        assert single.exit_code == 0
        assert full.exit_code == 0
        assert len(bytes.fromhex(full.output.strip())) > len(bytes.fromhex(single.output.strip()))
