# ISO 8583

**ISO 8583**は、国際標準化機構が金融取引カード始発メッセージを定めたもので、カード所有者が支払手段にカードを使用した場合に発生する電子メッセージの標準規格である。以下の3部で構成される。
* Part 1:メッセージ、データエレメントおよびコード値
* Part 2:機関識別コード (IIC) の応用および登録手順
* Part 3:メッセージ、データエレメントおよびコード値の保全手順

## 概要

カードを使用した場合、そのカードが使用できるかを確認するため、POS端末や現金自動預け払い機(ATM)などのカードを読み取る機械から、ネットワークを経由して、カードを発行している会社（イシュア）のシステムまでメッセージは渡される。そのメッセージデータには、カードの情報（カード番号など）や端末の情報（店舗番号など）、業務情報（金額など）、システムによって加えられる情報などが含まれる。カードを発行しているシステムは、そのトランザクションを承認または拒否して端末へ送る応答メッセージを発生させる。

異なるシステムが上記のトランザクションを交わすことができるよう、ISO 8583はメッセージ形式とコミュニケーション・フローを定義している。客が店で支払をする際にカードを使用する場合や、ATMが使用される大多数の場合は、ISO 8583が使用されている。マスターカードやVisaネットワークなど多くのネットワークは、信用照会業務はISO 8583をベースに手順を定められているが、ISO 8583にはルーティング情報がないため、TPDUヘッダが追加されている場合が多い。

ISO 8583には、カード所有者から発生するトランザクション（購入・取消・融資・返済・残高照会・口座変更）などや、セキュリティ・キー交換や、取引件数・金額の管理など、その他管理目的のための、システムメッセージ様式が定められている。

ISO 8583での標準のメッセージ形式は、各ネットワークやシステムではそのまま使用されていない。各ネットワークは、ISO 8583の形式をそれぞれカスタマイズして使用している。

ISO 8583の異なる版によって、各フィールドの使用方法が異なっている。例えば、1987年版と1993年版で使用されている通貨エレメントは、2003年版では使用されておらずそれぞれの金額項目のサブフィールドとして通貨を持つようになっている。ただし現在、ISO 8583の2003年版は、広く使用はされていない。

ISO 8583は、以下の内容で構成されている。
* メッセージタイプID (MTI)
* どのデータエレメントが存在するかを示すためのビットマップ
* メッセージフィールドのデータエレメント

## メッセージタイプID (MTI)

MTIは、メッセージの種類を分類する4桁の数値フィールドである。MTIには、メッセージクラス・メッセージ機能、メッセージの発生源の情報が、1桁毎に設定されている。以下の例 (MTI 0110) に、各桁があらわす内容を記載する。
   0xxx → ISO 8583の版（1987年版）
   x1xx → メッセージクラス（オーソリメッセージ）
   xx1x → メッセージ機能（要求に対する応答）
   xxx0 → 手順の発生源（アイワイアラ）

### ISO 8583の版

MTIの1桁目には、このメッセージがどのISO 8583標準バージョンを使用しているかを指定する。

| 値 | 意味 |
|---|---|
| 0xxx | ISO 8583-1:1987年版 |
| 1xxx | ISO 8583-2:1993年版 |
| 2xxx | ISO 8583-1:2003年版 |
| 9xxx | 個社使用 |

### メッセージクラス

MTIの2桁目には、メッセージの全体的な目的を指定する。

| 値 | 意味 | 例 |
|---|---|---|
| x1xx | オーソリ | 取引を承認するか、否認するかを決定する。デュアルメッセージシステム (DMS) のため、決済処理は行わない。 |
| x2xx | ファイナンシャル | 取引を承認する場合は、シングルメッセージシステム (SMS) のため、同時に決済・精算処理を行う。 |
| x3xx | ファイル更新 | カード情報などの更新を行う。 |
| x4xx | 取消 | オーソリの取消を行う。 |
| x5xx | 交換 | 処理件数等の更新情報を送信する。 |
| x6xx | 管理 | システム管理情報を送信する。例えば障害発生による取消メッセージなどで使用される。 |
| x7xx | 課金 | |
| x8xx | ネットワーク管理 | セキュリティキー交換や、開局、エコー・テストなどのネットワーク処理で使用する。 |
| x9xx | ISO予約値 | |

### メッセージ機能

MTIの3桁目には、メッセージをシステム内のどこまで保証しなければならないかを指定する。要求の両端（例えばアクワイアラからイシュア（カード発行会社）で、タイムアウトが発生した場合は自動取消をその範囲で行う）や、アドバイス（端末からアクワイアラ、アクワイアラからネットワーク、ネットワークからイシュア間を保証する）を指定する。

