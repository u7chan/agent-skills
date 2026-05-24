---
name: browser-check
description: AI browser checks for localhost UI testing.
---

# Browser Check

`browser-use` を、`localhost` の画面確認用に最小構成で使う。

## 基本

```bash
browser-use open http://localhost:3000
browser-use state
browser-use click 5
browser-use input 3 "hello"
browser-use screenshot
browser-use close
```

`state` で要素番号を確認してから操作する。画面遷移後は必要に応じて再度 `state` を取る。

## よく使うコマンド

```bash
browser-use open http://localhost:3000
browser-use --headed open http://localhost:3000

browser-use state
browser-use screenshot

browser-use click 5
browser-use input 3 "hello"
browser-use keys "Enter"
browser-use scroll down

browser-use get title
browser-use wait selector "button[type=submit]"
browser-use wait text "Saved"

browser-use close
```

## 運用ルール

- `localhost` や `127.0.0.1` の確認用途を優先する
- まず `state` を見てから要素番号で操作する
- 見た目や挙動を確認したい時は `--headed` を使う
- 複雑な自動化より、1 コマンドずつ確実に進める

## 起動モード選択

- スキル起動時、まず `DISPLAY` 環境変数の有無を確認する
- `DISPLAY` がない場合: GUIブラウザは起動できない旨を通知し、ヘッドレスモードに自動フォールバックする
- `DISPLAY` がある場合: ユーザーに「GUIブラウザ表示 (推奨, headed)」または「ヘッドレス (headless)」を選んでもらう
- GUIブラウザ表示 (推奨, headed) を選んだ場合は、`browser-use --headed open <url>` で起動する
- ヘッドレス (headless) を選んだ場合、またはヘッドレスモードにフォールバックした場合は、`browser-use open <url>` で起動する

## トラブルシュート

- ブラウザがおかしい時: `browser-use close` してから再度 `open`
- 要素が見つからない時: `browser-use scroll down` の後に `browser-use state`
- `DISPLAY` 環境変数がない環境で `--headed` を使おうとした時: GUIブラウザは起動できないため、ヘッドレスモードで実行
