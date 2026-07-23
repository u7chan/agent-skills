---
name: herdr-agent-delegate
description: Herdr 0.7.5公式APIでCLI Agentを配置し、任意の委譲メタ情報付きで送信・待機・出力回収を行う。「別Agentに任せて」「複数Agentへ並列委譲」「子Agentの結果を回収」などで使う。
---

# Herdr Agent Delegate

`agent-kind`（`codex`/`claude`/`opencode`）と `native-agent-args`（JSON配列）は `cagent-agent-command-resolve` が解決し本Skillは書き換えない。
Agent名は `^[a-z][a-z0-9_-]{0,31}$`、同一workspace内一意必須。委譲メタ情報は3キーが揃った場合だけ `references/delegation-metadata.md` に従い付与。Agent CLIの詳細は`references/agent-cli.md`を読む。

## 禁止事項

- `herdr pane run` でAgent起動しない。`herdr wait agent-status`(旧API)を使わない。
- `herdr agent wait` に `--status` 指定しない。本フローでは `--timeout` のみ。
- working Agentへ追加prompt禁止。1 pane=1 agent、1 agent=1 active task。
- ID推測・キャッシュ・独自watchdog禁止。自分の作ってない資源をcloseしない。

## 1. プリフライト

1. `HERDR_ENV=1`・空でない `HERDR_PANE_ID` 確認
2. `herdr` `jq` `python3` 確認。非インストール
3. `herdr pane current --current` でID/cwd取得。都度読み

## 2. 宛先解決

1. `herdr agent get <target>` で都度解決。自分自身拒否
2. `agent_status=idle` のみ再利用。`working/blocked/done` は報告のみ

## 3. pane配置

`MAX_PANES_PER_TAB=4`(root込み)。初回・再取得ともレイアウトは同一コマンド:

```bash
herdr pane layout --pane <root-pane-id> \
  | <skill-dir>/scripts/layout_planner.py --root-pane-id <root> [--child <child-id>...] [--new-tab]
```

`layout_planner.py` は stdin から Herdr 0.7.5 envelope を受け付け、全ID存在・最小size(40x10)・無関係paneを検証し `use_new_tab` を返す。

`use_new_tab=true` の場合:
1. `herdr tab create --workspace <ws-id> --cwd <cwd> --no-focus`
2. 応答 `result.root_pane.pane_id` を新root、child_ids空リセット
3. `herdr pane layout --pane <new-root>` で再取得、`layout_planner.py` を再実行（--new-tab非付与で無限作成回避）

`use_new_tab=false` の場合、`direction` と `split_target` で分割:

```bash
herdr pane split <split_target> --direction <right|down> --ratio 0.5 --cwd <cwd> --no-focus
```

子1=右、子2=下、子3=右。split失敗は返却paneのみclose後 new-tab fallback。

## 4. Agent起動

`launch_agent.py` が `subprocess.run` で `herdr agent start` を実行し、exit/stdout/stderrを伝播:

```bash
<skill-dir>/scripts/launch_agent.py --name <name> --kind <codex|claude|opencode> \
  --pane-id <pane-id> [--native-args-file <args.json>]
```

`--print-argv` を付けると実行せずJSON argvを出力（検証用）。`native_agent_args` は個別argvとして安全に渡される（eval/@sh禁止）。

## 5. 依頼送信

1. 本文を一時ファイルへ書く。メタ情報完全時は `build_prompt.py` で組立・stdout結果を保存:

```bash
<skill-dir>/scripts/build_prompt.py --prompt-file <tmp> --metadata-json '<JSON>' > <built>
```

不完全時は `--metadata-json` 省略。3キー・非空・`—`拒否検証、失敗時非0。

2. 組立済promptを二重引用符でHerdrへ渡す（単一引用符直接禁止）:

```bash
BUILT="$(cat <built>)"
herdr agent prompt <target> "$BUILT" --wait --until working --timeout 30000
```

`--wait --until working` でworking遷移待機。失敗時は `herdr agent read <target> --source recent-unwrapped --lines 80` で状態取得し停止。

## 6. 完了待機

```bash
herdr agent wait <target> --timeout 1800000
```

standalone waitは `--timeout` のみ（本フロー）。待機後 `herdr agent get <target>` で最終状態:
- `idle`/`done` → 完了
- `blocked` → 中断（停止）
- `working`/`unknown`/取得不能 → 未完了

## 7. 出力回収

```bash
herdr agent read <target> --source recent-unwrapped --lines 120
```

1MB超はファイル保存。pane既定保持。

## 8. 追加操作

```bash
herdr agent send-keys <target> 'Enter'
```

## 9. ネスト・並列委譲

- 各Agentは直下子のみ管理。孫結果は子が統合
- 複数子へ先に `prompt` 送信、後で個別 `wait`
- 並列は同一ファイル非変更時のみ
- 追加調査は新規pane。working Agentへ割込禁止
- 親のメタ情報を孫へ転用しない