| 値 | 意味 |
|---|---|
| xx0x | 要求 |
| xx1x | 要求に対する応答 |
| xx2x | アドバイス |
| xx3x | アドバイスに対する応答 |
| xx4x | 通知 |
| xx8x | 応答の認証 |
| xx9x | ネガティブな認証 |

### メッセージ発生源

MTIの4桁目には、メッセージの一連のトランザクションの発生源を指定する。

| 値 | 意味 |
|---|---|
| xxx0 | アクワイアラ |
| xxx1 | アクワイアラ（リピート） |
| xxx2 | イシュア |
| xxx3 | イシュア（リピート） |
| xxx4 | その他 |
| xxx5 | その他（リピート） |

### MTI一覧

MTIの4桁の値で、そのメッセージが何のためのメッセージであるか、ネットワークのどの範囲までのものかを指定される。なお、ISO 8583を使用しているすべてのシステムで、MTIの意味を全く同じに解釈しているとは限らないが、以下にMTI値の例を示す。

| MTI | 意味 | 例 |
|---|---|---|
| 0100 | オーソリ要求 | カード会員が購入するためのPOS端末からの承認要求 |
| 0110 | オーソリ応答 | カード会員へ承認するためのイシュアからPOS端末への応答 |
| 0120 | オーソリアドバイス | POS端末が故障した場合など、承認しなければならない処理結果 |
| 0121 | オーソリアドバイスリピート | アドバイスでタイムアウト発生時 |
| 0130 | オーソリアドバイス応答 | オーソリアドバイスに対する受信結果 |
| 0200 | ファイナンシャル要求 | ATMやシングルメッセージシステムのPOS端末などから発生する決済要求 |
| 0210 | ファイナンシャル要求応答 | 決済要求に対するイシュアからの応答 |
| 0220 | ファイナンシャルアドバイス | たとえばホテルのチェックアウトなど、オーソリ要求から始まった一連のトランザクションの完了時に使用される |
| 0221 | ファイナンシャルアドバイスリピート | アドバイスでタイムアウト発生時 |
| 0230 | ファイナンシャルアドバイス応答 | ファイナンシャルアドバイスに対する受信結果 |
| 0400 | 取消要求 | トランザクションの取消 |
| 0420 | 取消アドバイス | 取消が発生した結果の通知 |
| 0421 | 取消アドバイスリピート | アドバイスでタイムアウト発生時 |
| 0430 | 取消応答 | 取消アドバイスに対する受信結果 |
| 0800 | ネットワーク管理要求 | エコーテスト、開局、閉局など |
| 0810 | ネットワーク管理応答 | エコーテスト、開局、閉局など |
| 0820 | ネットワーク管理アドバイス | キー交換 |

## ビットマップ

ISO 8583内のビットマップは、メッセージ内にどのデータエレメントが存在するかを示すためのフィールド/サブフィールドである。

メッセージには「プライマリ・ビットマップ」と呼ばれるビットマップが必ず含まれる。それはデータエレメントのうち、フィールド1から64までの存在有無を示すビットマップである。セカンダリ・ビットマップが存在する場合は、一般的にフィールド1のデータエレメントの値に設定され、フィールド65から128までの存在有無を示す。同様に、サード・ビットマップは、フィールド129から192までの存在有無を示すものだが、あまり使用されない。

ビットマップは、8バイトのバイナリデータや、16進数の文字（0-9, A-F のASCIIまたはEBCDICコード）で示される。

特定のビットが立っている場合のみ、該当のフィールドが存在する。たとえば、'82x は2進数で '1000 0010' であるため、フィールド1と7のみ存在し、2, 3, 4, 5, 6, 8は存在しないことを示す。

### ビットマップの設定例

| ビットマップ | 存在フィールド |
|---|---|
| 4210001102C04804 | フィールド 2, 7, 12, 28, 32, 39, 41, 42, 50, 53, 62 |
| 7234054128C28805 | フィールド 2, 3, 4, 7, 11, 12, 14, 22, 24, 26, 32, 35, 37, 41, 42, 47, 49, 53, 62, 64 |
| 8000000000000001 | フィールド 1, 64 |
| 0000000000000003（セカンダリ・ビットマップ） | フィールド 127, 128 |

