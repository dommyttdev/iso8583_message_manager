# テスト戦略

QA マネージャーの視点から、プロジェクト全体のテスト設計を体系化したドキュメント。
CLI 層・REST API 層・パッケージング基盤のすべてを対象とする。

> **REST API 固有のテスト計画**（ルーターテスト・契約テスト等）は `doc/api/api_design.md` §9 を参照。
> **UAT 実施記録**は `doc/tests/uat_test_plan.md` を参照。

---

## 1. テスト方針

### 1.1 基本原則

| 原則 | 内容 |
|------|------|
| **TDD** | Red → Green → Refactor を厳守 |
| **ピラミッド構造** | Unit > Integration > E2E の比率を維持 |
| **単一責任** | テストは 1 つの関心事だけを検証する |
| **独立性** | テスト間に依存関係を持たせない |
| **再現性** | 外部依存（ファイルシステム・ネットワーク）はモックまたは Fixture で制御 |

### 1.2 品質ゲート（CI 通過条件）

```
ラインカバレッジ  ≥ 90%
ブランチカバレッジ ≥ 85%
全テスト PASS
mypy エラー 0
ruff エラー 0
```

---

## 2. テストピラミッド（目標比率）

```
              ┌────────────────────────────────┐
              │         E2E / UAT              │  目標: 5%
              │  実インフラで全経路を通す        │
              └────────────────────────────────┘
         ┌──────────────────────────────────────────┐
         │         Integration Tests               │  目標: 20%
         │  レイヤー間の結合・実ファイル使用         │
         └──────────────────────────────────────────┘
    ┌──────────────────────────────────────────────────────┐
    │                  Unit Tests                         │  目標: 75%
    │  モック使用・単一クラス/関数の責務のみ検証            │
    └──────────────────────────────────────────────────────┘
```

---

## 3. 現行カバレッジ評価

### 3.1 レイヤー別評価

| レイヤー | テスト数 | 評価 | 備考 |
|---------|---------|------|------|
| Core (MTI) | ~45 | ✅ 良好 | enum 全値・境界値・不変性を網羅 |
| Core (Iso8583MessageModel) | 11 | ✅ 良好 | MODEL-01〜11 全 PASS |
| Core (パッケージデータ) | 5 | ✅ 良好 | importlib.resources 経由のアクセスを検証 |
| Use Cases | 12 + 3 | ✅ 良好 | モック + 実アダプター結合テスト完備 |
| Infrastructure | 6 + 7 | ✅ 良好 | 結合テスト + 境界値テスト（INF-BV-01〜07）完備 |
| Presentation / CLI | ~52 | ✅ 良好 | 全コマンド・全出力形式・全エラーパスを網羅 |
| Presentation / CLI（統合エントリポイント） | 9 | ✅ 良好 | `__main__.py` の全サブコマンドを検証 |
| Presentation / API | ~16 | ✅ 良好 | FastAPI ルーター（health/metadata/generate/parse）完備 |
| Integration | 14 | ✅ 良好 | CLI 往復・実スペックファイル使用 |
| Code Generators | 11 + 4 | ✅ 良好 | generate_openapi.py・generate_models.py テスト完備 |
| OpenAPI バリデーション | 5 | ✅ 良好 | OA-VAL-01〜05 全 PASS |
| 契約テスト | 1 | ⚠️ 部分的 | schemathesis の API 変更により 1 件失敗中（既知）|
| パッケージメタデータ | 5 | ✅ 良好 | optional-dependencies 構造・エントリポイントを検証 |

### 3.2 既知の未解決事項

| # | 内容 | リスク | 対応方針 |
|---|------|-------|---------|
| 1 | `test_api_contract.py` が `schemathesis.from_path()` の API 変更で失敗 | 低（契約テスト自体は設計済み） | schemathesis を最新バージョン対応に更新 |

---

## 4. テスト種別ごとの詳細計画

### 4.1 コード生成スクリプトのテスト ✅ 完了

**配置:** `tests/scripts/test_generate_openapi.py` / `tests/scripts/test_generate_models.py`

