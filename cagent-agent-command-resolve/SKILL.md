---
name: cagent-agent-command-resolve
description: >
  Herdrなどの上位委譲フローが、cagentでagent、task level、model、effortを解決し、
  実行値を固定したagent-commandと任意の委譲メタ情報を必要とするときに使う。
  pane作成、Agent起動、readiness確認、依頼送信、完了待機は行わない。
---

# Cagent Agent Command Resolve

`cagent` に選択値の解決を任せ、結果を次の4値に分けて返す。

- `base-agent-type`: 入力可能判定・送信・完了判定に使う実体のAgent種別（`codex` / `claude` / `opencode` など）
- `resolved`: cagentが選んだagent ID、表示用Agent名、Model、Effort
- `agent-command`: 解決済みagent ID、Model、Effortを明示した対話起動コマンド
- `delegation-metadata`: 3表示値を同じ起動値へ固定できた場合だけ返すJSON。できなければ`null`

ラッパー名 `cagent` を `base-agent-type` や表示用Agent名として扱わない。

## 責務境界

- このSkillはpreflight、task level判断、`cagent doctor` / `--dry-run`による解決、起動値の固定、4値の返却だけを行う。
- paneの作成・分割・操作、Agent CLIの起動、readiness確認、依頼送信、完了待機、出力回収、cleanupは行わない。
- 上記の実行責務は`herdr-agent-delegate`などの呼び出し側が持つ。

## 1. プリフライト

1. `HERDR_ENV=1` と空でない `HERDR_PANE_ID` を確認する。満たさなければ停止する。
2. `command -v herdr`、`command -v cagent`、`command -v python3`を確認する。自動インストールしない。
3. `cagent --help` を実行し、rootの対話起動、`doctor`、`--dry-run`、`--agent`、`--model`、`--effort`、任意のlevel位置引数が表示されることを確認する。実行失敗または不足があれば、必要なcapabilityを欠く非互換binとして停止する。

いずれかに失敗しても `codex`、`claude`、`opencode` などを直接起動して回避しない。失敗した確認項目と理由を報告する。

## 2. 明示指定を確定する

優先順位を次に固定する。

1. ユーザーが明示し、依頼から理解した `agent` / `level` / `model` / `effort`
2. このSkillによるtask level判断
3. cagent configの `default_agent` / `default_level` / model / effort

ユーザー指定をコスト最適化や独自判断で変更しない。明示された値だけを対応するCLIオプションへ渡す。

- agentの実効値はcagentと同じ `ユーザー明示の --agent > CAGENT_AGENT > config.default_agent` の優先順位で確定する。
- agent未指定: 初回dry-runでは`--agent`を省略する。`CAGENT_AGENT`があればその値、なければ`cagent config path`が示す設定の`default_agent`を実効agent IDとして記録する。
- `base-agent-type` は、この優先順位で選んだ同じagent IDのprovider / adapterから解決する。
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

## 4. 解決値を固定する

選択値に依存するpreflightを順に行う。

1. agent明示時は`cagent --agent <agent> doctor`、未指定時は`cagent doctor`を実行する。終了コードが非0、または`ERROR`があれば停止する。
2. ユーザー明示値と判断したlevelだけを指定した初回`cagent ... --dry-run`を実行し、出力を一時ファイルへ保存する。Agent CLIやpaneは起動しない。
3. doctorで検証した実効agent IDとprovider / adapterから`base-agent-type`を確定する。コマンド名から推測しない。
4. `<skill-dir>/scripts/freeze_resolution.py`へ実効agent ID、`base-agent-type`、level、初回dry-run出力を渡し、検証前の`agent-command`を得る。この時点の`delegation-metadata`は必ず`null`である。
5. `agent-command`と同じ引数へ`--dry-run`を加えて再実行する。初回と検証用の両出力をhelperへ渡し、Agent CLI、Model、Effortが一致した`verified: true`の結果だけを採用する。不一致、非0、解決不能なら停止する。

```bash
<skill-dir>/scripts/freeze_resolution.py \
  --agent-id <resolved-agent-id> \
  --base-agent-type <codex|claude|opencode> \
  --level <level> \
  --dry-run-file <initial-dry-run-output> \
  --verification-dry-run-file <fixed-command-dry-run-output>
```

固定後の例:

```bash
# agent、model、effort、levelを明示
cagent --agent codex --model gpt-5.6-sol --effort high high
```

preflight用の`--dry-run`は実際の`agent-command`に含めない。ModelまたはEffortを解決できない場合も、既定値、task level、Codex Configから補完しない。

## 5. 呼び出し側へ返す

`base-agent-type`、`resolved`、`agent-command`、`delegation-metadata`を分離して返す。呼び出し側は`agent-command`をpaneで起動し、readiness・依頼送信・完了判定には`base-agent-type`を使う。

`delegation-metadata`は、表示用Agent名、Model、Effortがすべて非空で、同じagent ID、Model、Effortが`agent-command`へ明示され、再dry-runで一致した場合だけ次の形で返す。

```json
{"agent":"Codex","model":"gpt-5.6-sol","effort":"high"}
```

1値でも欠ける、表示名へ正規化できない、または起動値へ固定できない場合は全体を`null`にする。`—`、部分JSON、pane/process infoの再調査、Codex Config fallbackを使わない。

通常フローでは `cagent run`、`cagent mux start`、`cagent mux run` を使わない。`cagent` が指定値や設定を解決できない場合も直接CLIへfallbackせず停止する。
