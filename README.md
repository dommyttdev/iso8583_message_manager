# ISO 8583 Message Manager

![Python](https://img.shields.io/badge/python-3.10%2B-blue)

ISO 8583 金融メッセージの生成・解析を行うモノレポ。
`pyiso8583` をクリーンアーキテクチャでラップし、CLI・REST API・Web UI の各インターフェースを提供する。

## リポジトリ構成

```
d:/Projects/Cards/
├── packages/
│   ├── iso8583-types/     # 型定義・インターフェース・例外（pyiso8583 依存なし）
│   └── iso8583-core/      # ユースケース・インフラ実装
├── api/                   # FastAPI サービス
├── cli/                   # CLI ツール
├── shared/
│   └── openapi/           # API 契約（api/ と web/ の HTTP 境界）
└── doc/                   # 設計ドキュメント
```

### 依存関係

```
api/ ──→ iso8583-core ──→ iso8583-types
cli/ ──→ iso8583-core ──→ iso8583-types
web/ ──→ (HTTP のみ)  ──→ api/
```

## セットアップ

各コンポーネントは独立した仮想環境で管理します（[uv](https://docs.astral.sh/uv/) 推奨）。

```bash
# CLI
cd cli && uv sync

# REST API
cd api && uv sync

# ライブラリのみ（開発・テスト用）
cd packages/iso8583-core && uv sync
```

uv 未インストールの場合は pip を使用してください。

```bash
cd cli && pip install -e .
cd api && pip install -e .
```

## クイックスタート

### CLI

```bash
# メッセージ生成（hex 出力）
iso8583-msg generate 0200 primary_account_number=4111111111111111 processing_code=000000

# メッセージ生成（JSON 出力）
iso8583-msg generate 0200 primary_account_number=4111111111111111 --output json

# メッセージ解析
iso8583-msg parse 303230302...

# メッセージ解析（テーブル出力）
echo "303230302..." | iso8583-msg parse --output table

# フィールド定義一覧
iso8583-msg fields

# MTI 種別一覧
iso8583-msg mti-types
```

### REST API サーバー

```bash
cd api
uvicorn iso8583_api.app:app --host 127.0.0.1 --port 8000
# → http://127.0.0.1:8000/docs (Swagger UI)
```

### Python ライブラリとして使用

```python
import importlib.resources

from iso8583_types.models.mti import Mti
from iso8583_types.models.generated.iso_models import Iso8583MessageModel
from iso8583_core.use_cases.message_generation import GenerateMessageUseCase
from iso8583_core.infrastructure.pyiso8583_adapter.wrapper import PyIso8583Adapter

spec_path = str(importlib.resources.files("iso8583_core.data.schemas") / "iso8583_fields.json")
adapter = PyIso8583Adapter(spec_path)
use_case = GenerateMessageUseCase(adapter)

model = Iso8583MessageModel(
    primary_account_number="4111111111111111",
    processing_code="000000",
)
raw = use_case.execute(mti=Mti.from_str("0200"), model_data=model)
print(raw.hex())
```

## 開発コマンド

各コンポーネントのディレクトリから実行します。

```bash
# テスト
pytest

# カバレッジ付きテスト
pytest --cov

# 型チェック
mypy src/

# リント
ruff check src/ tests/
```

全コンポーネントをまとめてテストする場合:

```bash
for dir in packages/iso8583-types packages/iso8583-core api cli; do
    echo "=== $dir ===" && (cd $dir && pytest -q)
done
```

## フィールド定義の更新

`packages/iso8583-core/src/iso8583_core/data/schemas/iso8583_fields.json` を編集した後、モデルと OpenAPI スキーマを再生成します。

```bash
cd packages/iso8583-core
python scripts/code_generator/generate_models.py
python scripts/code_generator/generate_openapi.py
```

生成物:
- `packages/iso8583-types/src/iso8583_types/models/generated/iso_models.py`
- `packages/iso8583-core/src/iso8583_core/data/schemas/generated/openapi.yaml`
- `shared/openapi/iso8583-api.yaml`

## アーキテクチャ

```
Presentation（api/ / cli/）
        ↓
   Use Cases（iso8583-core）
        ↓
   Interfaces（iso8583-types）
        ↑
Infrastructure（iso8583-core / pyiso8583 アダプター）
```

詳細: [doc/architecture/system_design.md](doc/architecture/system_design.md)

## ドキュメント

| ドキュメント | 内容 |
|---|---|
| [doc/architecture/system_design.md](doc/architecture/system_design.md) | システム設計・アーキテクチャ方針 |
| [doc/api/api_design.md](doc/api/api_design.md) | REST API 設計・エンドポイント仕様 |
| [doc/cli/cli_reference.md](doc/cli/cli_reference.md) | CLI コマンドリファレンス |
| [doc/domain/iso8583/iso8583_specs.md](doc/domain/iso8583/iso8583_specs.md) | ISO 8583 ドメイン知識 |
| [doc/tests/test_strategy.md](doc/tests/test_strategy.md) | テスト戦略 |
