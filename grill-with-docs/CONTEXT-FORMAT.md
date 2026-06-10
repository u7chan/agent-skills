# CONTEXT.md

`CONTEXT.md` は、コンテキスト固有のユビキタス言語（共通言語）を定義するためのドキュメントである。

目的は、用語の意味を統一し、コンテキスト境界を明確にすることにある。

## 構成

```md
# {Context Name}

{このコンテキストが扱う責務を1〜2文で説明する}

## Language

### Order

顧客から受け付けた注文。

Avoid:
- Purchase
- Transaction

### Invoice

納品後に発行する請求書。

Avoid:
- Bill
- Payment Request

### Customer

注文を行う個人または組織。

Avoid:
- Client
- Buyer

## Flagged Ambiguities

### User vs Customer

本コンテキストでは Customer を使用する。

User はシステム利用者全般を指すため使用しない。
```

## 記載ルール

### 目的

- ユビキタス言語を定義する
- 用語の意味を統一する
- コンテキスト境界を明確にする

### 記載するもの

- このコンテキスト固有の業務用語
- 他コンテキストと意味が衝突しやすい用語
- 避けるべき別名（同義語）
- 一般的な技術用語でも、このコンテキスト固有の業務上の意味を持つ用語

### 記載しないもの

- 実装詳細
- API 仕様
- DB 設計
- ライブラリ名
- フレームワーク名
- 一般的な技術用語
- 業務フロー説明

### 用語定義ルール

- 1〜2文で定義する
- 「何であるか」を記述する
- 「何をするか」は記述しない
- 同義語は1つに統一する
- `Avoid` は避けるべき別名がある場合のみ記載する
- あいまいな用語は `Flagged Ambiguities` に記載する
- 実装都合ではなく業務上の意味で定義する

## 単一コンテキスト

単一コンテキストの場合はリポジトリルートに `CONTEXT.md` を配置する。

```text
CONTEXT.md
```

## 複数コンテキスト

複数コンテキストが存在する場合は、リポジトリルートに `CONTEXT-MAP.md` を配置する。

```text
CONTEXT-MAP.md
src/
├── ordering/
│   └── CONTEXT.md
├── billing/
│   └── CONTEXT.md
└── fulfillment/
    └── CONTEXT.md
```

### CONTEXT-MAP.md

```md
# Context Map

## Contexts

- [Ordering](./src/ordering/CONTEXT.md) — 顧客の注文を受け付け、追跡する
- [Billing](./src/billing/CONTEXT.md) — 請求書を生成し、支払いを処理する
- [Fulfillment](./src/fulfillment/CONTEXT.md) — 倉庫のピッキングと出荷を管理する

## Relationships

- Ordering → Fulfillment : OrderPlaced
- Fulfillment → Billing : ShipmentDispatched
```

関係性はコンテキスト間の依存やイベント連携のみを簡潔に記載する。

## 判断ルール

以下のような用語は `CONTEXT.md` に記載する。

- Order
- Invoice
- Customer
- Subscription
- Tenant
- Shipment
- Product

以下のような用語は、一般的な技術用語として使っているだけなら記載しない。

- Repository
- Service
- Controller
- Timeout
- Error
- Cache
- API
- JWT
- PostgreSQL

ただし、一般的な技術用語でも、このコンテキスト固有の業務上の意味を持つ場合は記載してよい。

## ドキュメントの責務

| ドキュメント | 目的 |
|------------|------|
| ADR | なぜその設計を選んだか |
| CONTEXT | 用語の意味を定義する |
| CONTEXT-MAP | コンテキスト境界と関係を示す |
| Design Doc | どのように実現するか |
| Issue | 実施する作業を管理する |

`CONTEXT.md` は業務仕様書ではなく用語辞書として扱う。
長い説明は避け、将来の開発者が「この用語は何を意味するのか」を素早く理解できることを優先する。
