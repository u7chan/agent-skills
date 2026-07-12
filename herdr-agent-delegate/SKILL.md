---
name: herdr-agent-delegate
description: Herdr上でCLI Agentへタスクを委譲し、公式プリミティブによる1タブあたり最大4paneの配置、送信、完了待機、出力回収を行う。「別Agentに任せて」「複数Agentへ並列委譲」「子Agentの結果を回収」などで使う。
---

# Herdr Agent Delegate

このスキルのディレクトリを `<skill-dir>` として絶対パスで解決する。Agent別の起動・入力可能条件は `references/agent-cli.md` を読む。

## 1. プリフライト

1. `HERDR_ENV=1` と空でない `HERDR_PANE_ID` を確認する。満たさなければHerdr外から対象を推測せず終了する。
2. `command -v herdr`、`command -v jq`、利用するAgent CLIを確認する。自動インストールしない。
3. `herdr pane current --current` から現在の `pane_id`、`workspace_id`、`tab_id`、`cwd` を取得する。IDは応答から都度読み、推測・永続化しない。
4. ユーザー指定がなければ現在のAgent種別とcwdを引き継ぐ。Agent種別も不明なら確認する。起動オプションは明示されたものだけを使う。

## 2. 宛先を解決する

明示的な宛先がある場合だけ既存Agentの再利用を試す。

1. `herdr agent get <target>` で操作直前に解決する。
2. 解決した `pane_id` が自分自身なら拒否する。
3. `agent_status=idle` の時だけ再利用する。`working`、`blocked`、`done`、`unknown` には送信せず報告する。

宛先がない、または存在しない場合は新規Agentを起動する。idleでない明示宛先を無断で新規Agentへ置き換えない。

## 3. 新規paneを配置する

`MAX_PANES_PER_TAB = 4` とし、親と今回この親が作った子だけを配置対象にする。分割順序は次に固定する。

1. 子1: 親を右分割
2. 子2: 子1を下分割
3. 子3: 子2を右分割
4. 子4: 子3を下分割
5. 子5以降: 新規タブで子1から繰り返す

起動数が事前に分かる場合、4体以下は同一タブ、5体以上は `layout_planner.py` の4体単位の結果に従って必要な新規タブを最初に用意する。現在タブに親と今回の子以外のpaneがあれば、体数にかかわらず新規タブを使う。

通常は、現在のgroupで作成済みの子を `--child` で順に渡す。

```bash
<skill-dir>/scripts/split_scoped_pane.py \
  --parent-pane-id "$HERDR_PANE_ID" \
  --cwd <cwd> \
  --child <child-pane-id>
```

事前配置で新しいgroupを始める場合は `--new-tab` を付ける。返却JSONの `pane_id` を子1、`anchor_pane_id` をそのgroupの親として保持し、以後はそのgroup内で同じ固定順序を繰り返す。

スクリプトは最小サイズ不足、4pane超過、無関係pane混在時に新規タブへフォールバックする。分割後は `herdr pane get` で新規paneの `workspace_id` / `tab_id` を検証する。検証失敗時にcloseできるのは今回のsplitが返した新規paneだけで、親・既存の子・無関係paneは操作しない。

## 4. Agentを起動して入力可能まで待つ

1. 分割レスポンスの `pane_id` に対して `herdr pane run <pane-id> '<agent-command>'` を実行する。
2. `herdr wait agent-status <pane-id> --status idle --timeout 30000` を別コマンドで実行する。このidleだけでは入力可能と判定しない。
3. Codex、Claude Code、OpenCodeは次で入力欄を確認する。

```bash
<skill-dir>/scripts/wait_for_input_ready.py \
  --target <pane-id> --agent <codex|claude|opencode>
```

4. その他のCLIは `references/agent-cli.md` の条件を使う。条件が未定義、またはtrust/login/初期設定画面なら自動承認せず停止する。
5. セッション名が指定されていれば `herdr agent rename <pane-id> '<name>'` を実行する。

起動、semantic検出、入力可能確認は別々に行う。バックグラウンド操作には `--no-focus` を使い、別クライアントのフォーカスに依存しない。

## 5. 依頼を直接送る

入力可能を確認した新規Agentには、依頼本文をEnter込みで原子的に送る。

```bash
herdr pane run <pane-id> "<依頼本文>"
```

対応Agentには `herdr agent send <pane-id> "<依頼本文>"` を使ってもよい。既存idle Agentの再利用時も同様に直接送る。送信後は `herdr wait agent-status <pane-id> --status working --timeout 30000` で開始を確認する。依頼ファイル、replyファイル、完了markerは作らない。

## 6. 完了を待って出力を回収する

対象tabのattention stateを確認し、公式のイベント駆動待機を直接使う。`<pane-id>` は回収対象の実際のpane IDへ置き換える。

<!-- completion-wait-contract:start -->
```bash
(
target_pane_id="<pane-id>"
target_pane_json="$(herdr pane get "$target_pane_id")"
target_tab_id="$(printf '%s' "$target_pane_json" | jq -r '.result.pane.tab_id // empty')"
tab_list_json="$(herdr tab list)"
tab_focused="$(printf '%s' "$tab_list_json" | jq -r --arg tab_id "$target_tab_id" \
  '.result.tabs[] | select(.tab_id == $tab_id) | .focused')"

case "$tab_focused" in
  true) wait_status=idle ;;
  false) wait_status=done ;;
  *) exit 1 ;;
esac

wait_rc=0
herdr wait agent-status "$target_pane_id" --status "$wait_status" --timeout 120000 || wait_rc=$?
final_pane_json="$(herdr pane get "$target_pane_id")"
final_status="$(printf '%s' "$final_pane_json" | jq -r '.result.pane.agent_status // empty')"

case "$final_status" in
  idle|done) ;;
  *)
    if [ "$wait_rc" -ne 0 ]; then
      exit "$wait_rc"
    fi
    exit 1
    ;;
esac
)
```
<!-- completion-wait-contract:end -->

foreground tabは `idle`、background tabは `done` を待つ。待機中にattention stateが変わる可能性があるため、waitがtimeoutしても直ちに未完了とせず、最後の `pane get` では `idle` と `done` の双方を完了扱いにする。最終状態が `working`、`blocked`、`unknown`、または取得不能なら完了扱いしない。

完了後は公式の読み取りを直接使う。

```bash
herdr pane read <pane-id> --source recent-unwrapped --lines 120
```

`recent-unwrapped` はソフトラップを結合する。必要な結果を親が統合し、paneは既定で保持する。ユーザーの明示がない限りcloseしない。

## ネストと並列委譲

- 各Agentは直下の子だけを管理する。孫の結果は子が統合して直上の親へ返す。
- 複数の子へ先に依頼を送り、その後に各paneを個別に待つ。
- 追加調査は新しいpaneで行い、既存のworking Agentへ割り込まない。
- 子や孫からrootへ直接通知しない。失敗も直上へ要約して伝播する。

## 禁止事項

- JSON Payload、ファイル交換プロトコル、独自watchdogや完了待機ラッパーを追加しない。
- 自分が作っていないworkspace、tab、pane、sessionをcloseしない。
- 変更操作後のIDを推測せず、JSON応答またはgetコマンドから再取得する。