ビットマップの例（8バイトのプライマリ・ビットマップ = 64ビット）フィールド 4210001102C04804
BYTE1 : 01000010 = 42x（左から2番目と7番目のビットが1のため、フィールド2と7が存在することを示す）
BYTE2 : 00010000 = 10x（フィールド12が存在）
BYTE3 : 00000000 = 00x（フィールドは存在しない）
BYTE4 : 00010001 = 11x（フィールド28と32が存在）
BYTE5 : 00000010 = 02x（フィールド39が存在）
BYTE6 : 11000000 = C0x（フィールド41と42が存在）
BYTE7 : 01001000 = 48x（フィールド50と53が存在）
BYTE8 : 00000100 = 04x（フィールド62が存在）

```text
0________10________20________30________40________50________60__64
1234567890123456789012345678901234567890123456789012345678901234  ビットの位置
0100001000010000000000000001000100000010110000000100100000000100  ビットマップ
```

上記内容で存在するフィールド
2-7-12-28-32-39-41-42-50-53-62

## データエレメント

データエレメントは、そのトランザクションの情報を構成する個々のフィールドである。ISO 8583:1987でデータエレメントは最大128フィールド制定され、後に192フィールドまで拡張された。1993年での改訂ではメッセージ形式そのものは変わっていないが、新しい定義が加えられたのと同時に多少の削除があった。

それぞれのデータエレメントには意味とフォーマットが指定されているが、ISOで標準化されている内容と使用している各システムでは実際には若干異なっており、システム特有・国特有の多目的なデータエレメントが含まれる。

各データエレメントは、以下の表で記載される属性（値や長さ）で記述される。

| 属性 | 意味 |
|---|---|
| a | 英字（ブランクを含む） |
| n | 数字のみ |
| s | 特殊文字のみ |
| an | 英字または数字 |
| as | 英字または特殊文字 |
| ns | 数字または特殊文字 |
| ans | 英字、数字、特殊文字 |
| b | バイナリデータ |
| z | ISO/IEC 7813 と ISO/IEC 4909 で定義されたトラック2・トラック3のコード値 |
| . ／ .. ／ ... | 長さが可変であることを示す。 |
| x ／ xx ／ xxx | 固定長の桁数 または 可変長の最大桁数 |

各フィールドは、固定長である場合と可変長の場合がある。可変長であれば、値の前に実際の長さが設定される。

| 属性 | 意味 |
|---|---|
| Fixed | 桁数フィールドは使用しない |
| LLVAR ／ (..xx) | LLが100未満の場合は、2桁の桁数を指定する |
| LLLVAR ／ (...xxx) | LLが100未満の場合は、3桁の桁数を指定する |
| LL／LLLは、16進数またはASCII。桁数フィールドはASCIIの時に限り圧縮することができる。 | LLは1バイトまたは2バイトである。16進数の1バイトとして圧縮する場合は、'27x は27バイトのフィールド値が後続することをあらわす。ASCII 2バイト '32x '37x が指定された場合も、同様に27バイトのフィールド値が後続することをあらわす。ASCIIで3桁フィールドの桁数を指定する場合、先頭の'0'を省略して2バイトであらわす場合もある。 |

### ISOで定義されたデータエレメント