#### `test_generate_openapi.py`

| テストID | テスト内容 | 検証観点 | 状態 |
|---------|-----------|---------|------|
| GEN-OA-01 | 標準の JSON から MessageFields を生成 | properties にフィールド名がすべて存在する | ✅ |
| GEN-OA-02 | 可変長フィールド（len_type=2）の制約生成 | `minLength: 1`, `maxLength: N`, `pattern: ^[0-9]{1,N}$` | ✅ |
| GEN-OA-03 | 固定長フィールド（len_type=0）の制約生成 | `minLength == maxLength`, `pattern: ^[0-9]{N}$` | ✅ |
| GEN-OA-04 | `additionalProperties: false` が生成される | 未定義フィールドを拒否する | ✅ |
| GEN-OA-05 | `ans` 型フィールドに pattern が生成されない | 文字セットが広すぎるため省略が正しい | ✅ |
| GEN-OA-06 | FieldsExample が JSON の全フィールドを含む | フィールド数と ID が一致する | ✅ |
| GEN-OA-07 | MtiTypesExample が mti.py の全 enum を含む | versions=4, classes=8, functions=7, origins=6 | ✅ |
| GEN-OA-08 | MtiTypesExample の description が mti.py の `.description` と一致 | 日本語説明の乖離を防ぐ | ✅ |
| GEN-OA-09 | フィールドを JSON に追加して再生成 → openapi.yaml に反映 | 単一真実の連携検証 | ✅ |
| GEN-OA-10 | openapi_base.yaml が存在しない場合 → sys.exit(1) | エラーハンドリング | ✅ |
| GEN-OA-11 | 生成された openapi.yaml が有効な OpenAPI 3.1.0 | `openapi-spec-validator` で検証 | ✅ |

#### `test_generate_models.py`

| テストID | テスト内容 | 状態 |
|---------|-----------|------|
| GEN-MD-01 | 標準の JSON から Pydantic クラスを生成 → クラス名・フィールド名の存在確認 | ✅ |
| GEN-MD-02 | `field_mapping` の完全性検証（JSON の全フィールド ID が含まれる） | ✅ |
| GEN-MD-03 | 生成ファイルが Python として構文エラーなし（`ast.parse` で検証） | ✅ |
| GEN-MD-04 | JSON ファイル不在時に適切なエラー | ✅ |

---

### 4.2 Iso8583MessageModel のユニットテスト ✅ 完了

**配置:** `tests/core/test_iso_models.py`

| テストID | テスト内容 | 検証観点 | 状態 |
|---------|-----------|---------|------|
| MODEL-01 | 全フィールド省略可能（すべて None でインスタンス化） | Optional 定義の確認 | ✅ |
| MODEL-02 | 各フィールドの最大長ちょうどで正常 | Pydantic max_length 境界値 | ✅ |
| MODEL-03 | 各フィールドの最大長+1で ValidationError | 上限超過の検出 | ✅ |
| MODEL-04 | 可変長フィールド（PAN）の最小長 1 で正常 | min_length=1 の確認 | ✅ |
| MODEL-05 | 可変長フィールド（PAN）の空文字列で ValidationError | min_length の検出 | ✅ |
| MODEL-06 | `to_iso_dict()` — 設定フィールドのみを返す | exclude_unset 動作 | ✅ |
| MODEL-07 | `to_iso_dict()` — None フィールドを含まない | exclude_none 動作 | ✅ |
| MODEL-08 | `to_iso_dict()` — キーが ISO フィールド番号文字列 | `{"2": "...", "4": "..."}` 形式 | ✅ |
| MODEL-09 | `from_iso_dict()` — 全フィールドの往復変換 | encode → decode の一致 | ✅ |
| MODEL-10 | `from_iso_dict()` — 未知のキー（"999"）は無視 | KeyError 非発生 | ✅ |
| MODEL-11 | `field_mapping` が JSON の全フィールド数と一致 | スキーマとモデルの同期 | ✅ |

---

