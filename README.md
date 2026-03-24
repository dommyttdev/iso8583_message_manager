# iso8583-manager

![Python](https://img.shields.io/badge/python-3.10%2B-blue)

`pyiso8583` をクリーンアーキテクチャでラップした ISO 8583 金融メッセージ生成・解析ライブラリ。

## 特徴

- **メタデータ駆動**: `iso8583_fields.json` を唯一の定義源として Pydantic モデルを自動生成
- **型安全な MTI**: バージョン・クラス・機能・起点の 4 enum で構成する Value Object
- **CLI / REST API**: `iso8583-msg cli` と `iso8583-msg api` の両インターフェースを提供
- **複数出力形式**: hex / JSON / binary / table に対応
- **クリーンアーキテクチャ**: Use Cases が具体実装に依存しない設計（DIP）

## インストール

### 基本（CLI のみ）

```bash
pip install -e .
```

### REST API サーバー付き

```bash
pip install -e ".[api]"
```

## クイックスタート

### CLI

```bash
# メッセージ生成（hex 出力）
iso8583-msg cli generate 0200 primary_account_number=4111111111111111 processing_code=000000

# メッセージ生成（JSON 出力）
iso8583-msg cli generate 0200 primary_account_number=4111111111111111 --output json

# メッセージ解析（JSON 出力）
iso8583-msg cli parse 303230302...

# メッセージ解析（テーブル出力 / stdin から読み込み）
echo "303230302..." | iso8583-msg cli parse --output table

# フィールド定義一覧
iso8583-msg cli fields

# MTI 種別一覧
iso8583-msg cli mti-types
```

### REST API サーバー

```bash
# サーバー起動
iso8583-msg api --host 127.0.0.1 --port 8000
# → ブラウザで http://127.0.0.1:8000/docs (Swagger UI) を開く
```

### Python ライブラリとして使用

```python
from iso8583_manager.core.models.mti import Mti
from iso8583_manager.core.models.generated.iso_models import Iso8583MessageModel
from iso8583_manager.presentation.container import build_generate_use_case

mti = Mti.from_str("0200")
model = Iso8583MessageModel(
    primary_account_number="4111111111111111",
    processing_code="000000",
)
use_case = build_generate_use_case()
raw = use_case.execute(mti=mti, model_data=model)
print(raw.hex())
```

## アーキテクチャ

```
Presentation（CLI / REST API）
        ↓
   Use Cases（ビジネスロジック）
        ↓
   Core（モデル・インターフェース）
        ↑
Infrastructure（pyiso8583 アダプター）
```

詳細: [doc/architecture/system_design.md](doc/architecture/system_design.md)

## フィールド定義の更新

`src/iso8583_manager/data/schemas/iso8583_fields.json` を編集した後、モデルを再生成します。

```bash
python scripts/code_generator/generate_models.py
```

## 開発コマンド

以下のコマンドはプロジェクトルート（`pyproject.toml` があるディレクトリ）から実行してください。

```bash
# テスト実行
pytest

# カバレッジ付きテスト
pytest --cov=iso8583_manager

# 型チェック
mypy src/

# リント
ruff check src/ tests/
```

## ドキュメント

[doc/README.md](doc/README.md) を参照してください。
