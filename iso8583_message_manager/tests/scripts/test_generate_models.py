"""
generate_models.py のユニットテスト。

テスト戦略 doc/test_strategy.md §4.1 GEN-MD-01〜04 に対応。
"""
import ast
import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

APP_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(APP_DIR / "src"))
sys.path.insert(0, str(APP_DIR / "scripts" / "code_generator"))

import generate_models as gen_mod  # noqa: E402
from generate_models import generate_models  # noqa: E402

ROOT_DIR = APP_DIR.parent  # d:/Projects/Cards/
_FIELDS_JSON = ROOT_DIR / "packages" / "iso8583-core" / "src" / "iso8583_core" / "data" / "schemas" / "iso8583_fields.json"


@pytest.fixture(scope="module")
def fields() -> dict:
    with open(_FIELDS_JSON, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def generated_models_file(tmp_path: Path, fields: dict) -> Path:
    """一時ディレクトリに iso_models.py を生成して返す。"""
    output_file = tmp_path / "iso_models.py"
    with (
        patch.object(gen_mod, "JSON_FILE", _FIELDS_JSON),
        patch.object(gen_mod, "MODELS_FILE", output_file),
        patch.object(gen_mod, "GENERATED_DIR", tmp_path),
    ):
        generate_models()
    return output_file


class TestGenerateModels:
    def test_gen_md_01_class_and_fields_exist(
        self, generated_models_file: Path, fields: dict
    ) -> None:
        """GEN-MD-01: 標準 JSON から Pydantic クラスを生成 → クラス名・フィールド名の存在確認。"""
        content = generated_models_file.read_text(encoding="utf-8")
        assert "class Iso8583MessageModel" in content
        for _field_id, meta in fields.items():
            assert meta["name"] in content, (
                f"フィールド '{meta['name']}' が生成ファイルに存在しない"
            )

    def test_gen_md_02_field_mapping_completeness(
        self, generated_models_file: Path, fields: dict
    ) -> None:
        """GEN-MD-02: field_mapping の完全性検証（JSON の全フィールド ID が含まれる）。"""
        content = generated_models_file.read_text(encoding="utf-8")
        for field_id in fields.keys():
            assert f'"{field_id}"' in content, (
                f"フィールド ID '{field_id}' が field_mapping に存在しない"
            )

    def test_gen_md_03_no_syntax_error(self, generated_models_file: Path) -> None:
        """GEN-MD-03: 生成ファイルが Python として構文エラーなし（ast.parse で検証）。"""
        content = generated_models_file.read_text(encoding="utf-8")
        try:
            ast.parse(content)
        except SyntaxError as exc:
            pytest.fail(f"生成ファイルに構文エラーがあります: {exc}")

    def test_gen_md_04_missing_json_file_exits(self, tmp_path: Path) -> None:
        """GEN-MD-04: JSON ファイル不在時に適切なエラー（sys.exit(1)）。"""
        output_file = tmp_path / "iso_models.py"
        with (
            patch.object(gen_mod, "JSON_FILE", tmp_path / "nonexistent.json"),
            patch.object(gen_mod, "MODELS_FILE", output_file),
            patch.object(gen_mod, "GENERATED_DIR", tmp_path),
            pytest.raises(SystemExit) as exc_info,
        ):
            generate_models()
        assert exc_info.value.code == 1
