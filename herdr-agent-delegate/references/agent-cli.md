# Agent CLI運用差分

## 起動契約と入力可能確認

`base-agent-type` と `agent-command` を分ける。前者は入力可能判定・送信・完了判定に、後者はpaneでの起動だけに使う。`agent-command` がラッパーでも、実体に対応する `base-agent-type` を使い、実行ファイル名から推測しない。

| `base-agent-type` | 未指定時の直接起動コマンド | `wait_for_input_ready.py` の表示条件 |
| --- | --- | --- |
| `codex` | `codex` | 行頭の入力プロンプト `›` |
| `claude` | `claude` | 行頭の入力プロンプト `❯` |
| `opencode` | `opencode` | 入力欄フッター `ctrl+p commands` |
| その他 | ユーザー指定 | 事前に定義できる固有プロンプト |

別の解決処理から渡された `agent-command` は書き換えない。未指定の場合だけ、`base-agent-type` に対応する直接起動コマンドへユーザー指定の引数を加える。コマンドは `herdr pane run <pane-id> '<command>'` の1引数として送る。`--no-focus` は `herdr pane split` や `herdr tab create` などの pane 配置操作で使うフォーカス制御オプションであり、`herdr pane run` には追加しない。`herdr pane run <pane-id> '<command>'` の後ろに `--no-focus` を付けると `<command>` の引数として解釈され、`codex --no-focus` などで起動に失敗する。

新規起動は次の公式プリミティブを順に使う。

1. `herdr pane split` のJSONから新規 `pane_id` を読む。
2. `herdr pane run <pane-id> '<command>'` でAgentを起動する。
3. `herdr wait agent-status <pane-id> --status idle --timeout 30000` で検出を待つ。
4. `wait_for_input_ready.py` が内部で使う `herdr wait output` と `herdr pane read --source recent-unwrapped` の両方で入力欄を確認する。
5. trust、login、初期設定画面なら自動承認せず、paneを保持して報告する。

## 依頼送信

入力可能を確認してから、Enter込みの公式操作を直接使う。`herdr agent send <pane-id> "<文字列>"` は文字列入力のみを行いEnterを送らないため、実行開始が必要な依頼送信には使わない。Agent種別ごとの差異は `../scripts/send_request.py` で吸収する。

```bash
<skill-dir>/scripts/send_request.py \
  --target <pane-id> \
  --agent <codex|claude|opencode> \
  --prompt "<依頼本文>" \
  --metadata-json '{"agent":"Codex","model":"gpt-5.6-sol","effort":"high"}'
```

`send_request.py` は `herdr pane run` で依頼を送信し、30秒以内の `working` 遷移を待つ。Claude Code のみ、長文ペーストが `[Pasted text #1]` として入力欄に留まることがあるため、活性化用の短いプロンプトを追加送信して再び `working` を待つ。

`--metadata-json`は任意で、起動時に固定したAgent / Model / Effortがすべて揃う場合だけ渡す。スクリプトが標準ブロックを依頼末尾へ追加するため、呼び出し側は手書きしない。出自不明の既存paneでは省略し、snapshotを保持する同じpaneへの再送だけ同じ値を使う。

30秒以内に `working` へ遷移しなかった場合、読み取り専用で状態を取得して報告し、異常を報告してこの依頼の送信を停止する。以降の完了待機や出力回収も行わず、人間の判断を待つ。

```bash
herdr pane get <pane-id>
herdr pane read <pane-id> --source recent-unwrapped --lines 80
```

## 完了と回収

`herdr tab list` で対象tabの `focused` を確認し、foregroundなら `idle`、backgroundなら `done` を `herdr wait agent-status` で待つ。waitの終了後は成否にかかわらず `herdr pane get` を実行し、最終状態が `idle` または `done` の場合だけ完了として、次を実行する。

```bash
herdr pane read <pane-id> --source recent-unwrapped --lines 120
```

実行可能な分岐と最終確認は `../SKILL.md` の `completion-wait-contract` に従う。waitがtimeoutしても最終状態では `idle` と `done` の双方を完了扱いにし、`working`、`blocked`、`unknown`、取得不能は未完了とする。独自ポーリング、marker、replyファイルによる判定は追加しない。

## 既存Agentの再利用

明示された対象を `herdr agent get` で操作直前に確認し、`idle` の時だけ再利用する。自分自身、`done`、`blocked`、`working`、`unknown` は再利用しない。

pane IDはcloseなどで変化し得る。`agent get`、`pane current`、create/splitレスポンスから都度読む。
