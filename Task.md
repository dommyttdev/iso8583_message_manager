# モノレポ移行 実施計画

## 目標アーキテクチャ

```
d:/Projects/Cards/
├── packages/
│   ├── iso8583-types/     # インターフェース・モデル・例外 (実装なし)
│   └── iso8583-core/      # ユースケース・インフラ実装
├── api/                   # FastAPI サービス (独立)
├── cli/                   # CLI ツール (独立)
├── web/                   # Spring Boot Web アプリ (独立)
└── shared/
    └── openapi/           # API 契約 (api/ と web/ の境界)
```

### 依存関係

```
api/ ──→ iso8583-core ──→ iso8583-types
cli/ ──→ iso8583-core ──→ iso8583-types
web/ ──→ (HTTP のみ) ──→ api/
```

---

## フェーズ 0: 移行前確認

**目的**: 移行のベースラインを確定する

### タスク

- [ ] 現行テストが全件パスすることを確認
- [ ] カバレッジレポートを取得・記録
- [ ] 現状の `pyproject.toml` 依存関係を整理・記録
- [ ] `container.py` (Composition Root) の依存グラフを把握

### 完了条件

- pytest が全件グリーン
- カバレッジ数値が記録済み

---

## フェーズ 1: モノレポ基盤構築

**目的**: ルートディレクトリ構造を作り、既存コードを移動する

### タスク

- [ ] `d:/Projects/Cards/` 配下にディレクトリ骨格を作成
  ```
  packages/iso8583-types/src/
  packages/iso8583-core/src/
  api/src/
  cli/src/
  shared/openapi/
  ```
- [ ] 現行 `iso8583_message_manager/` を `api/` 配下へ **まるごとコピー** (移動ではなくコピーで安全に進める)
- [ ] コピー後のテストが全件パスすることを確認
- [ ] ルート `README.md` にモノレポ構造の説明を追記

### 完了条件

- `api/` 配下でテストが全件グリーン
- 元の `iso8583_message_manager/` は削除せず残す (フェーズ 3 完了まで)

---

## フェーズ 2: `iso8583-types` パッケージ抽出

**目的**: インターフェース・モデル・例外を実装なしの独立パッケージとして切り出す

### 対象ファイル (api/ から移動)

| 移動元 | 移動先 |
|--------|--------|
| `core/interfaces/iso_ports.py` | `packages/iso8583-types/src/iso8583_types/interfaces/` |
| `core/models/mti.py` | `packages/iso8583-types/src/iso8583_types/models/` |
| `core/models/generated/iso_models.py` | `packages/iso8583-types/src/iso8583_types/models/generated/` |
| `core/exceptions.py` | `packages/iso8583-types/src/iso8583_types/` |

### タスク

- [ ] `packages/iso8583-types/pyproject.toml` を作成
  - 依存: `pydantic>=2.0.0` のみ
- [ ] 対象ファイルをコピー・import パスを修正
- [ ] `packages/iso8583-types/tests/` にユニットテスト作成
- [ ] `api/` の import を `iso8583_types.*` に更新
- [ ] `api/` のテストが全件パスすることを確認

### 完了条件

- `iso8583-types` 単独で `pytest` が通る
- `api/` のテストが全件グリーン
- `iso8583-types` は `pyiso8583` に依存しない

---

## フェーズ 3: `iso8583-core` パッケージ抽出

**目的**: ユースケース・インフラ実装を独立パッケージとして切り出す

### 対象ファイル (api/ から移動)

| 移動元 | 移動先 |
|--------|--------|
| `use_cases/message_generation.py` | `packages/iso8583-core/src/iso8583_core/use_cases/` |
| `use_cases/message_parsing.py` | `packages/iso8583-core/src/iso8583_core/use_cases/` |
| `infrastructure/pyiso8583_adapter/wrapper.py` | `packages/iso8583-core/src/iso8583_core/infrastructure/` |
| `data/schemas/iso8583_fields.json` | `packages/iso8583-core/src/iso8583_core/data/schemas/` |
| `scripts/code_generator/` | `packages/iso8583-core/scripts/` |

### タスク

- [ ] `packages/iso8583-core/pyproject.toml` を作成
  - 依存: `iso8583-types` (ローカル editable), `pyiso8583>=1.0.1`
- [ ] 対象ファイルをコピー・import パスを修正
- [ ] `packages/iso8583-core/tests/` にテスト作成 (use_cases, infrastructure)
- [ ] `api/` の import を `iso8583_core.*` に更新
- [ ] `api/` の `container.py` を `iso8583_core.*` 依存に更新
- [ ] `api/` のテストが全件パスすることを確認

### 完了条件

- `iso8583-core` 単独で `pytest` が通る
- `api/` のテストが全件グリーン

