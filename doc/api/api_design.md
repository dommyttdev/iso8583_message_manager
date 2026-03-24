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
cd iso8583_message_manager
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
| `src/iso8583_manager/data/schemas/generated/openapi.yaml` | **自動生成** | 最終的な OpenAPI 仕様（コミット対象） |
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
cd iso8583_message_manager

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

> テスト計画の詳細は `doc/tests/api_test_plan.md` を参照。
> システム全体のテスト方針・カバレッジ評価・ロードマップは `doc/tests/test_strategy.md` を参照。

