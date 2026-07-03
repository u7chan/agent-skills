# Agent CLI運用差分

## 起動コマンド

| Agent | 起動コマンド | 完了待機 |
| --- | --- | --- |
| Codex | `codex` | semantic state |
| Claude Code | `claude` | semantic state |
| OpenCode | `opencode` | semantic state |
| その他 | ユーザー指定のコマンド | output marker。`agent get` が安定して識別できる場合だけsemantic state |

ユーザーが指定した引数は該当コマンドへ渡す。指定されていない引数を補わない。シェル展開が必要な文字列を組み立てず、コマンドは `herdr pane run` の1引数として渡す。

## 新規起動の入力可能確認

1. `herdr pane split` のJSONから新規 `pane_id` を読む。
2. `herdr pane run <pane-id> '<command>'` を実行する。
3. 対応Agentではsemantic stateで対象Agentが検出されるまで待つ。`agent_status=idle` だけでは入力可能と判定しない。
4. `wait_for_input_ready.py` で次の表示を `herdr wait output` と直後の `pane read` の両方から確認する。

| Agent | 新規起動時の入力可能表示 |
| --- | --- |
| Codex | 行頭の入力プロンプト `›` |
| Claude Code | 行頭の入力プロンプト `❯` |
| OpenCode | 入力欄フッター `ctrl+p commands` |

5. trust、login、初期設定などのダイアログがあれば自動承認しない。入力可能失敗としてpaneとtask directoryを保持し、内容を報告する。

新規起動では `pane run`、semantic検出、入力可能確認、notice送信、Enter送信、`working` 遷移確認を別々に実行する。入力可能を確認できなければnoticeもEnterも送らない。未対応CLIは観測可能な固有プロンプトを事前に定義できる場合だけ同じ二重確認を行い、未定義なら失敗とする。

## 既存idle Agentの再利用

明示指定された既存Agentは、`herdr agent get` で操作直前に `idle` と確認できれば再利用できる。すでに起動済みのTUIなので新規起動用の入力可能待機は行わない。ただしnotice送信とEnter送信は分離し、直後の `working` 遷移を必ず確認する。`done`、`blocked`、`working`、`unknown` は再利用しない。

## IDと送信

- pane IDはcloseなどで変化しうる。`agent list`、`agent get`、`pane current`、create/splitレスポンスから都度読む。
- `agent send` と `pane send-text` はEnterを送らない。`pane send-keys <pane-id> Enter` を別に実行する。
- シェルへコマンドを送る時だけ `pane run` を使う。Agentの入力欄へ依頼を送る時はtextとEnterを分離する。
- 新規起動の工程を単一の `&&` チェーンにまとめない。各観測結果を確認してから次へ進む。

## semantic待機の判定

`agent get` が対象をAgentとして解決し、処理開始後に `working`、完了時に `idle` または `done` を返す場合にsemantic待機を使う。`unknown` のまま安定しないCLIはmarker待機へ切り替える。marker一致だけでは成功とせず、必ず同じtask directoryの `reply.md` も検証する。
