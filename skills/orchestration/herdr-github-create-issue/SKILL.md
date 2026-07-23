---
name: herdr-github-create-issue
description: >
  Herdr上で確定済みプランのGitHub Issue作成をcagent lowの新規Agentへ委譲し、
  利用可能な委譲snapshotのAI Work Metadataと作成結果を確認する。
---

# Herdr GitHub Create Issue

確定済みプランをGitHub Issueへ起票する工程だけを、Herdrの新規paneで起動した安価なIssue作成担当へ同期委譲する。親は有効な委譲snapshotがある役割だけを記録し、作成結果を確認する。壁打ち、プラン補完、再設計は行わない。

## 使用条件と停止条件

- Herdr環境で、ユーザーのIssue作成依頼、対象リポジトリ、会話内の確定済みプランがそろった時だけ使う。確定済みプランは、合意済みの`<proposed_plan>`または同等に最終版と明示された原文全体とする。
- プランがない、未確定、対象リポジトリが不明、またはHerdr / `cagent` / `gh`のpreflightに失敗した場合、paneを作らずに停止する。Grill系スキルまたは設計会話で先にプランを確定するよう案内する。
- `github-issue-create-from-plan`、`cagent-agent-command-resolve`、`herdr-agent-delegate`を事前に読む。cagentの解決は`cagent-agent-command-resolve`、pane配置・起動・送信・完了待機は`herdr-agent-delegate`を適用する。本スキル固有の責務とcleanup規則を優先する。
- 自動再試行、親による代替起票、別Agentへの切替・再委譲はしない。失敗、`blocked`、timeout、`herdr agent wait`違反、作成結果の不一致ではpaneを保持して停止する。

## 1. 役割とメタ情報を確定する

- 親の現在Agentを`壁打ち`、新規paneのAgentを`Issue作成`とする。親を`オーケストレーター`として別行にしない。
- 壁打ち行は、親の現在の委譲指示末尾に有効な標準suffixがある場合だけ、その3値で作る。単体実行またはHerdr直接起動のrootには作らない。
- Issue作成行は、`cagent low`で解決した3値を同じ`agent-kind`・`native-agent-args`へ固定できた場合だけ作る。同じJSONを標準ブロックとして依頼末尾へ付与する。
- 部分行、`—`、pane/process info調査、Codex Config fallback、他役割からの補完を禁止する。行が1件もなければ`## AI Work Metadata`セクション自体を作らない。

有効な役割行がある場合、作成Issue本文の最終セクションは次の形にする。追加の最終セクションを置かない。

```markdown
## AI Work Metadata

| Role | Agent | Model | Effort |
| --- | --- | --- | --- |
| `<metadata-backed role>` | `<agent>` | `<model>` | `<effort>` |
```

## 2. Issue作成担当を毎回新規起動する

1. `HERDR_ENV=1`、空でない`HERDR_PANE_ID`、`herdr`、`jq`、`cagent`、`gh`を確認し、`herdr pane current --current`から現在のIDと作業ディレクトリを都度取得する。
2. `cagent-agent-command-resolve`のpreflightを実施する。Agent、Model、Effortは指定せずtask levelを`low`とし、doctor / dry-runで実効3値を解決する。同じ3値を明示した`agent-kind`、`native-agent-args`、任意の`delegation-metadata`を得る。起動自体を解決できなければ停止する。
3. 既存idle Agentは検索も再利用もしない。`herdr-agent-delegate`の新規pane配置、ID検証、`launch_agent.py`起動、送信を順に適用し、今回のIssue作成担当だけを起動する。`agent-kind`と`native-agent-args`を混同せず、`launch_agent.py`へ`--native-args-file`で渡す。
4. Agent起動後、親が次の順で送信前処理を完了する。スナップショット取得に失敗した場合は送信せずpaneを保持して停止する。
   1. 親が、対象cwd、`git status --short`の出力、`git rev-parse HEAD`、現在ブランチとその対象remote refのOIDまたは不存在を送信前スナップショットとして保持する。remote refは実際のremoteから`git ls-remote --heads`で取得する。さらに対象リポジトリで認証ユーザーが作成したIssue一覧とPR一覧を、それぞれ`gh issue list --author @me --state all --limit 1000 --json number,url`、`gh pr list --author @me --state all --limit 1000 --json number,url`で記録する。
   2. 現在の親タスクに有効な標準suffixがあれば壁打ち行を、cagentの`delegation-metadata`があればIssue作成行を固定する。どちらもなければ空とする。
   3. 確定済みプラン原文、対象リポジトリ、固定した行、送信指示を組み立て、`herdr agent prompt`で一度だけ送信する。Issue作成担当の完全なsnapshotがある場合だけ送信前に標準ブロックをプロンプト末尾へ付与し、標準ブロックは手書きしない。送信失敗時は読み取り専用で状態を回収し、paneを保持して停止する。

