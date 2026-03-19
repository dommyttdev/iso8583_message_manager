# テスト戦略

QA マネージャーの視点から、プロジェクト全体のテスト設計を体系化したドキュメント。
CLI 層（既存）と REST API 層（設計済み）の両方を対象とする。

> **REST API 固有のテスト計画**（ルーターテスト・契約テスト等）は `doc/api/api_design.md` §9 を参照。

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

| レイヤー | テスト数 | 評価 | 理由 |
|---------|---------|------|------|
| Core (MTI) | ~45 | ✅ 良好 | enum 全値・境界値・不変性を網羅 |
| Core (Iso8583MessageModel) | **0** | ❌ 欠落 | Pydantic モデルのユニットテストが存在しない |
| Use Cases | 12 | ⚠️ 不足 | モックのみ。ハッピーパス寄り |
| Infrastructure | 6 | ⚠️ 不足 | 結合テスト 1 件 + エラーモック 4 件のみ |
| Presentation / CLI | ~52 | ✅ 良好 | 全コマンド・全出力形式・全エラーパスを網羅 |
| Presentation / **API** | **0** | ❌ 欠落 | FastAPI ルーター未実装のため当然だが計画が必要 |
| Integration | 14 | ✅ 良好 | CLI 往復・実スペックファイル使用 |
| **Code Generators** | **0** | ❌ 欠落 | generate_models.py / generate_openapi.py にテストなし |

### 3.2 重大なギャップ（リスク順）

| # | ギャップ | リスク | 優先度 |
|---|---------|-------|--------|
| 1 | `generate_openapi.py` のテスト欠落 | スクリプトが壊れても openapi.yaml が無言で不正になる | **P0** |
| 2 | `Iso8583MessageModel` のユニットテスト欠落 | フィールド制約（min/maxLength・pattern）が機能するか保証なし | **P0** |
| 3 | API 層のテスト計画なし | FastAPI 実装後に品質保証の基盤がない | **P1** |
| 4 | Infrastructure の境界値テスト不足 | フィールド長の上限/下限での挙動が未検証 | **P1** |
| 5 | OpenAPI スキーマ有効性の検証なし | 生成された openapi.yaml が仕様違反でも検出できない | **P1** |
| 6 | `generate_models.py` のテスト欠落 | iso_models.py が誤生成されても検出できない | **P2** |
| 7 | Use Cases の実結合テスト欠落 | モックと実 Adapter の乖離リスク | **P2** |

---

## 4. テスト種別ごとの詳細計画

### 4.1 【P0】コード生成スクリプトのテスト

**配置:** `tests/scripts/test_generate_openapi.py` / `tests/scripts/test_generate_models.py`

#### `test_generate_openapi.py`

| テストID | テスト内容 | 検証観点 |
|---------|-----------|---------|
| GEN-OA-01 | 標準の JSON から MessageFields を生成 | properties にフィールド名がすべて存在する |
| GEN-OA-02 | 可変長フィールド（len_type=2）の制約生成 | `minLength: 1`, `maxLength: N`, `pattern: ^[0-9]{1,N}$` |
| GEN-OA-03 | 固定長フィールド（len_type=0）の制約生成 | `minLength == maxLength`, `pattern: ^[0-9]{N}$` |
| GEN-OA-04 | `additionalProperties: false` が生成される | 未定義フィールドを拒否する |
| GEN-OA-05 | `ans` 型フィールドに pattern が生成されない | 文字セットが広すぎるため省略が正しい |
| GEN-OA-06 | FieldsExample が JSON の全フィールドを含む | フィールド数と ID が一致する |
| GEN-OA-07 | MtiTypesExample が mti.py の全 enum を含む | versions=4, classes=8, functions=7, origins=6 |
| GEN-OA-08 | MtiTypesExample の description が mti.py の `.description` と一致 | 日本語説明の乖離を防ぐ |
| GEN-OA-09 | フィールドを JSON に追加して再生成 → openapi.yaml に反映 | 単一真実の連携検証 |
| GEN-OA-10 | openapi_base.yaml が存在しない場合 → sys.exit(1) | エラーハンドリング |
| GEN-OA-11 | 生成された openapi.yaml が有効な OpenAPI 3.1.0 | `openapi-spec-validator` で検証 |