### 4.3 Infrastructure の境界値テスト ✅ 完了

**配置:** `tests/infrastructure/test_wrapper_boundary.py`

| テストID | テスト内容 | 検証観点 | 状態 |
|---------|-----------|---------|------|
| INF-BV-01 | PAN 1桁（最小）のエンコード→デコード往復 | 可変長最小値 | ✅ |
| INF-BV-02 | PAN 19桁（最大）のエンコード→デコード往復 | 可変長最大値 | ✅ |
| INF-BV-03 | amount_transaction 12桁（固定長ちょうど）のエンコード | 固定長境界値 | ✅ |
| INF-BV-04 | 1 フィールドのみ指定（他は None）のエンコード→デコード | 疎なメッセージ | ✅ |
| INF-BV-05 | 全フィールド None のエンコード（MTI のみ） | 最小メッセージ | ✅ |
| INF-BV-06 | 全フィールド指定のエンコード→デコード往復 | 密なメッセージ | ✅ |
| INF-BV-07 | response_code が `an` 型（英数混在）のエンコード | データ型検証 | ✅ |

---

### 4.4 REST API 層のテスト ✅ 完了

> 詳細なテストケース一覧（API-HLT / API-META / API-GEN / API-PAR / OA-VAL / CT 系）は
> `doc/api/api_design.md` §9 を参照。

**配置:** `tests/presentation/api/`, `tests/scripts/test_openapi_validity.py`, `tests/contract/`

---

### 4.5 Use Cases の実結合テスト ✅ 完了

**配置:** `tests/use_cases/test_message_generation_with_real_adapter.py`

| テストID | テスト内容 | 状態 |
|---------|-----------|------|
| UC-RA-01 | 実アダプターで GenerateMessageUseCase を実行 → bytearray を返す | ✅ |
| UC-RA-02 | 実アダプターで ParseMessageUseCase を実行 → Mti と Iso8583MessageModel を返す | ✅ |
| UC-RA-03 | 生成→解析の往復で全フィールド値が一致 | ✅ |

---

### 4.6 パッケージデータ・エントリポイントのテスト ✅ 完了（新規）

**背景:** `app/` 中間層除去・`importlib.resources` 対応・統合エントリポイント追加に伴い追加。

#### `tests/core/test_package_data.py`

| テストID | テスト内容 | 状態 |
|---------|-----------|------|
| PD-01 | `importlib.resources` で `iso8583_fields.json` にアクセスできる | ✅ |
| PD-02 | `iso8583_fields.json` が有効な JSON（dict 形式）である | ✅ |
| PD-03 | 各フィールド定義に必須キーが含まれる | ✅ |
| PD-04 | `container.py` のデフォルトスペックパスがパッケージ内に解決される | ✅ |
| PD-05 | デフォルトスペックパスでユースケースが正常生成される | ✅ |

#### `tests/presentation/test_main.py`

| テストID | テスト内容 | 状態 |
|---------|-----------|------|
| MAIN-01 | `iso8583_manager.__main__` がインポートできる | ✅ |
| MAIN-02 | `main()` 関数が存在する | ✅ |
| MAIN-03 | Typer `app` オブジェクトが存在する | ✅ |
| MAIN-04 | 引数なしでヘルプ（cli/api/web）が表示される | ✅ |
| MAIN-05 | `--help` でサブコマンド一覧が表示される | ✅ |
| MAIN-06 | `cli --help` で既存コマンドが表示される | ✅ |
| MAIN-07 | `api --help` で `--host`/`--port` が表示される | ✅ |
| MAIN-08 | `web --help` で `--host`/`--port` が表示される | ✅ |
| MAIN-09 | uvicorn 未インストール時に有用なエラーメッセージが表示される | ✅ |

#### `tests/test_package_metadata.py`

