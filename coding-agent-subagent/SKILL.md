---
name: coding-agent-subagent
description: >
  Herdr上で設定済みのコーディングエージェントをサブエージェントとして起動するときに使う。
  pane操作を担うHerdr委譲Skillと併用し、cagentでagent、task level、model、effortを解決して、基礎Agent種別と既存pane向け対話起動コマンドを組み立てる。
---

# Coding Agent Subagent

`cagent` に選択と起動を任せ、Herdr の pane 操作は Herdr 委譲側に任せる。結果は必ず次の2値に分ける。

- `base-agent-type`: 入力可能判定・送信・完了判定に使う実体のAgent種別（`codex` / `claude` / `opencode` など）
- `agent-command`: 既存paneで実行する `cagent ...` の対話起動コマンド

ラッパー名 `cagent` を `base-agent-type` として扱わない。

## 1. プリフライト

1. `HERDR_ENV=1` と空でない `HERDR_PANE_ID` を確認する。満たさなければ停止する。
2. `command -v herdr` と `command -v cagent` を確認する。自動インストールしない。
3. `cagent doctor` を実行する。失敗または `ERROR` があれば停止する。
4. doctorで検証済みの設定から、選択対象のagent IDと、そのprovider / adapterに対応する `base-agent-type` を確認する。対応種別を特定できなければ停止する。

いずれかに失敗しても `codex`、`claude`、`opencode` などを直接起動して回避しない。paneを作成・操作する前に失敗理由を報告する。

## 2. 明示指定を確定する

優先順位を次に固定する。

1. ユーザーが明示し、依頼から理解した `agent` / `level` / `model` / `effort`
2. このSkillによるtask level判断
3. cagent configの `default_agent` / `default_level` / model / effort

ユーザー指定をコスト最適化や独自判断で変更しない。明示された値だけを対応するCLIオプションへ渡す。

- agent未指定: agentを推測せず `--agent` を省略し、`default_agent` に任せる。
- model未指定: `--model` を省略する。
- effort未指定: `--effort` を省略する。
- level未指定: 次節で判断し、判断不能な場合だけlevelを省略して `default_level` に任せる。

## 3. task levelを判断する

役割名では固定せず、タスク難度・影響範囲・失敗コストを合わせて判断する。

| Level | 基準 | 例 |
| --- | --- | --- |
| `low` | 小さく反復的で、失敗しても容易にやり直せる | typo、README整形、単純調査、小さな文言修正 |
| `mid` | 通常の実装・保守で、影響範囲が限定的 | 1〜数ファイルの実装、バグ修正、テスト追加、軽いrefactor |
| `high` | 設計判断、広い影響範囲、高い失敗コストを伴う | architecture、認証・DB・CI設計、複雑な障害調査、破壊的変更前review |

通常のreviewを常に `high`、通常の実装を常に `mid` とはしない。根拠を持って分類できない場合はlevelを省略する。

## 4. 対話起動コマンドを組み立てる

次の順で、値が確定した要素だけを追加する。levelは位置引数にする。

```bash
cagent [--agent <agent>] [--model <model>] [--effort <effort>] [<level>]
```

例:

```bash
# agent未指定、通常実装
cagent mid

# agentとlevelを明示
cagent --agent opencode-go high

# agent、model、effort、levelを明示
cagent --agent codex --model gpt-5.6-sol --effort high high

# levelを判断できないためconfigへ委ねる
cagent
```

agent未指定でも、doctorで検証された `default_agent` のprovider / adapterから `base-agent-type` を解決する。`agent-command` の実行ファイル名から推測しない。

## 5. Herdr委譲へ渡す

`base-agent-type` と `agent-command` を分離したまま渡す。Herdr委譲側は `agent-command` を既存paneで起動し、readiness・依頼送信・完了判定には `base-agent-type` を使う。

通常フローでは `cagent run`、`cagent mux start`、`cagent mux run` を使わない。`cagent` が指定値や設定を解決できない場合も直接CLIへfallbackせず停止する。
