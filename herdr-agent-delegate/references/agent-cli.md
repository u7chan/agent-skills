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

入力可能を確認してから、Enter込みの公式操作を直接使う。Herdr 0.7.3 のCLI契約では `herdr agent send <pane-id> "<文字列>"` は文字列入力のみを行いEnterを送らないため、実行開始が必要な依頼送信には使わない。

```bash
herdr pane run <pane-id> "<依頼本文>"
```

送信後は `herdr wait agent-status <pane-id> --status working --timeout 30000` で開始を確認する。30秒以内に `working` へ遷移しなかった場合、同じ依頼の `pane run` 再実行やEnter追送は行わず、`herdr pane get` と `herdr pane read <pane-id> --source recent-unwrapped --lines 80` で状態を取得して報告し、異常を報告してこの依頼の送信を停止する。以降の完了待機や出力回収も行わず、人間の判断を待つ。

## 完了と回収

`herdr tab list` で対象tabの `focused` を確認し、foregroundなら `idle`、backgroundなら `done` を `herdr wait agent-status` で待つ。waitの終了後は成否にかかわらず `herdr pane get` を実行し、最終状態が `idle` または `done` の場合だけ完了として、次を実行する。

```bash
herdr pane read <pane-id> --source recent-unwrapped --lines 120
```

実行可能な分岐と最終確認は `../SKILL.md` の `completion-wait-contract` に従う。waitがtimeoutしても最終状態では `idle` と `done` の双方を完了扱いにし、`working`、`blocked`、`unknown`、取得不能は未完了とする。独自ポーリング、marker、replyファイルによる判定は追加しない。

## 既存Agentの再利用

明示された対象を `herdr agent get` で操作直前に確認し、`idle` の時だけ再利用する。自分自身、`done`、`blocked`、`working`、`unknown` は再利用しない。

pane IDはcloseなどで変化し得る。`agent get`、`pane current`、create/splitレスポンスから都度読む。
