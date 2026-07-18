---
name: ai-identity-resolve
description: >
  レビューコメントやPR返信、PR Work Metadataに付けるAI識別メタデータを解決するときに使う。
  現在のAgentのAgent名・実行モデル・Effortを優先し、取得不能時だけCodex Configへフォールバックする。
---

# 概要

AIレビュー補助コメントに入れるAgent名・モデル名・Effortを、使用時点の実行環境から取得する。
取得元、取得タイミング、値の所有者を分け、取得できない値は推測しない。

## 標準契約

- 呼び出し元スキルへ特定のAgent名、モデル名、Effort、Config値を固定せず、使用時点の現在Agentについて解決する。

## Agent名

- 現在Agent自身のシステムプロンプトにある `You are <name>` から取得する。
- `You are powered by`、対話相手、スキル本文の例示名を現在Agent名として扱わない。

## モデル取得優先順位

現在Agent自身について、使用時点の値を次の順で取得する。別の役割や過去のセッションの値を混ぜない。

1. 現在のAgentセッションが提供する明示的な実行モデル
2. 現在Agentを起動したHerdr/cagentが明示またはdoctor / dry-runで解決した実行モデル
3. 1と2の実行モデルを取得できないCodexに限り、`~/.codex/config.toml` の `model`
4. すべて取得不能なら不明。モデル名を推測しない

会話、依頼、例、古い固定値、Agent種別、既定値からモデル名を推測しない。Herdr/cagentの値は、現在paneの起動に使った明示値または解決値だけを使う。

## Effort取得優先順位

現在Agent自身について、使用時点の値を次の順で取得する。別の役割や過去のセッションの値を混ぜない。

1. 現在セッションが提供する明示的な実行Effort
2. 現在Agentを起動したHerdr/cagentが当該起動について明示またはdoctor / dry-runで解決したEffort
3. 1と2を取得できない通常Codexに限り、当該現在Agentの`~/.codex/config.toml`の`model_reasoning_effort`
4. すべて取得不能なら `—`

非Codex AgentへCodex Configを流用しない。会話、依頼、例、Agent種別、起動コマンド、既定値、別Agent、過去値からEffortを推測しない。Herdr/cagentの値は、現在paneの起動に使った明示値または解決値だけを使う。

## 取得タイミングと所有者

- 現在Agent自身が自身のAgent名・モデル名・Effortの所有者となり、レビューコメントやPR返信を確定する直前に再取得する。会話開始時や過去の取得値を再利用しない。
- 委譲では親が親自身の値の所有者となる。子paneの起動とinput-ready確認、worktree・HEAD・remote ref・Issue/PR一覧など必要な送信前スナップショットを先に完了する。
- 親は送信の最後の準備として、このスキルの優先順位で親自身の識別値を再取得し、cagentで解決済みの子の値とともにハンドオフ時点のメタ情報として固定する。
- 親は固定値を子へ明示する。子は親の識別値を再解決、推測、上書きしない。
- 親自身の識別情報の最終取得完了から `send_request.py` による送信まで、外部I/Oや識別情報の再取得を挟まない。

## PR Work Metadata との整合

- PR 本文の各役割の Agent / Model / Effort は、このスキルの標準契約をそのまま適用する。呼び出し元はModelまたはEffortの優先順位を再定義しない。
- 対象役割の現在Agentが Agent / Model / Effort の値の所有者である。親が PR Work Metadata のスナップショットを記録する場合も、親自身は親の現在値だけをこのスキルで解決し、子役割は Herdr/cagent がその起動に対して明示または解決した実行値だけを記録する。
- オーケストレーターは、親が送信前スナップショットと子 pane の input-ready 確認を終えた後、依頼送信の直前に現在値を再取得して固定する。実装・レビューの値に親の現在値、別 Agent、過去セッション、別 pane の値を混ぜない。
- 実行値を取得できない子役割について、親が自身または別AgentのCodex Configを参照してModelまたはEffortを補完しない。対象役割自身が通常Codexとしてこのスキルを実行する場合だけ、標準契約どおりConfig fallbackを使える。

## 出力

- レビューコメント・PR返信用は、Agent名を取得できた場合に常に `（<agent> / <model-or-—> / <effort-or-—>）` とする。ModelまたはEffortが不明なら、そのセルだけ `—` とする。
- Agent名も取得できなければ、レビューコメント用の識別子は空文字列とする。この場合、ModelやEffortだけで識別子を作らない。
- PR Work MetadataはAgent、Model、Effortを個別セルに記録し、取得不能なセルだけ `—` とする。

## 契約例

- Configが `gpt-5.6-sol` でも、Herdr/cagentの明示実行モデルが `gpt-5.6-terra` なら `gpt-5.6-terra` を使う。
- 通常Codexで実行モデルを取得できず、Configが `gpt-5.6-sol` なら `gpt-5.6-sol` へフォールバックする。
- 通常Codexで実行Effortを取得できず、Configの`model_reasoning_effort`が`high`なら `high` へフォールバックする。
- 非Codex Agentで実行Effortを取得できなければ、Codex Configを読まず `—` とする。
- 実行モデル・EffortとConfig値の両方を取得できなければ、該当セルを `—` とし、推測しない。

## 品質チェック

- [ ] 使用時点の実行モデル・EffortをConfigより優先している
- [ ] 現在Agent自身のAgent名・モデル名・Effortを、契約で定めた所有者が取得している
- [ ] 過去値、他の役割、例示名を使わず、取得不能値を推測していない
