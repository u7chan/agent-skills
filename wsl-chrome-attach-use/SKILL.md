---
name: wsl-chrome-attach-use
description: attach 済み Windows Chrome を chrome-devtools-mcp 経由で操作する
---

# WSL Chrome Attach Use

`wsl-chrome-attach` で接続診断済みの Windows Chrome を、`chrome-devtools-mcp` のツールで操作する。

このスキルは attach 済みの Chrome を使う。`browser-use` CLI の独自ブラウザ起動は扱わない。

## 前提条件

- `wsl-chrome-attach` の診断が成功している。
- 診断成功時に表示された `--browserUrl=...` が `chrome-devtools-mcp` の起動引数に設定されている。
- MCP 設定後にエージェントを再起動し、このセッションで Chrome DevTools MCP ツールが利用可能になっている。クライアントによっては `chrome-devtools_navigate_page` のようにサーバー名 prefix 付きで表示されるため、`navigate_page`、`take_screenshot`、`click`、`fill`、`press_key`、`wait_for` に対応するツールが見えていることを確認する。
- Chrome はユーザー管理の専用 profile で起動したままにする。

## ワークフロー

### 1. MCP ツールの可視性を確認する

このセッションで Chrome DevTools MCP ツールが見えているか確認する。

利用可能な MCP ツール一覧に `navigate_page`、`take_screenshot`、`take_snapshot` などに対応するツールがない場合は、まだ操作を始めない。`chrome-devtools_navigate_page` のような prefix 付き表示も同じ操作として扱う。対応するツールが見つからない時は、`wsl-chrome-attach` の診断結果を使って MCP 設定を見直し、エージェントを再起動してから再実行する。

### 2. 対象 URL を決める

ユーザー指定の URL がある場合はそれを使う。指定がない場合は、対象アプリの dev server や README を確認して `localhost` または `127.0.0.1` の URL を特定する。

### 3. ページへ遷移する

`navigate_page` で対象 URL を開く。既存タブを使う場合でも、最初に明示的に遷移して操作対象を固定する。

### 4. 初期状態を確認する

`take_snapshot` でアクセシビリティツリーと要素参照を確認する。見た目の確認が必要な場合は `take_screenshot` も取る。

### 5. 要素参照で操作する

`take_snapshot` に表示された要素参照を使って、クリックや入力を 1 操作ずつ進める。画面遷移や DOM 更新の後は、再度 `take_snapshot` を取って参照を確認し直す。

よく使う操作:

- `click`: ボタン、リンク、チェックボックスなどを押す
- `fill`: 入力欄へテキストを入れる
- `press_key`: Enter、Tab、Escape などのキーを送る
- `wait_for`: 表示テキストや状態変化を待つ

### 6. 結果を待って確認する

保存・送信・遷移などの完了条件を `wait_for` で待つ。その後 `take_snapshot` や `take_screenshot` で結果を確認する。

### 7. 片付ける

確認が終わっても、ユーザー管理の Chrome は勝手に閉じない。必要なら操作に使ったタブだけを閉じる。remote debugging 付き Chrome の終了はユーザーの判断に委ねる。

## 判断基準

- attach 済み Chrome を使いたい場合だけこのスキルを使う。
- MCP ツールがこのセッションで見えていない場合は、操作ではなく設定確認へ戻る。
- 認証済み profile や既存セッションが必要な確認では、`browser-use` ではなくこのスキルを使う。
- 画面遷移後や入力後は、要素参照が変わる前提で再確認する。

## トラブルシュート

- MCP ツールが使えない時: `wsl-chrome-attach` の成功 URL を `chrome-devtools-mcp` の `--browserUrl` に設定し、エージェントを再起動する。
- 要素が見つからない時: スクロール後に `take_snapshot` を取り直す。必要に応じて `take_screenshot` で実画面も確認する。
- `Session not found` や接続失敗が出る時: Chrome が起動中か、portproxy が有効か、`wsl-chrome-attach` の診断が成功するかを確認する。
- 認証状態が期待と違う時: Windows 側 Chrome が専用 profile で起動しているか確認する。
