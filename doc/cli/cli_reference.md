# ISO 8583 CLI リファレンス

`iso8583` コマンドは、ISO 8583 金融メッセージのエンコード・デコードをコマンドラインから行うツールです。

---

## インストール

```bash
pip install -e "app/[dev]"
```

インストール後、`iso8583` コマンドが使用可能になります。

---

## 概要

```
iso8583 [OPTIONS] COMMAND [ARGS]...
```

### コマンド一覧

| コマンド | 説明 |
|---|---|
| [`generate`](#generate) | ISO 8583 メッセージをエンコードして出力する |
| [`parse`](#parse) | ISO 8583 メッセージをデコードして出力する |
| [`fields`](#fields) | フィールド定義の一覧を表示する |
| [`mti-types`](#mti-types) | サポートされている MTI 種別の一覧を表示する |

---

## generate

MTI とフィールド値を指定して ISO 8583 メッセージをエンコードし、hex / JSON / バイナリで出力します。

### 構文

```
iso8583 generate [OPTIONS] MTI [FIELDS]...
```

### 引数

| 引数 | 必須 | 説明 |
|---|---|---|
| `MTI` | ✓ | 4桁の MTI 文字列 (例: `0200`) |
| `FIELDS` | — | フィールド指定。`フィールド名=値` 形式で複数指定可 |

### オプション

| オプション | 短縮形 | デフォルト | 説明 |
|---|---|---|---|
| `--output` | `-o` | `hex` | 出力形式: `hex` / `json` / `binary` |
| `--spec` | — | パッケージ内蔵 | spec JSON ファイルのパス |

### 出力形式

#### hex (デフォルト)
hex エンコードされた文字列を標準出力に出力します。他のコマンドへのパイプ入力に適しています。

```bash
$ iso8583 generate 0200 \
    primary_account_number=1234567890123456 \
    amount_transaction=000000001000 \
    --spec data/schemas/iso8583_fields.json

3032303035303030303030303030303030303030313631323334353637383930313233343536303030303030303031303030
```

#### json
MTI・hex 文字列・バイト長を含む JSON を出力します。

```bash
$ iso8583 generate 0200 \
    primary_account_number=1234567890123456 \
    amount_transaction=000000001000 \
    --output json \
    --spec data/schemas/iso8583_fields.json

{"mti": "0200", "hex": "3032303035303030303030303030303030303030313631323334353637383930313233343536303030303030303031303030", "length": 50}
```

#### binary
生バイト列を標準出力に書き込みます。ファイル保存やバイナリパイプに使用します。

```bash
$ iso8583 generate 0200 primary_account_number=1234567890123456 \
    --output binary \
    --spec data/schemas/iso8583_fields.json > message.bin
```

### フィールド指定の注意点

- 値に `=` を含む場合は最初の `=` のみで分割されます (`processing_code=ab=cd` → 値は `ab=cd`)
- 利用可能なフィールド名は [`fields`](#fields) コマンドで確認できます
- `=` を含まない引数や、キーが空の引数 (`=value`) はエラーになります

### エラー終了コード

| 終了コード | 原因 |
|---|---|
| 1 | MTI 形式不正 / 未定義の MTI 値 / 不明なフィールド名 / バリデーションエラー |
| 2 | spec ファイルが見つからない、または読み込みエラー |
| 3 | エンコード処理の失敗 |
| 10 | 予期しないエラー |

---

## parse

hex エンコードされた ISO 8583 メッセージをデコードし、JSON またはテーブルで出力します。

### 構文

```
iso8583 parse [OPTIONS] [HEX_MESSAGE]
```

`HEX_MESSAGE` を省略すると標準入力から読み込みます。

### 引数

| 引数 | 必須 | 説明 |
|---|---|---|
| `HEX_MESSAGE` | — | hex エンコードされた ISO 8583 メッセージ。省略時は stdin から読み込む |

### オプション

| オプション | 短縮形 | デフォルト | 説明 |
|---|---|---|---|
| `--output` | `-o` | `json` | 出力形式: `json` / `table` |
| `--spec` | — | パッケージ内蔵 | spec JSON ファイルのパス |

### 出力形式

#### json (デフォルト)
MTI とフィールド値を含む JSON を出力します。値が `None` のフィールドは出力されません。

```bash
$ iso8583 parse \
    3032303035303030303030303030303030303030313631323334353637383930313233343536303030303030303031303030 \
    --spec data/schemas/iso8583_fields.json

{"mti": "0200", "fields": {"primary_account_number": "1234567890123456", "amount_transaction": "000000001000"}}
```

#### table
フィールド名と値をテーブル形式で表示します。

```bash
$ iso8583 parse \
    3032303035303030303030303030303030303030313631323334353637383930313233343536303030303030303031303030 \
    --output table \
    --spec data/schemas/iso8583_fields.json

                  MTI: 0200
┌────────────────────────┬──────────────────┐
│ フィールド名           │ 値               │
├────────────────────────┼──────────────────┤
│ primary_account_number │ 1234567890123456 │
│ amount_transaction     │ 000000001000     │
└────────────────────────┴──────────────────┘
```

### 標準入力からの読み込み

```bash
# generate の出力を直接 parse にパイプする
$ iso8583 generate 0200 primary_account_number=1234567890123456 \
    --spec data/schemas/iso8583_fields.json \
  | iso8583 parse --spec data/schemas/iso8583_fields.json
```

### エラー終了コード

| 終了コード | 原因 |
|---|---|
| 1 | hex 文字列の形式不正 (非 hex 文字、奇数長、入力なし) |
| 2 | spec ファイルが見つからない、または読み込みエラー |
| 4 | デコード処理の失敗 (メッセージが ISO 8583 形式として不正) |
| 10 | 予期しないエラー |

---

## fields

spec ファイルに定義されたフィールドの一覧をテーブル表示します。
フィールド ID・プロパティ名・説明・データ型・最大長を確認できます。

### 構文

```
iso8583 fields [OPTIONS]
```

### オプション

| オプション | デフォルト | 説明 |
|---|---|---|
| `--spec` | パッケージ内蔵 | spec JSON ファイルのパス |

### 実行例

```bash
$ iso8583 fields --spec data/schemas/iso8583_fields.json

        ISO 8583 フィールド定義
┌───────────────┬────────────────────────────┬──────────────────────────┬──────────┬───────┐
│ フィールドID  │ プロパティ名               │ 説明                     │ データ型 │ 最大長│
├───────────────┼────────────────────────────┼──────────────────────────┼──────────┼───────┤
│ 2             │ primary_account_number     │ Primary Account Number   │ n        │ 19    │
│ 3             │ processing_code            │ Processing Code          │ n        │ 6     │
│ 4             │ amount_transaction         │ Amount, Transaction      │ n        │ 12    │
│ ...           │ ...                        │ ...                      │ ...      │ ...   │
└───────────────┴────────────────────────────┴──────────────────────────┴──────────┴───────┘
```

### エラー終了コード

| 終了コード | 原因 |
|---|---|
| 2 | spec ファイルが見つからない、JSON として不正、またはパスエラー |
| 10 | 予期しないエラー |

---

## mti-types

サポートされている MTI の構成要素 (Version / Class / Function / Origin) の一覧を表示します。
spec ファイルは不要です。

### 構文

```
iso8583 mti-types [OPTIONS]
```

### オプション

| オプション | 短縮形 | デフォルト | 説明 |
|---|---|---|---|
| `--output` | `-o` | `table` | 出力形式: `table` / `json` |

### 出力形式

#### table (デフォルト)
4 つの enum グループをそれぞれテーブル形式で表示します。

```bash
$ iso8583 mti-types

      Version (第1桁: バージョン)
┌──────┬─────────┬──────────────────────┐
│ 桁値 │ 名前    │ 説明                 │
├──────┼─────────┼──────────────────────┤
│ 0    │ V1987   │ ISO 8583-1:1987年版   │
│ 1    │ V1993   │ ISO 8583-2:1993年版   │
│ 2    │ V2003   │ ISO 8583-1:2003年版   │
│ 9    │ PRIVATE │ 個社使用             │
└──────┴─────────┴──────────────────────┘
        Class (第2桁: クラス)
┌──────┬────────────────────┬────────────────────────┐
│ 桁値 │ 名前               │ 説明                   │
├──────┼────────────────────┼────────────────────────┤
│ 1    │ AUTHORIZATION      │ オーソリゼーション     │
│ 2    │ FINANCIAL          │ ファイナンシャル       │
│ ...  │ ...                │ ...                    │
└──────┴────────────────────┴────────────────────────┘
(Function, Origin も同様)
```

#### json
全グループを JSON 配列で出力します。各要素は `digit` / `name` / `description` を持ちます。

```bash
$ iso8583 mti-types --output json

{
  "version": [
    {"digit": 0, "name": "V1987",   "description": "ISO 8583-1:1987年版"},
    {"digit": 1, "name": "V1993",   "description": "ISO 8583-2:1993年版"},
    {"digit": 2, "name": "V2003",   "description": "ISO 8583-1:2003年版"},
    {"digit": 9, "name": "PRIVATE", "description": "個社使用"}
  ],
  "class": [
    {"digit": 1, "name": "AUTHORIZATION",     "description": "オーソリゼーション"},
    {"digit": 2, "name": "FINANCIAL",         "description": "ファイナンシャル"},
    {"digit": 3, "name": "FILE_UPDATE",       "description": "ファイル更新"},
    {"digit": 4, "name": "REVERSAL",          "description": "取消"},
    {"digit": 5, "name": "RECONCILIATION",    "description": "交換"},
    {"digit": 6, "name": "ADMINISTRATIVE",    "description": "管理"},
    {"digit": 7, "name": "FEE",               "description": "課金"},
    {"digit": 8, "name": "NETWORK_MANAGEMENT","description": "ネットワーク管理"}
  ],
  "function": [
    {"digit": 0, "name": "REQUEST",       "description": "要求"},
    {"digit": 1, "name": "RESPONSE",      "description": "要求に対する応答"},
    {"digit": 2, "name": "ADVICE",        "description": "アドバイス"},
    {"digit": 3, "name": "ADVICE_RESPONSE","description": "アドバイスに対する応答"},
    {"digit": 4, "name": "NOTIFICATION",  "description": "通知"},
    {"digit": 8, "name": "RESPONSE_ACK",  "description": "応答の認証"},
    {"digit": 9, "name": "NEGATIVE_ACK",  "description": "ネガティブな認証"}
  ],
  "origin": [
    {"digit": 0, "name": "ACQUIRER",        "description": "アクワイアラ"},
    {"digit": 1, "name": "ACQUIRER_REPEAT", "description": "アクワイアラ（リピート）"},
    {"digit": 2, "name": "ISSUER",          "description": "イシュア"},
    {"digit": 3, "name": "ISSUER_REPEAT",   "description": "イシュア（リピート）"},
    {"digit": 4, "name": "OTHER",           "description": "その他"},
    {"digit": 5, "name": "OTHER_REPEAT",    "description": "その他（リピート）"}
  ]
}
```

---

## MTI 構造

MTI (Message Type Indicator) は 4 桁の数字で、各桁が以下の意味を持ちます。

```
  0    2    0    0
  │    │    │    └─ Origin   (第4桁): 発生源
  │    │    └────── Function (第3桁): 機能
  │    └─────────── Class    (第2桁): クラス
  └──────────────── Version  (第1桁): バージョン
```

詳細な桁値と意味は `iso8583 mti-types` コマンドで確認できます。

---

## 終了コード一覧

| 終了コード | 名称 | 主な原因 |
|---|---|---|
| 0 | 正常終了 | — |
| 1 | ユーザーエラー | MTI 形式不正 / 不明なフィールド名 / バリデーションエラー / hex 形式不正 |
| 2 | spec エラー | spec ファイルが見つからない / JSON として不正 |
| 3 | エンコードエラー | メッセージのエンコード処理の失敗 |
| 4 | デコードエラー | メッセージのデコード処理の失敗 |
| 5 | I/O エラー | ファイル読み書きエラー |
| 10 | 予期しないエラー | その他の例外 |

---

## spec ファイルの解決順序

`--spec` オプションを省略した場合、以下の優先順位でパスが決定されます。

1. `--spec` オプションで指定されたパス
2. 環境変数 `ISO8583_SPEC_PATH` で指定されたパス
3. パッケージに内蔵されたデフォルト (`data/schemas/iso8583_fields.json`)

```bash
# 環境変数による設定例
export ISO8583_SPEC_PATH=/path/to/custom/spec.json
iso8583 generate 0200 primary_account_number=1234567890123456
```

---

## 使用例: generate → parse ラウンドトリップ

```bash
# メッセージを生成して変数に保存
HEX=$(iso8583 generate 0200 \
    primary_account_number=1234567890123456 \
    processing_code=123456 \
    amount_transaction=000000001000 \
    --spec data/schemas/iso8583_fields.json)

echo "生成されたメッセージ: $HEX"

# 生成したメッセージを解析
iso8583 parse "$HEX" --output table --spec data/schemas/iso8583_fields.json
```

### パイプを使った例

```bash
# generate の hex 出力を直接 parse にパイプ
iso8583 generate 0200 primary_account_number=1234567890123456 \
    --spec data/schemas/iso8583_fields.json \
  | iso8583 parse --output table --spec data/schemas/iso8583_fields.json
```

### JSON を jq で処理する例

```bash
# JSON 出力を jq でフィールド値だけ取り出す
iso8583 parse "$HEX" --spec data/schemas/iso8583_fields.json \
  | jq '.fields.primary_account_number'
```
