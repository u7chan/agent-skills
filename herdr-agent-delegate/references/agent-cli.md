# Agent CLI運用差分

## 起動契約

`agent-kind`（`codex`/`claude`/`opencode`）と `native-agent-args`（JSON配列）は `../../cagent-agent-command-resolve/SKILL.md` の `freeze_resolution.py` が解決。本Skillは書き換えない。

`agent-kind` を実行ファイル名から推測しない。

## Agent起動

`launch_agent.py` が `subprocess.run` で `herdr agent start` を直接実行しexit/stdout/stderrを伝播:

```bash
<skill-dir>/scripts/launch_agent.py --name <name> --kind <kind> --pane-id <id> [--native-args-file <args.json>]
```

`--print-argv` を付けると実行せずJSON argv出力（検証用）。`native-args-file` = freeze_resolution `native_agent_args` JSON配列。双方向対話可能なinteractive readiness保証。失敗時pane保持・報告。

eval/@sh禁止。`--no-focus` はpane配置操作用、`agent start` に追加不可。

## 依頼送信

1. 本文を一時ファイルへ書く。メタ情報完全時は `build_prompt.py` で組立:

```bash
<skill-dir>/scripts/build_prompt.py --prompt-file <tmp> --metadata-json '<JSON>' > <built>
```

3キー完全・非空・`—`拒否検証。不完全時 `--metadata-json` 省略。

2. 組立済プロンプトを二重引用符で送信（単一引用符直接禁止）:

```bash
BUILT="$(cat <built>)"
herdr agent prompt <target> "$BUILT" --wait --until working --timeout 30000
```

`--wait --until working` でworking遷移待機。失敗時 `herdr agent read` で状態取得し停止。

## 完了と回収

```bash
herdr agent wait <target> --timeout 1800000
```

本フローでは `--timeout` のみ指定。待機後 `herdr agent get <target>` で最終状態（pane ID保持時のみ `pane get` 可）。`idle`/`done`→完了。

```bash
herdr agent read <target> --source recent-unwrapped --lines 120
```

1MB超はファイル保存。独自ポーリング/marker/replyファイル禁止。

## 追加操作

```bash
herdr agent send-keys <target> 'Enter'
```

working Agentへ追加prompt禁止。

## 既存Agent再利用

`herdr agent get` で都度確認。`idle` 時のみ再利用。IDは都度読み。
