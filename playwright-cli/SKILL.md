---
name: playwright-cli
description: Playwright CLIで独立ブラウザを操作し、画面を検証する
---

# Playwright CLI

`playwright-cli` で、`localhost` や指定URLを独立したブラウザセッションで検証する。

WSL上でも独立したブラウザセッションを起動する。既存ブラウザへのattachは行わない。

公式仕様は [Microsoft Playwright CLI Skill](https://github.com/microsoft/playwright-cli/blob/main/skills/playwright-cli/SKILL.md) を参照する。

## 標準フロー

1. 確認目的と対象URLを特定する。指定がなければ、対象アプリのREADMEやdev serverから
   `localhost` / `127.0.0.1` を調べる。
2. `playwright-cli` の可用性を確認する。グローバルCLIがなければ、依存関係を導入せず
   `npx --no-install playwright cli` を実行してローカル版だけ確認する。これも失敗した場合は
   原因を断定せず「ローカルCLIの可用性を確認できなかった」と案内する。自動インストールや
   代替操作は行わず、必要なら導入または環境修正をユーザーに依頼する。
3. セッションを開始し、snapshotから操作対象を取得する。
4. refを使って一操作ずつ実行し、結果を確認する。画面遷移またはDOM更新のたびに
   snapshotを再取得し、古いrefを再利用しない。
5. 必要な証跡だけを保存し、必ずセッションを終了する。

```bash
playwright-cli open http://localhost:3000
playwright-cli snapshot
playwright-cli click e15
playwright-cli snapshot
playwright-cli close
```

ローカル版を使う場合は、確認済みの呼び出しを `npx --no-install playwright cli` に置き換える。
例: `npx --no-install playwright cli open http://localhost:3000`。

## 要素の指定と確認

まず `snapshot` のref（例: `e15`）を使う。画面更新後のrefは失効し得るため、対象が
見つからない場合も含めて必ずsnapshotを取り直す。大きなページでは `find` または
浅いsnapshotで対象を絞り込む。

安定した対象を指定する必要がある場合だけ、Playwrightのsemantic locatorを使う。
CSSセレクタよりrole、label、test idを優先する。

```bash
playwright-cli fill e5 "user@example.com"
playwright-cli press Enter
playwright-cli click "getByRole('button', { name: '送信' })"
playwright-cli snapshot
```

## 証跡と失敗時

通常はsnapshotで確認し、視覚的な根拠が必要なときだけscreenshotを保存する。失敗時は
console、requests、traceを採取してからcloseする。詳細は用途別に分けた次の参照を使う。

- コマンド一覧と旧スキルからの対応: `references/commands.md`
- 認証、複数タブ、storage state、localhost確認: `references/workflows.md`
- 診断、証跡、CLI未導入時の切り分け: `references/debugging.md`

## 守ること

- 依存関係、ブラウザバイナリ、グローバルCLIを自動インストールしない
- 操作は対象URLと確認目的に必要な最小限にする
- 認証情報やstorage stateを、ユーザーの明示許可なく保存・共有しない
- `close` を省略しない。外部ブラウザへ接続した場合のdetachは本スキルの対象外