#### `test_generate_models.py`

| テストID | テスト内容 |
|---------|-----------|
| GEN-MD-01 | 標準の JSON から Pydantic クラスを生成 → クラス名・フィールド名の存在確認 |
| GEN-MD-02 | `field_mapping` の完全性検証（JSON の全フィールド ID が含まれる） |
| GEN-MD-03 | 生成ファイルが Python として構文エラーなし（`ast.parse` で検証） |
| GEN-MD-04 | JSON ファイル不在時に適切なエラー |

---

### 4.2 【P0】Iso8583MessageModel のユニットテスト

**配置:** `tests/core/test_iso_models.py`

| テストID | テスト内容 | 検証観点 |
|---------|-----------|---------|
| MODEL-01 | 全フィールド省略可能（すべて None でインスタンス化） | Optional 定義の確認 |
| MODEL-02 | 各フィールドの最大長ちょうどで正常 | Pydantic max_length 境界値 |
| MODEL-03 | 各フィールドの最大長+1で ValidationError | 上限超過の検出 |
| MODEL-04 | 可変長フィールド（PAN）の最小長 1 で正常 | min_length=1 の確認 |
| MODEL-05 | 可変長フィールド（PAN）の空文字列で ValidationError | min_length の検出 |
| MODEL-06 | `to_iso_dict()` — 設定フィールドのみを返す | exclude_unset 動作 |
| MODEL-07 | `to_iso_dict()` — None フィールドを含まない | exclude_none 動作 |
| MODEL-08 | `to_iso_dict()` — キーが ISO フィールド番号文字列 | `{"2": "...", "4": "..."}` 形式 |
| MODEL-09 | `from_iso_dict()` — 全フィールドの往復変換 | encode → decode の一致 |
| MODEL-10 | `from_iso_dict()` — 未知のキー（"999"）は無視 | KeyError 非発生 |
| MODEL-11 | `field_mapping` が JSON の全フィールド数と一致 | スキーマとモデルの同期 |

---

### 4.3 【P1】Infrastructure の境界値テスト

**配置:** `tests/infrastructure/test_wrapper_boundary.py`

| テストID | テスト内容 | 検証観点 |
|---------|-----------|---------|
| INF-BV-01 | PAN 1桁（最小）のエンコード→デコード往復 | 可変長最小値 |
| INF-BV-02 | PAN 19桁（最大）のエンコード→デコード往復 | 可変長最大値 |
| INF-BV-03 | amount_transaction 12桁（固定長ちょうど）のエンコード | 固定長境界値 |
| INF-BV-04 | 1 フィールドのみ指定（他は None）のエンコード→デコード | 疎なメッセージ |
| INF-BV-05 | 全フィールド None のエンコード（MTI のみ） | 最小メッセージ |
| INF-BV-06 | 全フィールド指定のエンコード→デコード往復 | 密なメッセージ |
| INF-BV-07 | response_code が `an` 型（英数混在）のエンコード | データ型検証 |

---

### 4.4 【P1】REST API 層のテスト

> 詳細なテストケース一覧（API-HLT / API-META / API-GEN / API-PAR / OA-VAL / CT 系）は
> `doc/api/api_design.md` §9 を参照。

**前提:** FastAPI + `presentation/api/` 実装後に追加。
**配置:** `tests/presentation/api/`, `tests/scripts/test_openapi_validity.py`, `tests/contract/`

---

### 4.5 【P2】Use Cases の実結合テスト

