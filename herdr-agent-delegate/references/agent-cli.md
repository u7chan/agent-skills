# Agent CLI運用差分

## 起動コマンド

| Agent | 起動コマンド | 完了待機 |
| --- | --- | --- |
| Codex | `codex` | semantic state |
| Claude Code | `claude` | semantic state |
| OpenCode | `opencode` | semantic state |
| その他 | ユーザー指定のコマンド | output marker。`agent get` が安定して識別できる場合だけsemantic state |

ユーザーが指定した引数は該当コマンドへ渡す。指定されていない引数を補わない。シェル展開が必要な文字列を組み立てず、コマンドは `herdr pane run` の1引数として渡す。

## 起動確認

1. `herdr pane split` のJSONから新規 `pane_id` を読む。
2. `herdr pane run <pane-id> '<command>'` を実行する。
3. 対応Agentでは `herdr wait agent-status <pane-id> --status idle --timeout 30000` を使う。
4. 未対応CLIでは期待するプロンプトを `herdr wait output` で待ち、`herdr pane read --source recent-unwrapped --lines 40` でも確認する。
5. trust、login、初期設定などのダイアログがあれば自動承認しない。内容をユーザーへ報告する。

## IDと送信

- pane IDはcloseなどで変化しうる。`agent list`、`agent get`、`pane current`、create/splitレスポンスから都度読む。
- `agent send` と `pane send-text` はEnterを送らない。`pane send-keys <pane-id> Enter` を別に実行する。
- シェルへコマンドを送る時だけ `pane run` を使う。Agentの入力欄へ依頼を送る時はtextとEnterを分離する。
- `agent_status=done` は再利用可能なidleではない。新しい依頼を送らない。

## semantic待機の判定

`agent get` が対象をAgentとして解決し、処理開始後に `working`、完了時に `idle` または `done` を返す場合にsemantic待機を使う。`unknown` のまま安定しないCLIはmarker待機へ切り替える。marker一致だけでは成功とせず、必ず同じtask directoryの `reply.md` も検証する。