---

## フェーズ 4: `api/` の独立化

**目的**: FastAPI サービスをスリムな Presentation 層のみに整理する

### 残すファイル (api/ 内)

```
api/
├── pyproject.toml          # fastapi, uvicorn, iso8583-core (local)
└── src/iso8583_api/
    ├── app.py
    ├── container.py        # Composition Root
    ├── error_handler.py
    ├── routers/
    └── schemas/
```

### タスク

- [ ] `api/pyproject.toml` を新規作成 (core/use_cases/infrastructure の import を削除)
- [ ] `api/src/iso8583_api/` として新パッケージ名に統一
- [ ] フェーズ 2〜3 で移動したファイルを api/ から削除
- [ ] `api/` 単独での起動確認 (`uvicorn`)
- [ ] `api/tests/` のテストが全件パスすることを確認
- [ ] `docker-compose.yml` に `api` サービスを追加

### 完了条件

- `api/` が `iso8583_message_manager/` を参照せず単独起動できる
- テスト全件グリーン

---

## フェーズ 5: `cli/` の独立化

**目的**: CLI ツールをスリムな Presentation 層のみに整理する

### ディレクトリ構成

```
cli/
├── pyproject.toml          # typer, rich, iso8583-core (local)
└── src/iso8583_cli/
    ├── app.py
    ├── container.py        # Composition Root
    ├── commands/
    └── formatters/
```

### タスク

- [ ] `cli/` ディレクトリを作成
- [ ] `api/` 内の `presentation/cli/` を `cli/src/iso8583_cli/` へ移動
- [ ] `cli/pyproject.toml` を作成
- [ ] `container.py` を cli/ 用に調整
- [ ] `cli/tests/` のテストが全件パスすることを確認
- [ ] `api/` から cli 関連コードを削除

### 完了条件

- `cli/` が単独で `iso8583-msg` コマンドとして動作する
- テスト全件グリーン

---

## フェーズ 6: OpenAPI 契約整備

**目的**: `api/` と `web/` の HTTP 境界を OpenAPI スペックで明確化する

### タスク

- [ ] `shared/openapi/iso8583-api.yaml` を確定版として配置
- [ ] `api/` 側の OpenAPI 自動生成スクリプトを更新 (`shared/openapi/` に出力)
- [ ] `web/` 用 OpenAPI Generator 設定ファイルを作成 (`web/openapi-generator-config.yaml`)
- [ ] `shared/openapi/` の変更が検知された際の再生成手順をドキュメント化

### 完了条件

- `shared/openapi/iso8583-api.yaml` が `api/` の実装と一致している
- Spring Boot クライアントコードが自動生成できることを確認

---

## フェーズ 6.5: `iso8583_message_manager` 残存ファイルの移行・削除

**目的**: 旧パッケージを完全に解体し、モノレポへの移行を完結させる

### 残存ファイルの移行先マッピング

| 残存ファイル | 移行先 | 備考 |
|------------|--------|------|
| `tests/core/test_iso_models.py` | `packages/iso8583-types/tests/core/` | |
| `tests/core/test_mti.py` | 削除 | `packages/iso8583-types/tests/core/test_mti.py` と重複 |
| `tests/core/test_package_data.py` | `packages/iso8583-core/tests/` | |
| `tests/infrastructure/test_wrapper*.py` (3件) | `packages/iso8583-core/tests/infrastructure/` | |
| `tests/use_cases/test_*.py` (3件) | `packages/iso8583-core/tests/use_cases/` | |
| `tests/presentation/api/test_*.py` (4件) | `api/tests/presentation/api/` | 既存と統合 |
| `tests/presentation/test_container.py` | `api/tests/` + `cli/tests/` に分割 | API/CLI それぞれの container テスト |
| `tests/presentation/test_error_handler.py` | `api/tests/` | API エラーハンドラ対象 |
| `tests/presentation/test_fields_command.py` | `cli/tests/presentation/` | |
| `tests/presentation/test_generate_command.py` | `cli/tests/presentation/` | |
| `tests/presentation/test_parse_command.py` | `cli/tests/presentation/` | |
| `tests/presentation/test_mti_types_command.py` | `cli/tests/presentation/` | |
| `tests/presentation/test_main.py` | `cli/tests/presentation/` | `__main__.py` の移行先に合わせる |
| `tests/integration/test_cli_integration.py` | `cli/tests/integration/` | |
| `tests/integration/test_message_generation_integration.py` | `packages/iso8583-core/tests/integration/` | |
| `tests/scripts/test_generate_models.py` | `packages/iso8583-core/tests/scripts/` | |
| `tests/scripts/test_generate_openapi.py` | `packages/iso8583-core/tests/scripts/` | |
| `tests/scripts/test_openapi_validity.py` | `api/tests/contract/` | OpenAPI 整合性検証 |
| `tests/contract/test_api_contract.py` | `api/tests/contract/` と重複のため削除 | |
| `tests/test_package_metadata.py` | 削除 | 旧パッケージメタデータのテスト |
| `scripts/code_generator/generate_models.py` | `packages/iso8583-core/scripts/` | パス定義を更新 |
| `scripts/code_generator/generate_openapi.py` | `packages/iso8583-core/scripts/` | パス定義を更新 |
| `src/iso8583_manager/__main__.py` | `cli/src/iso8583_cli/__main__.py` | `iso8583-msg` エントリポイントとして統合 |
| `doc/` (全8件) | モノレポルート `doc/` | git mv で履歴保持 |
| `README.md` | モノレポルート `README.md` | git mv で履歴保持 |

