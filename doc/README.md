# ドキュメント一覧

このディレクトリには iso8583-manager の設計・仕様・テスト関連ドキュメントが含まれています。

## アーキテクチャ・設計

| ファイル | 内容 |
|---------|------|
| [architecture/system_design.md](architecture/system_design.md) | クリーンアーキテクチャ採用の背景、層構造、DIP 設計方針 |

## インターフェース仕様

| ファイル | 内容 |
|---------|------|
| [cli/cli_reference.md](cli/cli_reference.md) | `iso8583-msg cli` 全コマンドのオプション・使用例・終了コード一覧 |
| [api/api_design.md](api/api_design.md) | REST API エンドポイント設計・リクエスト/レスポンス仕様（FastAPI） |

## ドメイン知識

| ファイル | 内容 |
|---------|------|
| [domain/iso8583/iso8583_specs.md](domain/iso8583/iso8583_specs.md) | ISO 8583 標準の概要・MTI・ビットマップ・データ要素の解説 |

## テスト

| ファイル | 内容 |
|---------|------|
| [tests/test_strategy.md](tests/test_strategy.md) | テスト全体戦略・TDD 方針・カバレッジ目標 |
| [tests/api_test_plan.md](tests/api_test_plan.md) | REST API 層テスト計画 |
| [tests/uat_test_plan.md](tests/uat_test_plan.md) | CLI ユーザー受け入れテスト計画 |

## 依存ライブラリ（外部ドキュメント）

| ライブラリ | ドキュメント |
|-----------|-------------|
| pyiso8583 | https://pyiso8583.readthedocs.io/en/latest/ |
| pyiso8583 (GitHub) | https://github.com/knovichikhin/pyiso8583 |
