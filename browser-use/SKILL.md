---
name: browser-use
description: browser-use CLI の独自ブラウザで localhost などの画面確認を進めるワークフロー。
---

# Browser Use

`browser-use` CLI が起動する独自ブラウザで、`localhost` などの画面確認を進める。

このスキルは `browser-use` CLI 専用であり、ユーザー管理の既存ブラウザや MCP 経由の操作は扱わない。

## ワークフロー

### 1. 対象URLを決める

ユーザー指定の URL がある場合はそれを使う。指定がない場合は、対象アプリの dev server や README を確認して `localhost` または `127.0.0.1` の URL を特定する。

### 2. 起動モードを選択する

まず `DISPLAY` 環境変数の有無を確認する。

- `DISPLAY` がない場合: GUI ブラウザは起動できないため、ヘッドレスモードで進める
- `DISPLAY` がある場合: 画面の見た目や操作感を確認する目的なら headed、状態確認だけで足りる目的なら headless を選ぶ

起動コマンド:

```bash
# headed
browser-use --headed open http://localhost:3000

# headless
browser-use open http://localhost:3000
```

### 3. 初期状態を確認する

`state` で現在のページ構造と要素番号を確認する。見た目の確認が必要な場合は `screenshot` も取る。

```bash
browser-use state
browser-use screenshot
browser-use get title
```

### 4. 要素番号で操作する

`state` に表示された要素番号を使って、クリックや入力を 1 コマンドずつ実行する。画面遷移や DOM 更新の後は、再度 `state` を取って番号を確認し直す。

> 注意: `open` 直後に取得した `state` の番号が、すぐに無効になることがあります。「Element index not found」と出た場合は、まず `browser-use state` を再度実行して番号を確認し直してください。

```bash
browser-use click 5
browser-use input 3 "hello"
browser-use keys "Enter"
browser-use scroll down
browser-use state
```

### 5. 結果を待って確認する

保存・送信・遷移などの完了条件を、セレクタまたは表示テキストで待つ。その後 `state` や `screenshot` で結果を確認する。

> 補足: 遷移や保存が即座に完了し、次の `state` で結果が確認できる場合は `wait` を省略しても構いません。

```bash
browser-use wait selector ".success-message"
browser-use wait text "Saved"
browser-use state
browser-use screenshot
```

### 6. 終了する

確認が終わったらブラウザを閉じる。

```bash
browser-use close
```

## 判断基準

- `localhost` や `127.0.0.1` の確認用途を優先する
- まず `state` を見てから要素番号で操作する
- 見た目や挙動を確認したい時は `--headed` を使う
- 複雑な自動化より、1 コマンドずつ確実に進める
- 画面遷移後や入力後は、要素番号が変わる前提で再確認する

## トラブルシュート

- ブラウザがおかしい時: `browser-use close` してから再度 `open`
- 要素が見つからない時: まず `browser-use state` を再度実行して番号を確認し直す。スクロールで見えていない可能性がある場合は `browser-use scroll down` の後に `browser-use state`
- `DISPLAY` 環境変数がない環境で `--headed` を使おうとした時: GUIブラウザは起動できないため、ヘッドレスモードで実行
