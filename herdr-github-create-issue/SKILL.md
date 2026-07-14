---
name: herdr-github-create-issue
description: >
  Herdr上で確定済みプランのGitHub Issue作成をcagent lowの新規Agentへ委譲し、
  AI Work Metadataと作成結果を確認する。
---

# Herdr GitHub Create Issue

確定済みプランをGitHub Issueへ起票する工程だけを、Herdrの新規paneで起動した安価なIssue作成担当へ同期委譲する。親は現在Agentを壁打ち担当として記録し、作成結果を確認する。壁打ち、プラン補完、再設計は行わない。

## 使用条件と停止条件

- Herdr環境で、ユーザーのIssue作成依頼、対象リポジトリ、会話内の確定済みプランがそろった時だけ使う。確定済みプランは、合意済みの`<proposed_plan>`または同等に最終版と明示された原文全体とする。
- プランがない、未確定、対象リポジトリが不明、またはHerdr / `cagent` / `gh`のpreflightに失敗した場合、paneを作らずに停止する。Grill系スキルまたは設計会話で先にプランを確定するよう案内する。
- `github-issue-create-from-plan`、`coding-agent-subagent`、`herdr-agent-delegate`、`ai-identity-resolve`を事前に読み、後者2つの起動・送信・Completion contractを適用する。本スキル固有の新規pane、責務、cleanup規則を優先する。
- 自動再試行、親による代替起票、別Agentへの切替・再委譲はしない。失敗、`blocked`、timeout、Completion contract違反、作成結果の不一致ではpaneを保持して停止する。

## 1. 役割とメタ情報を確定する

- 親の現在Agentを`壁打ち`、新規paneで起動するAgentを`Issue作成`とする。親を`オーケストレーター`として別行に記録しない。
- 壁打ち担当は、`ai-identity-resolve`に従い、現在の実行環境からAgentとModelを直接取得する。Codexは読める場合に限り`~/.codex/config.toml`の`model`を使う。Effortは実行環境または明示設定から直接取得する。
- Issue作成担当は、`cagent low`のdoctor / dry-runで解決されたAgent、Model、Effortを使う。起動コマンド、Agent種別、既定値からModelやEffortを推測しない。
- 各セルは取得できない時だけ`—`とする。親は両役割の確定値を、起動前にスナップショットとして保持して子へ明示する。

作成Issue本文の最終セクションは必ず次の形にする。追加の最終セクションを置かない。

```markdown
## AI Work Metadata

| Role | Agent | Model | Effort |
| --- | --- | --- | --- |
| 壁打ち | `<agent>` | `<model>` | `<effort>` |
| Issue作成 | `<agent>` | `<model>` | `<effort>` |
```

## 2. Issue作成担当を毎回新規起動する

1. `HERDR_ENV=1`、空でない`HERDR_PANE_ID`、`herdr`、`jq`、`cagent`、`gh`を確認し、`herdr pane current --current`から現在のIDと作業ディレクトリを都度取得する。
2. `coding-agent-subagent`のpreflightを実施する。Agent、Model、Effortは指定せず、task levelだけを`low`と判断して、対話起動コマンドを必ず`cagent low`として解決する。doctor、dry-run、provider / adapterから`base-agent-type`を確認できなければ停止する。
3. 既存idle Agentは検索も再利用もしない。`herdr-agent-delegate`の新規pane配置、ID検証、`herdr pane run`、semantic検出、input-ready確認を順に適用し、今回のIssue作成担当だけを起動する。`agent-command`と`base-agent-type`を混同せず、`pane run`へ`--no-focus`を渡さない。
4. 入力可能確認後にだけ、同スキルの`send_request.py`で依頼をEnter込みで一度だけ送信し、working遷移を確認する。送信失敗時は読み取り専用で状態を回収し、paneを保持して停止する。
5. 送信前に親が、対象cwd、`git status --short`の出力、`git rev-parse HEAD`、現在ブランチとその対象remote refのOIDまたは不存在をスナップショットとして保持する。remote refは実際のremoteから`git ls-remote --heads`で取得する。さらに対象リポジトリで認証ユーザーが作成したIssue一覧とPR一覧を、それぞれ`gh issue list --author @me --state all --limit 1000 --json number,url`、`gh pr list --author @me --state all --limit 1000 --json number,url`で記録する。取得不能なら送信せず停止する。

