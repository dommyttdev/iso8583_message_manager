# REST API 設計ノート

## 1. 概要

ISO 8583 Message Generator に HTTP アクセスを提供する REST API の設計仕様。
既存のクリーンアーキテクチャを維持しつつ、Presentation 層として API レイヤーを追加する。

---

## 2. 技術選定: FastAPI

### 選定理由

| 観点 | FastAPI | Flask | Django REST |
|------|---------|-------|-------------|
| OpenAPI 自動生成 | ✅ ビルトイン | ❌ 追加ライブラリ必要 | ❌ 追加ライブラリ必要 |
| Pydantic ネイティブ統合 | ✅ | ❌ | ❌ |
| 型安全 | ✅ Python 型ヒント → バリデーション | △ | △ |
| 非同期対応 | ✅ ASGI ネイティブ | △ | △ |
| 既存コードとの親和性 | ✅ Pydantic モデル再利用可 | △ | △ |

→ **FastAPI を採用**。既存の Pydantic モデルをリクエスト/レスポンス定義に直接転用でき、
`openapi.yaml` も自動生成されるため二重管理が不要になる。

---

## 3. アーキテクチャへの組み込み

既存のクリーンアーキテクチャを変更せず、Presentation 層に API モジュールを追加する。

```
presentation/
├── cli/          ← 既存（変更なし）
│   └── ...
└── api/          ← 新規追加
    ├── app.py           # FastAPI アプリケーション定義
    ├── routers/
    │   ├── health.py    # GET /api/v1/health
    │   ├── metadata.py  # GET /api/v1/fields, /api/v1/mti-types
    │   └── messages.py  # POST /api/v1/messages/generate, /parse
    ├── schemas/
    │   ├── generate.py  # GenerateRequest / GenerateResponse
    │   └── parse.py     # ParseRequest / ParseResponse
    └── error_handler.py # 例外 → HTTP レスポンス変換
```

**依存関係の方向は変わらない**:
`presentation/api` → `use_cases` → `core` ← `infrastructure`

DI コンテナ (`presentation/container.py`) は CLI・API の両方から共有する。

---

## 4. エンドポイント設計

### 4.1 全エンドポイント一覧

| Method | Path | 説明 |
|--------|------|------|
| GET | `/api/v1/health` | ヘルスチェック |
| GET | `/api/v1/fields` | 利用可能フィールド一覧 |
| GET | `/api/v1/mti-types` | MTI タイプ一覧 |
| POST | `/api/v1/messages/generate` | ISO 8583 メッセージ生成（エンコード） |
| POST | `/api/v1/messages/parse` | ISO 8583 メッセージ解析（デコード） |

### 4.2 設計上の決定事項

**出力フォーマット (`output_format`)**
- `hex`: 16進数文字列。人間可読で HTTP テストが容易。デフォルト。
- `base64`: バイナリデータの HTTP 転送標準。クライアントアプリとの統合時に使用。
- バイナリレスポンスは使用しない（Content-Type: application/octet-stream は REST API として扱いにくい）。

**フィールドキー形式**
- ISO フィールド番号（`"2"`, `"4"` 等）ではなくプロパティ名（`primary_account_number` 等）を使用。
- 理由: 番号は ISO 8583 の知識がないと意味不明。プロパティ名は自己説明的。
- フィールド番号との対応は `GET /api/v1/fields` で取得可能。

**MTI の検証**
- リクエストスキーマでは `pattern: "^[0-9]{4}$"` のみ（形式チェック）。
- ビジネスルールの検証（有効な組み合わせか等）はユースケース層に委譲。
- 理由: バリデーションをスキーマに詰め込むと複雑化し、ビジネスルールが Presentation 層に漏れる。

---

## 5. エラーレスポンス設計

### 5.1 HTTP ステータスコードの使い分け

| ステータス | 使用場面 |
|-----------|---------|
| 200 OK | 正常処理完了 |
| 400 Bad Request | ビジネスルール違反（無効な MTI、エンコード失敗、不正な hex 文字列等） |
| 422 Unprocessable Entity | FastAPI/Pydantic のスキーマバリデーション失敗 |
| 500 Internal Server Error | 予期しない内部エラー |

400 と 422 の分離理由:
- 422 は FastAPI が自動処理するリクエスト形式エラー（型不一致、必須フィールド欠落等）。
- 400 はアプリケーションのビジネスルール違反。この区別によりクライアントは対処が明確になる。

### 5.2 例外 → HTTP ステータスのマッピング

| 例外クラス | HTTP ステータス | エラーコード |
|-----------|----------------|-------------|
| `InvalidMtiError` | 400 | `INVALID_MTI` |
| `MessageEncodeError` | 400 | `MESSAGE_ENCODE_ERROR` |
| `MessageDecodeError` | 400 | `MESSAGE_DECODE_ERROR` |
| `SpecError` | 500 | `SPEC_ERROR` |
| その他 `Iso8583Error` | 500 | `INTERNAL_ERROR` |
| `ValueError`（フォーマット不正） | 400 | `INVALID_FORMAT` |

