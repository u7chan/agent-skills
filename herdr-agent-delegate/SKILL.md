---
name: herdr-agent-delegate
description: Herdr上でCodex、Claude Code、OpenCode、その他のCLI Agentへタスクを委譲し、同一TabへのGrid状起動、明示したidle Agentの再利用、依頼送信、完了待機、結果回収まで行う。「別Agentに任せて」「Codex/Claude/OpenCodeを起動して調査」「複数Agentへ並列委譲」「子Agentの結果を回収」など、Herdr内のAgent委譲で使う。
---

# Herdr Agent Delegate

このスキルのディレクトリを `<skill-dir>` として絶対パスで解決する。詳細なCLI差分が必要なら `references/agent-cli.md`、タスクファイルの安全条件やネスト規則が必要なら `references/task-protocol.md` を読む。

## 1. プリフライト

1. `HERDR_ENV=1` と空でない `HERDR_PANE_ID` を確認する。満たさない場合はHerdr外から対象を推測せず終了する。
2. `command -v herdr` と利用するAgent CLIを確認する。自動インストールしない。
3. `herdr pane current --current` を実行し、現在の `pane_id`、`tab_id`、`cwd`、Agent種別を取得する。記憶したIDを使い回さない。
4. ユーザー指定がなければ現在のAgent種別とcwdを引き継ぐ。現在のAgent種別も不明なら起動対象を確認する。起動オプションは明示されたものだけを使う。

## 2. タスク交換を作る

依頼本文を読み取り可能な一時Markdownへ保存し、本文をコマンド引数へ直接埋め込まず次を実行する。追加コンテキストは読み取り可能な絶対パスで繰り返し指定する。

```bash
<skill-dir>/scripts/task_exchange.py create \
  --task-file <request.md> \
  --context-file <absolute-context-path>
```

入力用 `request.md` は、委譲元のワークスペース内の一時領域（例: `.herdr-agent-delegate/` 配下）へ作成し、本文が失われないようにする。`task.md` へのコピーを確認後、入力用に作った `request.md` は削除する。

JSON出力の `task_dir`、`task_path`、`reply_path`、`marker` を保持する。これはCLI結果であり、Agent間Payloadではない。

## 3. 宛先を解決する

明示的な宛先がある場合だけ既存Agentの再利用を試す。

1. `herdr agent get <target>` で毎回解決する。
2. 解決した `pane_id` が自分自身なら拒否する。
3. `agent_status` が `idle` の時だけ再利用する。`working`、`blocked`、`done`、`unknown` には送信せず状態を報告する。

明示的な宛先がない場合、または対象が存在しない場合は同一Tabへ新規Agentを作る。存在するがidleでない明示宛先を無断で新規Agentへ置き換えない。

## 4. 新規AgentをGrid状に起動する

親と「今回この親が起動した子」のpane IDだけを候補にする。無関係な既存paneや再利用Agentは候補へ入れない。

グリッドは `HERDR_DELEGATE_GRID_COLUMNS`（0は自動）、`HERDR_DELEGATE_MIN_PANE_WIDTH`、`HERDR_DELEGATE_MIN_PANE_HEIGHT`、`HERDR_DELEGATE_MAX_PANES_PER_TAB` で制御する。

### 4.1 配置を計画する

バッチ委譲時は起動前に `layout_planner.py` で子数とウィンドウサイズから目標列数・slotを計画する。最小paneサイズを下回る場合は追加分割を停止する。計画を `<task-dir>/delegation-plan.md` に表形式（slot, Agent種別, タスク概要, task dir）で出力し、その後自動実行する。

### 4.2 paneを分割する

1. `herdr pane layout --pane "$HERDR_PANE_ID"` のJSONを一時ファイルへ保存する。
2. 次を実行し、親と同一 `workspace_id`・`tab_id` へ分割されたことを事前・事後に検証済みの新規 pane ID を取得する。子を増やすたび `--child` を追加する。

```bash
<skill-dir>/scripts/split_scoped_pane.py \
  --parent-pane-id "$HERDR_PANE_ID" \
  --task-dir <task-dir> \
  --cwd <cwd> \
  --layout-file <layout.json> \
  --child <child-pane-id>
```