**配置:** `tests/use_cases/test_message_generation_with_real_adapter.py`

モックを使わず実 `PyIso8583Adapter` を注入したテスト（現行統合テストより細粒度）。

| テストID | テスト内容 |
|---------|-----------|
| UC-RA-01 | 実アダプターで GenerateMessageUseCase を実行 → bytearray を返す |
| UC-RA-02 | 実アダプターで ParseMessageUseCase を実行 → Mti と Iso8583MessageModel を返す |
| UC-RA-03 | 生成→解析の往復で全フィールド値が一致 |

---

## 5. テストファイル配置計画

```
tests/
├── core/
│   ├── test_mti.py                              ✅ 既存（良好）
│   └── test_iso_models.py                       ❌ 新規追加（P0）
├── use_cases/
│   ├── test_message_generation.py               ✅ 既存
│   ├── test_message_parsing.py                  ✅ 既存
│   └── test_message_generation_with_real_adapter.py  ❌ 新規追加（P2）
├── infrastructure/
│   ├── test_wrapper.py                          ✅ 既存
│   ├── test_wrapper_errors.py                   ✅ 既存
│   └── test_wrapper_boundary.py                 ❌ 新規追加（P1）
├── presentation/
│   ├── test_container.py                        ✅ 既存
│   ├── test_error_handler.py                    ✅ 既存
│   ├── test_fields_command.py                   ✅ 既存
│   ├── test_generate_command.py                 ✅ 既存
│   ├── test_mti_types_command.py                ✅ 既存
│   ├── test_parse_command.py                    ✅ 既存
│   └── api/                                     ❌ 新規追加（P1 / API 実装後）
│       ├── __init__.py
│       ├── test_health.py
│       ├── test_metadata.py
│       ├── test_generate_endpoint.py
│       └── test_parse_endpoint.py
├── scripts/                                     ❌ 新規追加（P0/P1）
│   ├── __init__.py
│   ├── test_generate_models.py                  ← P2
│   ├── test_generate_openapi.py                 ← P0
│   └── test_openapi_validity.py                 ← P1
├── contract/                                    ❌ 新規追加（P1 / API 実装後）
│   ├── __init__.py
│   └── test_api_contract.py
└── integration/
    ├── test_cli_integration.py                  ✅ 既存（良好）
    └── test_message_generation_integration.py   ✅ 既存（良好）
```

---

## 6. テスト実行コマンド

```bash
cd iso8583_message_generator/app

# 全テスト
pytest

# カバレッジ付き
pytest --cov=iso8583_manager --cov-report=term-missing

# 優先度別（P0 から着手）
pytest tests/core/ tests/scripts/test_generate_openapi.py -v

# API 層のみ（実装後）
pytest tests/presentation/api/ -v

# 契約テスト（実装後）
pytest tests/contract/ -v
```

---

## 7. 実施ロードマップ

| フェーズ | 対象 | 優先度 | 完了条件 |
|---------|------|-------|---------|
| **Phase 1** | `test_iso_models.py` 追加 | P0 | MODEL-01〜11 全 PASS |
| **Phase 1** | `test_generate_openapi.py` 追加 | P0 | GEN-OA-01〜11 全 PASS |
| **Phase 2** | `test_wrapper_boundary.py` 追加 | P1 | INF-BV-01〜07 全 PASS |
| **Phase 2** | `test_openapi_validity.py` 追加 | P1 | OA-VAL-01〜05 全 PASS |
| **Phase 3** | API 層実装 + `tests/presentation/api/` 追加 | P1 | API-GEN/PAR 全 PASS |
| **Phase 3** | `tests/contract/` 追加 | P1 | CT-01〜03 全 PASS |
| **Phase 4** | `test_generate_models.py` 追加 | P2 | GEN-MD-01〜04 全 PASS |
| **Phase 4** | Use Cases 実結合テスト追加 | P2 | UC-RA-01〜03 全 PASS |