## 3. Issue作成担当への依頼

依頼には、確定済みプラン原文、対象リポジトリ、有効な役割行だけを持つメタ情報表、次をすべて含める。

```text
- $github-issue-create-from-plan を読み、同スキルのIssue生成・作成工程だけを適用すること
- プラン作成、再壁打ち、再設計、プランの補完、HTML確認・生成をしないこと
- 規模に応じてテンプレートを片方だけ選び、既存Labelを確認し、具体例・表・コード・設計判断を保持すること
- 本文を一時ファイルへ書き、gh issue create --body-file で対象リポジトリへ起票すること
- 親から1件以上の役割行が渡された場合だけ、本文の最後に値をそのまま使う「## AI Work Metadata」表を追加すること。部分行や — は作らないこと
- gh issue view でURL、title、labels、適用時の本文末尾メタ情報表を確認すること
- 別Agentへの再委譲、実装、commit、push、PR作成をしないこと
- Issue URL、title、labels、確認したメタ情報、未解決事項、ユーザー判断事項を返すこと
- Herdrのwaitで結果を確定すること
```

`github-issue-create-from-plan`の責務どおり、プラン作成・再設計・HTML確認や生成はこの委譲に含めない。Issue作成担当がプランの内容を変える必要を見つけた場合も起票せず、未解決事項またはユーザー判断事項として返す。

## 4. 完了確認とcleanup

親は`herdr-agent-delegate`の完了待機契約に従い、`herdr agent wait <target> --timeout 1800000`で最大30分待つ。`herdr agent get <target>`で最終状態を再取得し、`idle`または`done`を完了扱い、`blocked`/`working`/`unknown`/取得不能は未完了。完了後`herdr agent read`で出力回収。

正常回収後、親は子の報告だけで成功とせず、`herdr agent read --source recent-unwrapped`の実行出力、送信前スナップショット、GitHub側の作成物を照合する。次をすべて直接確認する。

- URL、title、labelsが子の報告と一致する。
- 本文に確定済みプランの必要な具体例と判断が保持されている。
- `gh issue view <url> --json url,title,labels,body`で、有効な役割行がある場合は本文の最終セクションが`## AI Work Metadata`で渡した行だけを持ち、ない場合は同セクションが存在しない。
- 対象cwd、`git status --short`、HEAD、対象remote refのOIDまたは不存在が送信前スナップショットと完全一致する。差分、未追跡ファイル、commit、pushを検出した場合は成功にしない。
- `gh issue list --author @me --state all --limit 1000 --json number,url`の差分は、子が返したURLと一致する今回のIssue 1件だけである。`gh pr list --author @me --state all --limit 1000 --json number,url`は送信前スナップショットと完全一致し、PR作成を検出していない。
- pane出力と子の報告を最後まで読み、再設計、HTML生成、再委譲、実装、commit、push、PR作成の実行または試行がない。出力が欠ける、判定できない、またはGitHub側の作成物を照合できない場合も成功にしない。

`herdr agent wait`による完了確認、回収、上記確認をすべて満たした成功時だけ、親が今回作成したpaneをHerdr公式操作で閉じる。close後は対象paneが閉じたことを確認する。禁止操作の検出、スナップショット不一致、確認不能、失敗、ユーザー判断待ち、cleanup失敗ではpaneを診断用に保持して停止し、既存paneや今回作成していない資源は閉じない。

## 最終報告

成功時はIssue URL、title、labels、確認済みメタ情報、閉じたpaneを返す。停止時はpane ID、状態、失敗箇所、回収出力、作成済みIssueの有無、未解決事項、必要なユーザー判断を返す。

## 品質チェック

- [ ] 確定済みプランがなければpaneを作らない
- [ ] `cagent low`をAgent・Model・Effort無指定で解決し、実効3値を固定したコマンドで毎回新規paneへ起動する
- [ ] 有効な委譲snapshotのある役割だけをIssue本文末尾の`## AI Work Metadata`へ伝達する
- [ ] `github-issue-create-from-plan`のIssue生成・作成工程だけを適用し、既存スキルを変更しない
- [ ] 作業ツリー、HEAD、対象remote ref、GitHubのIssue/PR一覧を送信前後で比較し、禁止操作または確認不能ならpaneを保持して停止する
- [ ] `gh issue view`でURL、title、labels、適用時の本文末尾メタ情報を親が確認する
- [ ] 成功時だけ今回作成したpaneを閉じ、失敗時は保持する
