# REST API テスト計画

> **API 設計仕様**（エンドポイント定義・スキーマ・エラーハンドリング等）は `doc/api/api_design.md` を参照。
> **全体テスト方針・カバレッジ評価・ロードマップ**は `doc/tests/test_strategy.md` を参照。

---

## 1. 基本方針

- FastAPI `TestClient`（httpx ベース）を使用。
- ユースケース層は pytest-mock で差し替え、**Presentation 層の責務のみ**を検証。
  - 検証対象: スキーマ変換・バリデーション・エラーハンドリング・HTTP ステータスコード
- 実 Adapter を使った結合テストは `tests/integration/test_api_integration.py` に分離。

---

## 2. テストファイル配置

```
tests/presentation/api/
├── __init__.py
├── test_health.py             # GET /api/v1/health
├── test_metadata.py           # GET /api/v1/fields, /mti-types
├── test_generate_endpoint.py  # POST /api/v1/messages/generate
└── test_parse_endpoint.py     # POST /api/v1/messages/parse

tests/scripts/
└── test_openapi_validity.py   # 生成された openapi.yaml の仕様準拠検証

tests/contract/
└── test_api_contract.py       # schemathesis 契約テスト
```

---

## 3. ルーターユニットテスト ✅ 完了

### `test_health.py`

| テストID | テスト内容 | 期待結果 | 状態 |
|---------|-----------|---------|------|
| API-HLT-01 | `GET /api/v1/health` | 200, `{"status": "ok"}` | ✅ |

### `test_metadata.py`

| テストID | テスト内容 | 検証観点 | 状態 |
|---------|-----------|---------|------|
| API-META-01 | `GET /api/v1/fields` → 200 | フィールド数が JSON スキーマと一致 | ✅ |
| API-META-02 | 各フィールドが `field_id`, `name`, `description`, `data_type`, `len_type`, `max_len` を持つ | `FieldDefinition` スキーマ準拠 | ✅ |
| API-META-03 | `GET /api/v1/mti-types` → 200 | `versions`/`classes`/`functions`/`origins` の 4 キー存在 | ✅ |
| API-META-04 | 各エントリが `code`, `description` を持つ | `MtiCodeEntry` スキーマ準拠 | ✅ |
| API-META-05 | `versions` の件数が `MtiVersion` enum 数と一致 | `mti.py` との同期保証 | ✅ |

### `test_generate_endpoint.py`

| テストID | テスト内容 | 期待結果 | 状態 |
|---------|-----------|---------|------|
| API-GEN-01 | 正常リクエスト（全フィールド, `output_format: hex`） | 200, `encoded_message` が hex 文字列 | ✅ |
| API-GEN-02 | `output_format: base64` | 200, Base64 文字列 | ✅ |
| API-GEN-03 | フィールド省略（MTI のみ） | 200 | ✅ |
| API-GEN-04 | `mti` 形式不正（3桁） | 422, パターン違反 | ✅ |
| API-GEN-05 | `mti` 未定義クラス（`"0900"`） | 400, `INVALID_MTI` | ✅ |
| API-GEN-06 | 未定義フィールド名（`unknown_field: "xxx"`） | 422, `additionalProperties` 違反 | ✅ |
| API-GEN-07 | フィールド値が maxLength 超過 | 422, `max_length` 違反 | ✅ |
| API-GEN-08 | 固定長フィールドの長さ不一致 | 422, `min/max_length` 違反 | ✅ |
| API-GEN-09 | `mti` キー欠落 | 422, required フィールド欠落 | ✅ |
| API-GEN-10 | エンコード失敗（アダプターエラー） | 400, `MESSAGE_ENCODE_ERROR` | ✅ |

### `test_parse_endpoint.py`

| テストID | テスト内容 | 期待結果 | 状態 |
|---------|-----------|---------|------|
| API-PAR-01 | 正常 hex 入力 | 200, `mti`・`fields`・`mti_description` を含む | ✅ |
| API-PAR-02 | 正常 base64 入力 | 200 | ✅ |
| API-PAR-03 | `mti_description` の全 4 キー（version/class/function/origin）存在 | `MtiDescription` スキーマ準拠 | ✅ |
| API-PAR-04 | 不正な hex 文字列（非 16 進数文字含む） | 400, `INVALID_FORMAT` | ✅ |
| API-PAR-05 | 奇数長の hex 文字列 | 400, `INVALID_FORMAT` | ✅ |
| API-PAR-06 | デコード失敗（破損データ） | 400, `MESSAGE_DECODE_ERROR` | ✅ |
| API-PAR-07 | `encoded_message` キー欠落 | 422 | ✅ |

---

## 4. OpenAPI スキーマ有効性テスト ✅ 完了

**配置:** `tests/scripts/test_openapi_validity.py`
**依存:** `openapi-spec-validator`

| テストID | テスト内容 | 状態 |
|---------|-----------|------|
| OA-VAL-01 | 生成された `openapi.yaml` が有効な OpenAPI 3.1.0 スキーマ | ✅ |
| OA-VAL-02 | 全 `$ref` 参照が解決可能 | ✅ |
| OA-VAL-03 | 全エンドポイントに `operationId` が存在 | ✅ |
| OA-VAL-04 | `MessageFields` に `additionalProperties: false` が存在 | ✅ |
| OA-VAL-05 | `MessageFields.properties` 数が JSON スキーマのフィールド数と一致 | ✅ |

---

## 5. 契約テスト ✅ 完了

**配置:** `tests/contract/test_api_contract.py`
**依存:** `schemathesis>=4.0`

```python
import schemathesis
from schemathesis.core.result import Ok
from schemathesis.transport.asgi import ASGI_TRANSPORT

# schemathesis 4.x: ASGI アプリから直接スキーマを読み込む
schema = schemathesis.openapi.from_asgi("/openapi.json", fastapi_app)

for result in schema.get_all_operations():
    if not isinstance(result, Ok):
        continue
    operation = result.ok()
    case = schema.make_case(operation=operation)
    response = ASGI_TRANSPORT.send(case)
    operation.validate_response(response)
```

| テストID | 検証内容 | 状態 |
|---------|---------|------|
| CT-01 | 全エンドポイントのレスポンスが OpenAPI スキーマの型定義に準拠 | ✅ |
| CT-02 | エラーレスポンスが `ErrorResponse` スキーマに準拠 | ✅ |
| CT-03 | バリデーションエラーレスポンスが `ValidationErrorResponse` スキーマに準拠 | ✅ |
