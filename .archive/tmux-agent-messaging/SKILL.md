---
name: tmux-agent-messaging
description: tmuxペイン上のAgent間で、長い指示や応答をJSON Payloadファイルとして安全に非同期配送する。別ペインのAgentへcommand・requestを送り、response・timeout・cleanupを扱う時に使う。
---

# tmux Agent Messaging

この`SKILL.md`の配置ディレクトリを`<skill-dir>`として解決し、`<skill-dir>/scripts/agent-message.sh`を使う。現在の作業ディレクトリからの相対パスで解決しない。tmuxには本文ではなくPayloadの絶対パスだけを送る。`jq`がなければ自動インストールせず、ユーザーへ確認する。

## 前提

1. `TMUX`、`TMUX_PANE`、`jq`を確認する。
2. Payloadの詳細が必要な時だけ`references/payload.schema.json`を読む。
3. 通知されたPayloadは必ず`read`してから処理する。JSONを直接信頼しない。

## 送信

応答不要の指示は`command`、応答が必要な指示は`request`を使う。`--text`と`--text-file`は排他的に指定する。コンテキストは読み取り可能な絶対パスを`--context-file`で繰り返し渡す。

```bash
"<skill-dir>/scripts/agent-message.sh" command --to-pane '%2' --text-file /absolute/path/instruction.md
"<skill-dir>/scripts/agent-message.sh" request --to-pane '%2' --text '調査してください' --timeout-seconds 1800
```

ネストした依頼では、現在処理中のrequestを指定して`traceId`を継承する。

```bash
"<skill-dir>/scripts/agent-message.sh" request --to-pane '%3' --parent-payload /tmp/tmux-agent-messaging/1000/trace-.../requests/msg-....json --text '追加調査'
```

request送信後は入力待ちへ戻る。1つの送信元ペインから同時に保持できる未完了requestは1件だけとする。

## 受信と応答

通知されたパスを`read`へ渡す。誤宛先、symlink、所有者違い、不正フィールドは拒否される。commandは正常に読んだ直後にPayloadが削除される。

```bash
"<skill-dir>/scripts/agent-message.sh" read /tmp/tmux-agent-messaging/1000/trace-.../commands/msg-....json
```

requestへの応答は元のPayloadを指定する。成功時は`completed`、失敗時は`failed`と`--error-code`を使う。

```bash
"<skill-dir>/scripts/agent-message.sh" respond --request /tmp/.../request.json --status completed --text-file /absolute/path/result.md
"<skill-dir>/scripts/agent-message.sh" respond --request /tmp/.../request.json --status failed --error-code execution_failed --text '実行に失敗しました'
```

responseは直上の親ペインへだけ通知する。子孫からrootへ直接通知しない。親がresponseを`read`するとrequestとの対応確認と未完了状態の解除が行われる。失敗を受け取った中間Agentは、自身の親requestへ`failed`で応答し、ホップ単位で伝播する。

## timeoutとcleanup

requestは既定1800秒のwatchdogを起動する。timeout時は子ペインを停止せず、通常responseと同じ保存先をロックして`timeout` responseを確定し、親へ通知する。遅延responseは採用しない。

rootは成功responseを読んで必要な成果物をworkspaceへ移した後、traceを削除する。失敗responseがある場合やresponseの`contextFiles`がtrace配下を参照する場合、cleanupは拒否される。

```bash
"<skill-dir>/scripts/agent-message.sh" cleanup --trace-id trace-...
```

timeout・失敗時はtraceを保持し、対象Agent、経過時間、`/tmp/tmux-agent-messaging/$UID/<traceId>/`をユーザーへ伝えて指示を待つ。
