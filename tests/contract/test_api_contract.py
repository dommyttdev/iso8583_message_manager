"""
schemathesis 契約テスト。

テスト戦略 doc/api/api_design.md §9.5 CT-01〜03 に対応。
openapi.yaml スキーマに基づいて自動生成されたリクエストで全エンドポイントを検証する。

前提:
  - openapi.yaml が生成済みであること（未生成の場合は fixture が生成する）
  - schemathesis >= 3.0 がインストール済みであること
"""
import sys
from pathlib import Path

import pytest

APP_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(APP_DIR / "src"))
sys.path.insert(0, str(APP_DIR / "scripts" / "code_generator"))

_OUTPUT_YAML = APP_DIR / "src" / "iso8583_manager" / "data" / "schemas" / "generated" / "openapi.yaml"


@pytest.fixture(scope="module", autouse=True)
def ensure_openapi_yaml() -> None:
    """テスト実行前に openapi.yaml が存在することを保証する。"""
    if not _OUTPUT_YAML.exists():
        import generate_openapi  # type: ignore[import]

        generate_openapi.generate_openapi()


def test_ct_01_02_03_api_contract() -> None:
    """
    CT-01〜03: OpenAPI スキーマに基づいて自動生成されたリクエストで全エンドポイントを検証。

    - CT-01: 全エンドポイントのレスポンスが OpenAPI スキーマの型定義に準拠
    - CT-02: エラーレスポンスが ErrorResponse スキーマに準拠
    - CT-03: バリデーションエラーレスポンスが ValidationErrorResponse スキーマに準拠
    """
    schemathesis = pytest.importorskip(
        "schemathesis", reason="schemathesis が必要"
    )

    from iso8583_manager.presentation.api.app import app as fastapi_app

    schema = schemathesis.from_path(
        str(_OUTPUT_YAML),
        app=fastapi_app,
        base_url="http://testserver",
    )

    # schemathesis が生成した各テストケースを ASGI 経由で実行して検証する
    for case in schema.get_all_cases():
        with schemathesis.runner.transport.asgi.ASGIClient(fastapi_app) as session:
            response = case.call(session=session)
            case.validate_response(response)