| テストID | テスト内容 | 状態 |
|---------|-----------|------|
| PM-01 | パッケージ名が `iso8583_manager` である | ✅ |
| PM-02 | エントリポイントが `iso8583-msg` 単一（旧 `iso8583-msg-cli` は削除済み）| ✅ |
| PM-03 | `[api]` optional-dependencies に fastapi が含まれる | ✅ |
| PM-04 | `[web]` optional-dependencies に fastapi が含まれる | ✅ |
| PM-05 | fastapi / uvicorn がコア必須依存に含まれない | ✅ |

---

## 5. テストファイル配置（現状）

```
tests/
├── core/
│   ├── test_mti.py                                        ✅ ~45 件
│   ├── test_iso_models.py                                 ✅ MODEL-01〜11
│   └── test_package_data.py                              ✅ PD-01〜05（新規）
├── use_cases/
│   ├── test_message_generation.py                         ✅
│   ├── test_message_parsing.py                            ✅
│   └── test_message_generation_with_real_adapter.py       ✅ UC-RA-01〜03
├── infrastructure/
│   ├── test_wrapper.py                                    ✅
│   ├── test_wrapper_errors.py                             ✅
│   └── test_wrapper_boundary.py                           ✅ INF-BV-01〜07
├── presentation/
│   ├── test_container.py                                  ✅
│   ├── test_error_handler.py                              ✅
│   ├── test_fields_command.py                             ✅
│   ├── test_generate_command.py                           ✅
│   ├── test_mti_types_command.py                          ✅
│   ├── test_parse_command.py                              ✅
│   ├── test_main.py                                       ✅ MAIN-01〜09（新規）
│   └── api/
│       ├── test_health.py                                 ✅ API-HLT
│       ├── test_metadata.py                               ✅ API-META
│       ├── test_generate_endpoint.py                      ✅ API-GEN
│       └── test_parse_endpoint.py                         ✅ API-PAR
├── scripts/
│   ├── test_generate_models.py                            ✅ GEN-MD-01〜04
│   ├── test_generate_openapi.py                           ✅ GEN-OA-01〜11
│   └── test_openapi_validity.py                           ✅ OA-VAL-01〜05
├── contract/
│   └── test_api_contract.py                               ⚠️ schemathesis API 変更で失敗中
├── integration/
│   ├── test_cli_integration.py                            ✅
│   └── test_message_generation_integration.py             ✅
└── test_package_metadata.py                               ✅ PM-01〜05（新規）
```

---

## 6. テスト実行コマンド

```bash
cd iso8583_message_manager

# 全テスト
pytest

# カバレッジ付き
pytest --cov=iso8583_manager --cov-report=term-missing

# レイヤー別
pytest tests/core/ -v
pytest tests/use_cases/ -v
pytest tests/infrastructure/ -v
pytest tests/presentation/ -v
pytest tests/scripts/ -v

# API 層のみ
pytest tests/presentation/api/ -v

# 契約テスト（schemathesis 更新後）
pytest tests/contract/ -v

# パッケージング関連
pytest tests/core/test_package_data.py tests/test_package_metadata.py -v
```

---

## 7. 実施ロードマップ

| フェーズ | 対象 | 優先度 | 状態 |
|---------|------|-------|------|
| **Phase 1** | `test_iso_models.py` 追加 | P0 | ✅ 完了 |
| **Phase 1** | `test_generate_openapi.py` 追加 | P0 | ✅ 完了 |
| **Phase 2** | `test_wrapper_boundary.py` 追加 | P1 | ✅ 完了 |
| **Phase 2** | `test_openapi_validity.py` 追加 | P1 | ✅ 完了 |
| **Phase 3** | API 層実装 + `tests/presentation/api/` 追加 | P1 | ✅ 完了 |
| **Phase 3** | `tests/contract/` 追加 | P1 | ✅ 完了（schemathesis 更新待ち）|
| **Phase 4** | `test_generate_models.py` 追加 | P2 | ✅ 完了 |
| **Phase 4** | Use Cases 実結合テスト追加 | P2 | ✅ 完了 |
| **Phase 5** | パッケージング基盤テスト追加 | — | ✅ 完了（新規）|
| **次期課題** | schemathesis 最新版対応（契約テスト修復） | 低 | 未着手 |