3. 検証済みの新規 pane ID へ `herdr pane run <new-pane-id> '<agent-command>'` だけを実行する。
4. 別コマンドの `herdr wait agent-status <new-pane-id> --status idle --timeout 30000` でsemantic stateによるAgent検出を待つ。この時点の `agent_status=idle` は入力可能を意味しない。
5. セッション名が指定されている場合、`herdr agent rename <new-pane-id> '<session-name>'` で名前を設定する。失敗時は pane と task directory を保持して停止する。
6. Codex、Claude Code、OpenCodeは次を別コマンドで実行し、Agent別の入力欄を `wait output` と `pane read` の両方で確認する。

```bash
<skill-dir>/scripts/wait_for_input_ready.py \
  --target <new-pane-id> --agent <codex|claude|opencode> --task-dir <task-dir>
```

7. その他のCLIは `references/agent-cli.md` の観測可能な入力可能条件を使う。条件が未定義または確認失敗なら、noticeもEnterも送らずpaneとtask directoryを保持して失敗終了する。
8. 分割判断に使ったlayout一時ファイルを削除する。

`split_scoped_pane.py` は検証失敗時に Agent を起動しない。事後検証失敗時は、新規 pane が安全に帰属できる場合だけ `herdr pane close` する。帰属不能または close 失敗時は pane と task directory を保持して停止する。診断情報は `<task-dir>/split_scoped_pane.diagnostics.json` に保存する。

### 4.3 追加調査は新規 Delegation Session

途中で追加調査が必要な場合、既存のplan/sessionは変更しない。新しいsession tagを発行し、単発委譲またはミニバッチplan-firstで新規Agentを起動する。追加調査では既存idle Agentを再利用しない。

### 4.4 最終プレビューを出力する

全バッチ完了後、`<task-dir>/delegation-summary.md` を生成する。含める内容：初期planと実際の配置、完了した子数/失敗・blocked数、追加で生成したsession一覧、保持中のtask directory一覧（失敗時）。

## 5. 依頼を送る

Agentへは短い通知だけを送る。

```text
次の委譲タスクを処理してください: <task_path>
ファイル全文を読み、Completion contractに従って結果を確定してください。
```

新規Agentでは入力可能確認の成功後に限り、対応Agentへの `herdr agent send <target> <notice>`（その他は `herdr pane send-text`）、`herdr pane send-keys <pane-id> Enter`、`working` 遷移確認をこの順の別コマンドで実行する。起動から送信までを `&&` で連結しない。既存idle Agentの再利用でもnoticeとEnterを分け、送信直後にsemantic stateが `working` へ遷移するか、画面が処理開始を示すことを確認する。遷移を確認できなければpaneとtask directoryを保持して失敗終了する。

## 6. 完了を待つ

Codex、Claude Code、OpenCodeなど `agent get` でAgentとして解決できる対象はsemantic待機を使う。

```bash
<skill-dir>/scripts/wait_for_completion.py \
  --target <pane-id> --reply-path <reply-path> semantic
```

未対応CLIはタスク固有markerを待つ。

```bash
<skill-dir>/scripts/wait_for_completion.py \
  --target <pane-id> --reply-path <reply-path> marker --marker <marker>
```

既定timeoutは1時間。長時間待機をバックグラウンド実行できる環境では待機を張って制御を返し、終了後に続行する。`blocked`、`timeout`、`reply_missing` は成功扱いしない。

## 7. 回収する

完了時だけ次を実行する。通常ファイル、所有者、保存ルート、非空を検証して内容を出力し、成功後にtask directoryを削除する。

```bash
<skill-dir>/scripts/task_exchange.py collect --task-dir <task-dir>
```

失敗時はcollectや手動削除をせず、`herdr agent get` と `herdr agent read --source recent-unwrapped --lines 80` で診断する。対象、状態、経過、保持した `task_dir` を報告する。

## ネストと並列委譲

- 各Agentは直下の子だけを管理する。孫は子へ返し、子が統合して親へ返す。
- 子がさらに委譲する時は新しいtask directoryとmarkerを作る。親のものを共有しない。
- 複数子は独立したtask directoryで起動してから個別に待つ。結果の混在を避ける。
- 子や孫からrootへ直接通知しない。失敗も直上へ要約してホップ単位で伝播する。

## 禁止事項

- JSON Payload、グローバルtrace、独自watchdogを追加しない。
- `working` Agentへ割り込まない。ユーザーが明示しても、このスキルでは中断操作を扱わない。
- pane IDを推測・永続化しない。操作直前に再取得する。
- 失敗・blocked・timeout時のtask directoryを削除しない。