## 3. Issue作成担当への依頼

依頼には、確定済みプラン原文、対象リポジトリ、両担当のメタ情報表、次をすべて含める。

```text
- $github-issue-create-from-plan を読み、同スキルのIssue生成・作成工程だけを適用すること
- プラン作成、再壁打ち、再設計、プランの補完、HTML確認・生成をしないこと
- 規模に応じてテンプレートを片方だけ選び、既存Labelを確認し、具体例・表・コード・設計判断を保持すること
- 本文を一時ファイルへ書き、gh issue create --body-file で対象リポジトリへ起票すること
- 本文の最後に、親から渡された値をそのまま使う「## AI Work Metadata」表を追加すること。不明セルは — とすること
- gh issue view でURL、title、labels、本文末尾のメタ情報表を確認すること
- 別Agentへの再委譲、実装、commit、push、PR作成をしないこと
- Issue URL、title、labels、確認したメタ情報、未解決事項、ユーザー判断事項を返すこと
- HerdrのCompletion contractに従って結果を確定すること
```

`github-issue-create-from-plan`のプラン提示・モード分岐・HTML確認はこの委譲に含めない。Issue作成担当がプランの内容を変える必要を見つけた場合も起票せず、未解決事項またはユーザー判断事項として返す。

## 4. 完了確認とcleanup

親は対象tabのfocused状態に応じて、HerdrのCompletion contractどおりforegroundでは`idle`、backgroundでは`done`を最大30分待つ。waitの終了理由にかかわらず`herdr pane get`を再取得し、最終状態が`idle`または`done`の場合だけ`recent-unwrapped`の出力を回収する。`working`、`blocked`、`unknown`、取得不能は未完了である。

正常回収後、親は子の報告だけで成功とせず、`herdr pane read --source recent-unwrapped`の実行出力、送信前スナップショット、GitHub側の作成物を照合する。次をすべて直接確認する。

- URL、title、labelsが子の報告と一致する。
- 本文に確定済みプランの必要な具体例と判断が保持されている。
- `gh issue view <url> --json url,title,labels,body`で、本文の最終セクションが`## AI Work Metadata`であり、壁打ちとIssue作成の2行だけを持ち、渡した各セルまたは`—`と一致する。
- 対象cwd、`git status --short`、HEAD、対象remote refのOIDまたは不存在が送信前スナップショットと完全一致する。差分、未追跡ファイル、commit、pushを検出した場合は成功にしない。
- `gh issue list --author @me --state all --limit 1000 --json number,url`の差分は、子が返したURLと一致する今回のIssue 1件だけである。`gh pr list --author @me --state all --limit 1000 --json number,url`は送信前スナップショットと完全一致し、PR作成を検出していない。
- pane出力と子の報告を最後まで読み、再設計、HTML生成、再委譲、実装、commit、push、PR作成の実行または試行がない。出力が欠ける、判定できない、またはGitHub側の作成物を照合できない場合も成功にしない。

Completion contract、回収、上記確認をすべて満たした成功時だけ、親が今回作成したpaneをHerdr公式操作で閉じる。close後は対象paneが閉じたことを確認する。禁止操作の検出、スナップショット不一致、確認不能、失敗、ユーザー判断待ち、cleanup失敗ではpaneを診断用に保持して停止し、既存paneや今回作成していない資源は閉じない。

## 最終報告

成功時はIssue URL、title、labels、確認済みメタ情報、閉じたpaneを返す。停止時はpane ID、状態、失敗箇所、回収出力、作成済みIssueの有無、未解決事項、必要なユーザー判断を返す。

## 品質チェック

- [ ] 確定済みプランがなければpaneを作らない
- [ ] `cagent low`をAgent・Model・Effort無指定で解決し、毎回新規paneへ起動する
- [ ] 2役割のメタ情報を推測せず、Issue本文の最終`## AI Work Metadata`表へ伝達する
- [ ] `github-issue-create-from-plan`のIssue生成・作成工程だけを適用し、既存スキルを変更しない
- [ ] 作業ツリー、HEAD、対象remote ref、GitHubのIssue/PR一覧を送信前後で比較し、禁止操作または確認不能ならpaneを保持して停止する
- [ ] `gh issue view`でURL、title、labels、本文末尾を親が確認する
- [ ] 成功時だけ今回作成したpaneを閉じ、失敗時は保持する