| データエレメント | 属性 | Name | 名称 |
|---|---|---|---|
| 1 | b 64 | Bit Map | ビットマップ（セカンダリが存在する場合は b 128、サードが存在する場合は b 192） |
| 2 | n ..19 | Primary Account Number | 会員番号・口座番号 (PAN) |
| 3 | n 6 | Processing Code | プロセシングコード |
| 4 | n 12 | Amount, Transaction | 取引金額 |
| 5 | n 12 | Amount, Settlement | 決済金額 |
| 6 | n 12 | Amount, Cardholder Billing | 会員請求金額 |
| 7 | n 10 | Transmission Date and Time | 送信日時 |
| 8 | n 8 | Amount, Cardholder Billing Fee | 会員請求料金 |
| 9 | n 8 | Conversion Rate, Settlement | 決済通貨レート |
| 10 | n 8 | Conversion Rate, Cardholder Billing | 会員請求通貨レート |
| 11 | n 6 | Systems Trace Audit Number | システムトレースオーディットナンバー |
| 12 | n 6 | Time, Local Transaction | 現地取引時刻 (hhmmss) |
| 13 | n 4 | Date, Local Transaction | 現地取引日 (MMDD) |
| 14 | n 4 | Date, Expiration | 有効期限 |
| 15 | n 4 | Date, Settlement | 決済日 |
| 16 | n 4 | Date, Conversion | レート変換日 |
| 17 | n 4 | Date, Capture | 収集日 |
| 18 | n 4 | Merchant Type | 加盟店業種 |
| 19 | n 3 | Acquiring Institution Country Code | アクワイアラ国コード |
| 20 | n 3 | PAN Extended, Country Code | 会員国コード |
| 21 | n 3 | Forwarding Institution. Country Code | 送信元国コード |
| 22 | n 3 | Point of Service Entry Mode | POS入力モード |
| 23 | n 3 | Application PAN Number | アプリケーションPAN通番 |
| 24 | n 3 | Function Code / Network International Identifier | ファンクションコード (ISO 8583:1993)／ネットワーク国際識別 (NII) |
| 25 | n 2 | Point of Service Condition Code | POS状態コード |
| 26 | n 2 | Point of Service Capture Code | POS暗証番号収集コード |
| 27 | n 1 | Authorizing Identification Response Length | 承認コード長 |
| 28 | n 8 | Amount, Transaction Fee | 取引手数料 |
| 29 | n 8 | Amount, Settlement Fee | 決済手数料 |
| 30 | n 8 | Amount, Transaction Processing Fee | オリジナル取引金額 |
| 31 | n 8 | Amount, Settlement Processing Fee | オリジナル決済金額 |
| 32 | n ..11 | Acquiring Institution Identification Code | アクワイアラ識別コード |
| 33 | n ..11 | Forwarding Institution Identification Code | 送信元識別コード |
| 34 | n ..28 | Primary Account Number, Extended | 拡張会員番号・拡張口座番号 |
| 35 | z ..37 | Track 2 Data | トラック2データ |
| 36 | n ...104 | Track 3 Data | トラック3データ |
| 37 | an 12 | Retrieval Reference Number | リトリーバルリファレンスナンバー |
| 38 | an 6 | Authorization Identification Response | 承認コード |
| 39 | an 2 | Response Code | レスポンスコード |
| 40 | an 3 | Service Restriction Code | サービス規制コード |
| 41 | ans 16 | Card Acceptor Terminal Identification | カード利用端末識別 |
| 42 | ans 15 | Card Acceptor Identification Code | カード利用識別コード |
| 43 | ans 40 | Card Acceptor Name/Location | カード利用店舗名／住所（1-23が住所、24-36が都市、37-38が州、39-40が国） |
| 44 | an ..25 | Additional Response Data | 追加応答データ |
| 45 | an ..76 | Track 1 Data | トラック1データ |
| 46 | an ...999 | Additional Data - ISO | ISO用追加データ |
| 47 | an ...999 | Additional Data - National | 各国用追加データ |
| 48 | an ...999 | Additional Data - Private | 個社用追加データ |
| 49 | a 3 | Currency Code, Transaction | 取引通貨コード |
| 50 | an 3 | Currency Code, Settlement | 決済通貨コード |
| 51 | a 3 | Currency Code, Cardholder Billing | 会員請求通貨コード |
| 52 | b 64 | Personal Identification Number Data | 会員暗証番号 |
| 53 | n 18 | Security Related Control Information | セキュリティ関連制御情報 |
| 54 | an ...120 | Additional Amounts | 追加金額 |
| 55 | ans ...999 | Reserved ISO | ISO用予約域 |
| 56 | ans ...999 | Reserved ISO | ISO用予約域 |
| 57 | ans ...999 | Reserved National | 各国用予約域 |
| 58 | ans ...999 | Reserved National | 各国用予約域 |
| 59 | ans ...999 | Reserved for National Use | 国際用予約域 |
| 60 | an .7 | Advice/reason Code (Private Reserved) | 理由コード（個社用予約域） |
| 61 | ans ...999 | Reserved Private | 個社用予約域 |
| 62 | ans ...999 | Reserved Private | 個社用予約域 |
| 63 | ans ...999 | Reserved Private | 個社用予約域 |
| 64 | b 16 | Message Authentication Code (MAC) | メッセージ認証コード (MAC) |
| 65 | b 64 | Tertiary Bitmap | サード・ビットマップ（セカンダリ・ビットマップ存在時のみ） |
| 66 | n 1 | Settlement Code | 決済コード |
| 67 | n 2 | Extended Payment Code | 拡張支払コード |
| 68 | n 3 | Receiving Institution Country Code | 受信機関国コード |
| 69 | n 3 | Settlement Institution Country Code | 決済機関国コード |
| 70 | n 3 | Network Management Information Code | ネットワーク管理情報コード |
| 71 | n 4 | Message Number | メッセージ番号 |
| 72 | ans ...999 | Data Record /n 4 Message Number, Last | データレコード (ISO 8583:1993)／n 4 最終メッセージ番号 |
| 73 | n 6 | Date, Action | 実行日 |
| 74 | n 10 | Credits, Number | クレジット件数 |
| 75 | n 10 | Credits, Reversal Number | クレジット取消件数 |
| 76 | n 10 | Debits, Number | デビット件数 |
| 77 | n 10 | Debits, Reversal Number | デビット取消件数 |
| 78 | n 10 | Transfer Number | 送信件数 |
| 79 | n 10 | Transfer, Reversal Number | 送信取消件数 |
| 80 | n 10 | Inquiries Number | 照会件数 |
| 81 | n 10 | Authorizations, Number | オーソリ件数 |
| 82 | n 12 | Credits, Processing Fee Amount | クレジット処理手数料 |
| 83 | n 12 | Credits, Transaction Fee Amount | クレジット業務手数料 |
| 84 | n 12 | Debits, Processing Fee Amount | デビット処理手数料 |
| 85 | n 12 | Debits, Transaction Fee Amount | デビット業務手数料 |
| 86 | n 15 | Credits, Amount | クレジット金額 |
| 87 | n 15 | Credits, Reversal amount | クレジット取消金額 |
| 88 | n 15 | Debits, Amount | デビット金額 |
| 89 | n 15 | Debits, Reversal Amount | デビット取消金額 |
| 90 | n 42 | Original Data Elements | オリジナルデータエレメント |
| 91 | an 1 | File Update Code | ファイル更新コード |
| 92 | n 2 | File Security Code | ファイルセキュリティコード |
| 93 | n 5 | Response Indicator | レスポンス指標 |
| 94 | an 7 | Service Indicator | サービス指標 |
| 95 | an 42 | Replacement Amounts | 交換金額 |
| 96 | an 8 | Message Security Code | メッセージセキュリティコード |
| 97 | n 16 | Amount, Net Settlement | ネット決済金額 |
| 98 | ans 25 | Payee | 受取人 |
| 99 | n ..11 | Settlement Institution Identification Code | 決済機関識別コード |
| 100 | n ..11 | Receiving Institution Identification Code | 受信機関識別コード |
| 101 | ans 17 | File Name | ファイル名 |
| 102 | ans ..28 | Account Identification 1 | 口座識別 1 |
| 103 | ans ..28 | Account Identification 2 | 口座識別 2 |
| 104 | ans ...100 | Transaction Description | 業務固有情報 |
| 105 | ans ...999 | Reserved for ISO Use | ISO用予約域 |
| 106 | ans ...999 | Reserved for ISO Use | ISO用予約域 |
| 107 | ans ...999 | Reserved for ISO Use | ISO用予約域 |
| 108 | ans ...999 | Reserved for ISO Use | ISO用予約域 |
| 109 | ans ...999 | Reserved for ISO Use | ISO用予約域 |
| 110 | ans ...999 | Reserved for ISO Use | ISO用予約域 |
| 111 | ans ...999 | Reserved for ISO Use | ISO用予約域 |
| 112 | ans ...999 | Reserved for ISO Use | ISO用予約域 |
| 113 | n ..11 | Authorizing Agent Institution ID Code | オーソリ許可識別コード |
| 114 | ans ...999 | Reserved for National Use | 各国用予約域 |
| 115 | ans ...999 | Reserved for National Use | 各国用予約域 |
| 116 | ans ...999 | Reserved for National Use | 各国用予約域 |
| 117 | ans ...999 | Reserved for National Use | 各国用予約域 |
| 118 | ans ...999 | Reserved for National Use | 各国用予約域 |
| 119 | ans ...999 | Reserved for National Use | 各国用予約域 |
| 120 | ans ...999 | Reserved for Private Use | 個社用予約域 |
| 121 | ans ...999 | Reserved for Private Use | 個社用予約域 |
| 122 | ans ...999 | Reserved for Private Use | 個社用予約域 |
| 123 | ans ...999 | Reserved for Private Use | 個社用予約域 |
| 124 | ans ...255 | Info Text | テキスト情報 |
| 125 | ans ..50 | Network Management Information | ネットワーク管理情報 |
| 126 | ans .6 | Issuer Trace ID | イシュアトレース識別 |
| 127 | ans ...999 | Reserved for Private Use | 個社用予約域 |
| 128 | b 16 | Message Authentication Code | メッセージ認証コード (MAC) |

### 属性の例

| フィールド属性値 | 意味 |
|---|---|
| n6 | 6桁の固定長数字フィールド |
| n.6 | 最大6桁の可変長数字フィールド |
| a..11 | 最大11桁の可変長英字フィールド |
| b...999 | 999バイトのバイナリフィールド |

---
*出典: Wikipedia (https://ja.wikipedia.org/wiki/ISO_8583) の内容を完全収録*