---

## 6. 追加ライブラリ

```toml
# pyproject.toml に追加
[dependencies]
fastapi>=0.115.0
uvicorn[standard]>=0.30.0        # ASGI サーバー

[project.optional-dependencies.dev]
httpx>=0.27.0                    # FastAPI TestClient の依存
pyyaml>=6.0                      # generate_openapi.py（既にインストール済み）
openapi-spec-validator>=0.7      # OpenAPI スキーマ有効性テスト
schemathesis>=3.0                # 契約テスト（API 実装後）
```

---

## 7. 起動方法（想定）

```bash
# 開発サーバー起動
cd iso8583_message_generator/app/
uvicorn iso8583_manager.presentation.api.app:app --reload --port 8000

# 本番起動
uvicorn iso8583_manager.presentation.api.app:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## 8. ソースコードと openapi.yaml の連携

### 8.1 単一真実の源（Single Source of Truth）

```
iso8583_fields.json ──┬─→ generate_models.py  ──→ iso_models.py  (Pydantic モデル)
                      │
                      └─→ generate_openapi.py ──→ openapi.yaml   (API スキーマ)
                                 ↑
mti.py (enum) ─────────────────┘
```

- フィールドを変更する場合は `iso8583_fields.json` のみを編集
- MTI タイプを変更する場合は `mti.py` の enum のみを編集
- いずれの場合も両スクリプトを実行して再生成する

### 8.2 ファイル構成

| ファイル | 管理 | 役割 |
|---------|------|------|
| `app/data/schemas/iso8583_fields.json` | **手動** | フィールド定義の唯一の真実 |
| `app/src/.../core/models/mti.py` | **手動** | MTI enum の唯一の真実 |
| `app/data/schemas/openapi_base.yaml` | **手動** | エンドポイント・エラースキーマ等の静的定義（生成スクリプトへの入力） |
| `doc/api/openapi.yaml` | **自動生成** | 最終的な OpenAPI 仕様（コミット対象） |
| `app/scripts/code_generator/generate_openapi.py` | **手動** | 生成スクリプト |

### 8.3 自動生成されるセクション

`openapi_base.yaml` の `x-auto-generated` プレースホルダーが以下に置換される。

| 識別子 | ソース | 生成内容 |
|--------|-------|---------|
| `MessageFields` | `iso8583_fields.json` | 各フィールドのプロパティ（minLength/maxLength/pattern）を持つ明示的スキーマ |
| `FieldsExample` | `iso8583_fields.json` | `GET /api/v1/fields` のレスポンス example |
| `MtiTypesExample` | `mti.py` の enum + `.description` | `GET /api/v1/mti-types` のレスポンス example |

**生成しないと判断したセクション:**

| セクション | 理由 |
|-----------|------|
| `FieldDefinition.data_type` enum | `[n,a,an,ans,b]` は ISO 8583 標準全体を表す。現在の設定値（`n`,`an`のみ）とは別概念のためハードコードが正しい |
| `ErrorCode` enum | `INVALID_FORMAT` 等、例外クラスと 1:1 対応しない API 固有の概念。ソースが曖昧 |
| リクエスト例の `fields` 値 | ドキュメント作者の編集上の選択であり、データから導出できない |

### 8.4 MessageFields の型導出ルール

| iso8583_fields.json | OpenAPI スキーマ |
|--------------------|----------------|
| `len_type: 0` | `minLength == maxLength`（固定長） |
| `len_type: 2` | `minLength: 1`（可変長） |
| `data_type: "n"` | `pattern: ^[0-9]{N}$` or `^[0-9]{1,N}$` |
| `data_type: "a"` | `pattern: ^[A-Za-z]{N}$` |
| `data_type: "an"` | `pattern: ^[A-Za-z0-9]{N}$` |
| `data_type: "ans"` | pattern なし（文字セット広すぎるため） |
| `additionalProperties: false` | 未定義フィールド名をリクエスト時に拒否 |

### 8.5 再生成コマンド

```bash
cd iso8583_message_generator/app

# フィールドを追加・変更した場合は以下を両方実行
python scripts/code_generator/generate_models.py   # Pydantic モデル
python scripts/code_generator/generate_openapi.py  # OpenAPI スキーマ
```

### 8.6 OpenAPI ドキュメント UI

FastAPI 起動後、以下 URL で確認できる。

| URL | 説明 |
|-----|------|
| `/docs` | Swagger UI |
| `/redoc` | ReDoc UI |
| `/openapi.json` | OpenAPI スキーマ（JSON、実装後はこちらが正） |

---

## 9. API テスト戦略

> システム全体のテスト方針・カバレッジ評価・ロードマップは `doc/test_strategy.md` を参照。
> 本節は **REST API 層固有** のテスト計画を記述する。

### 9.1 基本方針

- FastAPI `TestClient`（httpx ベース）を使用。
- ユースケース層は pytest-mock で差し替え、**Presentation 層の責務のみ**を検証。
  - 検証対象: スキーマ変換・バリデーション・エラーハンドリング・HTTP ステータスコード
- 実 Adapter を使った結合テストは `tests/integration/test_api_integration.py` に分離。

### 9.2 テストファイル配置

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
└── test_api_contract.py       # schemathesis 契約テスト（API 実装後）
```

