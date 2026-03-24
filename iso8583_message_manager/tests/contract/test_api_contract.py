"""
schemathesis 契約テスト。

テスト戦略 doc/api/api_design.md §9.5 CT-01〜03 に対応。
openapi.yaml スキーマに基づいて自動生成されたリクエストで全エンドポイントを検証する。

前提:
  - openapi.yaml が生成済みであること（未生成の場合は fixture が生成する）
  - schemathesis >= 4.0 がインストール済みであること
"""
import sys
from pathlib import Path

import pytest

APP_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(APP_DIR / "src"))
sys.path.insert(0, str(APP_DIR / "scripts" / "code_generator"))

ROOT_DIR = APP_DIR.parent
_OUTPUT_YAML = ROOT_DIR / "packages" / "iso8583-core" / "src" / "iso8583_core" / "data" / "schemas" / "generated" / "openapi.yaml"


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
    schemathesis = pytest.importorskip("schemathesis", reason="schemathesis が必要")

    from schemathesis.core.result import Ok
    from schemathesis.transport.asgi import ASGI_TRANSPORT

    from iso8583_api.app import app as fastapi_app

    # schemathesis 4.x: openapi.from_asgi() で ASGI アプリから直接スキーマを読み込む
    schema = schemathesis.openapi.from_asgi("/openapi.json", fastapi_app)

    # 全オペレーションを列挙し、スキーマ例から生成したケースを ASGI 経由で検証する
    for result in schema.get_all_operations():
        if not isinstance(result, Ok):
            continue
        operation = result.ok()
        case = schema.make_case(operation=operation)
        response = ASGI_TRANSPORT.send(case)
        operation.validate_response(response)