### 削除対象 (移行不要)

| ファイル | 理由 |
|---------|------|
| `src/iso8583_manager/` 全 `__init__.py` | 空ファイル、旧パッケージの残骸 |
| `src/iso8583_manager/presentation/container.py` | `api/` と `cli/` にコピー済み |
| `src/iso8583_manager/data/schemas/generated/openapi.yaml` | 新パスに生成済み |
| `pyproject.toml` | 各パッケージに分散済み |
| `iso8583_message_manager/` ディレクトリ全体 | 移行完了後に削除 |

### タスク

- [ ] テストを各パッケージへ `git mv` で移動・インポートパス修正
- [ ] `scripts/` を `packages/iso8583-core/scripts/` へ `git mv`
- [ ] `doc/` をモノレポルートへ `git mv`
- [ ] `README.md` をモノレポルートへ `git mv`
- [ ] `src/iso8583_manager/__main__.py` を `cli/` へ移動
- [ ] 各パッケージのテストが全件パスすることを確認
- [ ] `iso8583_message_manager/` を削除

### 完了条件

- `iso8583_message_manager/` ディレクトリが存在しない
- 全パッケージのテストが引き続き全件グリーン
- `scripts/` がモノレポルート直下またはコア配下で動作する

---

## フェーズ 7: `web/` Spring Boot 新規作成

**目的**: 一括生成・ストレステスト機能を持つ Web アプリを構築する

### ディレクトリ構成

```
web/
├── build.gradle
├── settings.gradle
├── openapi-generator-config.yaml
└── src/main/java/.../
    ├── client/           # 自動生成 API クライアント (iso8583-api)
    ├── batch/            # 一括メッセージ生成ロジック
    ├── stress/           # ストレステスト機能
    └── web/              # コントローラ・ビュー
```

### タスク

- [ ] Spring Boot 4 プロジェクト雛形作成 (Gradle)
- [ ] OpenAPI Generator で `iso8583-api` クライアントコードを自動生成
- [ ] `api/` ヘルスチェックとの疎通確認テスト作成
- [ ] 一括生成ユースケースの設計・実装
- [ ] ストレステスト機能の設計・実装
- [ ] `docker-compose.yml` に `web` サービスを追加

### 完了条件

- Spring Boot から `api/` を呼び出して ISO 8583 メッセージを生成できる
- 一括生成・ストレステストの基本機能が動作する

---

## フェーズ 8: インフラ整備

**目的**: 全サービスを一括で起動・管理できる環境を整える

### タスク

- [ ] `docker-compose.yml` を完成させる
  - `api/` サービス
  - `web/` サービス
  - サービス間の依存関係設定 (`depends_on`)
- [ ] ルート `Makefile` または `justfile` を作成
  - `make up` — 全サービス起動
  - `make test` — 全パッケージテスト
  - `make lint` — 全パッケージ lint
- [ ] CI 設定 (GitHub Actions)
  - packages/iso8583-types, packages/iso8583-core, api/, cli/ の並列テスト
  - web/ のビルド・テスト

### 完了条件

- `docker-compose up` で全サービスが起動する
- CI が全フェーズをカバーしている

---

## 移行中の安全策

- **フェーズごとにテスト全件グリーン**を確認してから次へ進む
- 元の `iso8583_message_manager/` はフェーズ 5 完了まで削除しない
- 各フェーズ完了時にコミットを作成する

## フェーズ完了見通し

| フェーズ | 内容 | 規模 |
|---------|------|------|
| 0 | 移行前確認 | 小 |
| 1 | モノレポ基盤 | 小 |
| 2 | iso8583-types 抽出 | 中 |
| 3 | iso8583-core 抽出 | 中 |
| 4 | api/ 独立化 | 中 |
| 5 | cli/ 独立化 | 小 |
| 6 | OpenAPI 契約 | 小 |
| 7 | web/ 新規作成 | 大 |
| 8 | インフラ整備 | 中 |