### 9.3 ルーターユニットテスト

#### `test_health.py`

| テストID | テスト内容 | 期待結果 |
|---------|-----------|---------|
| API-HLT-01 | `GET /api/v1/health` | 200, `{"status": "ok"}` |

#### `test_metadata.py`

| テストID | テスト内容 | 検証観点 |
|---------|-----------|---------|
| API-META-01 | `GET /api/v1/fields` → 200 | フィールド数が JSON スキーマと一致 |
| API-META-02 | 各フィールドが `field_id`, `name`, `description`, `data_type`, `len_type`, `max_len` を持つ | `FieldDefinition` スキーマ準拠 |
| API-META-03 | `GET /api/v1/mti-types` → 200 | `versions`/`classes`/`functions`/`origins` の 4 キー存在 |
| API-META-04 | 各エントリが `code`, `description` を持つ | `MtiCodeEntry` スキーマ準拠 |
| API-META-05 | `versions` の件数が `MtiVersion` enum 数と一致 | `mti.py` との同期保証 |

#### `test_generate_endpoint.py`

| テストID | テスト内容 | 期待結果 |
|---------|-----------|---------|
| API-GEN-01 | 正常リクエスト（全フィールド, `output_format: hex`） | 200, `encoded_message` が hex 文字列 |
| API-GEN-02 | `output_format: base64` | 200, Base64 文字列 |
| API-GEN-03 | フィールド省略（MTI のみ） | 200 |
| API-GEN-04 | `mti` 形式不正（3桁） | 422, パターン違反 |
| API-GEN-05 | `mti` 未定義クラス（`"0900"`） | 400, `INVALID_MTI` |
| API-GEN-06 | 未定義フィールド名（`unknown_field: "xxx"`） | 422, `additionalProperties` 違反 |
| API-GEN-07 | フィールド値が maxLength 超過 | 422, `max_length` 違反 |
| API-GEN-08 | 固定長フィールドの長さ不一致 | 422, `min/max_length` 違反 |
| API-GEN-09 | `mti` キー欠落 | 422, required フィールド欠落 |
| API-GEN-10 | エンコード失敗（アダプターエラー） | 400, `MESSAGE_ENCODE_ERROR` |

#### `test_parse_endpoint.py`

| テストID | テスト内容 | 期待結果 |
|---------|-----------|---------|
| API-PAR-01 | 正常 hex 入力 | 200, `mti`・`fields`・`mti_description` を含む |
| API-PAR-02 | 正常 base64 入力 | 200 |
| API-PAR-03 | `mti_description` の全 4 キー（version/class/function/origin）存在 | `MtiDescription` スキーマ準拠 |
| API-PAR-04 | 不正な hex 文字列（非 16 進数文字含む） | 400, `INVALID_FORMAT` |
| API-PAR-05 | 奇数長の hex 文字列 | 400, `INVALID_FORMAT` |
| API-PAR-06 | デコード失敗（破損データ） | 400, `MESSAGE_DECODE_ERROR` |
| API-PAR-07 | `encoded_message` キー欠落 | 422 |

### 9.4 OpenAPI スキーマ有効性テスト

**配置:** `tests/scripts/test_openapi_validity.py`
**依存:** `openapi-spec-validator`

| テストID | テスト内容 |
|---------|-----------|
| OA-VAL-01 | 生成された `openapi.yaml` が有効な OpenAPI 3.1.0 スキーマ |
| OA-VAL-02 | 全 `$ref` 参照が解決可能 |
| OA-VAL-03 | 全エンドポイントに `operationId` が存在 |
| OA-VAL-04 | `MessageFields` に `additionalProperties: false` が存在 |
| OA-VAL-05 | `MessageFields.properties` 数が JSON スキーマのフィールド数と一致 |

### 9.5 契約テスト

**配置:** `tests/contract/test_api_contract.py`（API 実装後）
**依存:** `schemathesis`

```python
import schemathesis

schema = schemathesis.from_file("doc/api/openapi.yaml", base_url="http://testserver")

@schema.parametrize()
def test_api_contract(case):
    """OpenAPI スキーマに基づいて自動生成されたリクエストで全エンドポイントを検証。"""
    response = case.call()
    case.validate_response(response)
```

| テストID | 検証内容 |
|---------|---------|
| CT-01 | 全エンドポイントのレスポンスが OpenAPI スキーマの型定義に準拠 |
| CT-02 | エラーレスポンスが `ErrorResponse` スキーマに準拠 |
| CT-03 | バリデーションエラーレスポンスが `ValidationErrorResponse` スキーマに準拠 |
