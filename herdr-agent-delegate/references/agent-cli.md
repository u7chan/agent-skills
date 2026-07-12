# Agent CLI運用差分

## 起動と入力可能確認

| Agent | 起動コマンド | `wait_for_input_ready.py` の表示条件 |
| --- | --- | --- |
| Codex | `codex` | 行頭の入力プロンプト `›` |
| Claude Code | `claude` | 行頭の入力プロンプト `❯` |
| OpenCode | `opencode` | 入力欄フッター `ctrl+p commands` |
| その他 | ユーザー指定 | 事前に定義できる固有プロンプト |

ユーザー指定の引数だけを起動コマンドへ渡す。コマンドはシェル文字列を組み立てず、`herdr pane run <pane-id> '<command>'` の1引数として送る。

新規起動は次の公式プリミティブを順に使う。

1. `herdr pane split` のJSONから新規 `pane_id` を読む。
2. `herdr pane run <pane-id> '<command>'` でAgentを起動する。
3. `herdr wait agent-status <pane-id> --status idle --timeout 30000` で検出を待つ。
4. `wait_for_input_ready.py` が内部で使う `herdr wait output` と `herdr pane read --source recent-unwrapped` の両方で入力欄を確認する。
5. trust、login、初期設定画面なら自動承認せず、paneを保持して報告する。

## 依頼送信

入力可能を確認してから、Enter込みの公式操作を直接使う。

```bash
herdr pane run <pane-id> "<依頼本文>"
# または対応Agentへ
herdr agent send <pane-id> "<依頼本文>"
```

送信後は `herdr wait agent-status <pane-id> --status working --timeout 30000` で開始を確認する。

## 完了と回収

```bash
herdr wait agent-status <pane-id> --status done --timeout 120000
herdr pane read <pane-id> --source recent-unwrapped --lines 120
```

foreground tabのAgentは完了時に `idle`、background tabでは `done` になり得る。どちらも意味的に完了であり、常に双方を完了扱いにする。独自ポーリング、marker、replyファイルによる判定は追加しない。

## 既存Agentの再利用

明示された対象を `herdr agent get` で操作直前に確認し、`idle` の時だけ再利用する。自分自身、`done`、`blocked`、`working`、`unknown` は再利用しない。

pane IDはcloseなどで変化し得る。`agent get`、`pane current`、create/splitレスポンスから都度読む。
