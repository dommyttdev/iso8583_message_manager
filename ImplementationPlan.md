# 実装計画: パッケージ構成リファクタリング

## 目的

パッケージ配布を見据えた適切なプロジェクト構成への移行。
`app/` 中間ディレクトリの除去、データファイルのパッケージ内移動、
統合エントリポイントの作成、依存関係の分割を行う。

## 対象外

- Step 5（`presentation/web/` スケルトン作成）はスキップ

---

## Step 1: `app/` 層の除去

### 目標
`pyproject.toml` をリポジトリルートに配置し、`pip install git+...` で直接インストール可能にする。

### TDD サイクル

**Red フェーズ（ベースライン確認）**
- 現在の全テストが `app/` 配下でパスすることを確認する

**Green フェーズ（ファイル移動）**
- `app/src/` → `src/`
- `app/tests/` → `tests/`
- `app/data/` → `data/`（Step 2 で `src/` 内に移動）
- `app/scripts/` → `scripts/`
- `app/pyproject.toml` → `pyproject.toml`

**Refactor フェーズ**
- `app/` ディレクトリを削除
- 全テストがリポジトリルートから実行できることを確認

### 変更ファイル
- `pyproject.toml`（パス更新不要、構造は同一）

---

## Step 2+3: `data/` を `src/iso8583_manager/data/` に移動 + `importlib.resources` 対応

### 目標
インストール後のパッケージでもスペックファイルを正しく参照できるようにする。
現状の `Path(__file__).parent * 4` はインストール環境で壊れる。

### TDD サイクル

**Red フェーズ**
- `tests/core/test_package_data.py` を新規作成
- `importlib.resources` でスペックファイルにアクセスするテストを記述（失敗）

**Green フェーズ**
- `data/schemas/` → `src/iso8583_manager/data/schemas/` へ移動
- `src/iso8583_manager/data/__init__.py` を作成
- `src/iso8583_manager/data/schemas/__init__.py` を作成
- `container.py` の `_DEFAULT_SPEC_PATH` を `importlib.resources` に変更

**Refactor フェーズ**
- 旧 `data/` ディレクトリを削除
- `container.py` のコードを整理

### 変更ファイル
- `src/iso8583_manager/presentation/container.py`
- `src/iso8583_manager/data/` （新規ディレクトリ）

---

## Step 4: `__main__.py` 作成（統合エントリポイント）

### 目標
`iso8583-msg cli|api|web` という単一コマンドでモードを選択できるようにする。
`python -m iso8583_manager` でも起動可能にする。

### エントリポイント設計

```
iso8583-msg                          # ヘルプ表示
iso8583-msg cli [generate|parse|...] # 既存 CLI コマンド（ネスト）
iso8583-msg api [--host] [--port]    # REST API 起動
iso8583-msg web [--host] [--port]    # Web UI 起動（将来実装）
```

### TDD サイクル

**Red フェーズ**
- `tests/presentation/test_main.py` を新規作成
- 以下のテストを記述（失敗）:
  - `test_main_module_exists`: `__main__` モジュールに `main` 関数と `app` が存在する
  - `test_cli_subcommand_registered`: `cli` サブコマンドが登録されている
  - `test_api_subcommand_registered`: `api` サブコマンドが登録されている
  - `test_web_subcommand_registered`: `web` サブコマンドが登録されている
  - `test_no_args_shows_help`: 引数なしでヘルプが表示される
  - `test_api_requires_extra`: fastapi 未インストール時に有用なエラーメッセージが出る

**Green フェーズ**
- `src/iso8583_manager/__main__.py` を作成
- Typer `app` に既存 CLI アプリをネスト
- `api` / `web` サブコマンドを追加（遅延インポートで optional 依存に対応）

**Refactor フェーズ**
- 不要になった既存のエントリポイント設定を整理

### 変更ファイル
- `src/iso8583_manager/__main__.py` （新規）
- `pyproject.toml`（エントリポイント更新）

---

## Step 6: `pyproject.toml` 依存関係の分割

### 目標
ライブラリ / CLI / API をそれぞれ独立してインストールできるようにする。

### 依存関係設計

```toml
[project.dependencies]
# ライブラリコア（必須）
pyiso8583, pydantic, typer, rich

[project.optional-dependencies]
api = [fastapi, uvicorn]
web = [fastapi, uvicorn, jinja2]
all = [iso8583_manager[api,web]]
dev = [pytest, mypy, ruff, ...]
```

`typer` / `rich` はランチャー自体に必要なのでコア依存に残す。

### TDD サイクル

**Red フェーズ**
- `tests/test_package_metadata.py` を新規作成
- パッケージのメタデータ（optional-dependencies の構造）を検証するテストを記述

**Green フェーズ**
- `pyproject.toml` の依存関係を分割
- `iso8583-msg` エントリポイントを `__main__:main` に更新

**Refactor フェーズ**
- 旧エントリポイント `iso8583-msg-cli` を削除

---

## 実行順序とチェックポイント

| Step | 作業内容 | 完了条件 |
|------|---------|---------|
| 1 | `app/` 除去 | 全テストがリポジトリルートから pass |
| 2+3 | data 移動 + importlib.resources | `test_package_data.py` pass |
| 4 | `__main__.py` | `test_main.py` pass |
| 6 | pyproject.toml 分割 | `test_package_metadata.py` pass |
