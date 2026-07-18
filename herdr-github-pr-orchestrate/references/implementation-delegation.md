# Herdr 実装委譲契約

作業領域の準備後に読む。pane配置、ID検証、Agent起動、readiness、送信、working確認、完了待機、出力回収は`../../herdr-agent-delegate/SKILL.md`へ一元化し、この文書では手順を再定義しない。本ワークフロー固有の責務境界、Agent選択、成果確認、停止・cleanup契約だけを追加する。

## 1. 責務を分離する

親Agentは要求と完了条件、作業領域を確定し、実装担当1体へ同期委譲する。実装担当は準備済みcwdで、要求範囲の実装と直接関連する検証だけを行う。

実装担当には次を禁止する。

- `herdr-github-pr-orchestrate`の利用
- commit、push、PR作成
- 別Agentへの再委譲
- 指定範囲外の変更や全体品質確認

親Agentは実装を代行せず、結果回収、成果確認、最終検証、限定stage、commit、push、PR作成、後続レビューを統括する。

## 2. 委譲前状態を固定する

- 準備済みcwd、`git status --short`、HEAD OID、対応remote refのOIDまたは不存在を記録する。
- 同じcwdへ書き込む別の実装担当がいないことを確認する。
- Herdr外、必要CLI不足、認証・trust待ち、既存Agentの不存在・非idleは停止条件とする。
- 実装担当の自動切替、自動再試行、親による代替実装は行わない。

## 3. 実装担当を解決する

ユーザー指定を優先する。Agent種別指定なら準備済みcwdで新規起動し、既存Agent名・ID指定なら`herdr agent get <target>`で解決してidleの場合だけ再利用する。指定なしなら現在の親Agentと同じ種別を新規起動する。

自分自身、存在しないAgent、非idle Agentは使わない。新規Agentの配置と起動は`herdr-agent-delegate`へ任せる。新規AgentはIssue番号があれば`implement-issue-<number>`、なければ作業対象が分かる名前へrenameする。既存Agent名は変更しない。

## 4. PR Work Metadata スナップショットを記録する

PR Work Metadata スナップショットとは、PR本文へ渡す役割別のAgent / Model / Effortを固定した記録である。親Agentが記録を管理するが、各値の所有者は対象役割の現在 Agentとする。現在 Agent 以外、別 pane、過去セッションの値を混ぜない。

Agent / Model / Effort は `ai-identity-resolve` の標準契約を適用する。ModelまたはEffortの優先順位はこの文書に再定義しない。子役割の実行値が取得できない場合、親自身や別AgentのCodex ConfigからModelまたはEffortを補完しない。Agent種別、起動コマンド、既定値、過去値から推測しない。

| 役割 | 記録条件 | 固定時点 |
| --- | --- | --- |
| オーケストレーター | 必須 | 実装 pane の input-ready 確認を終え、実装依頼を送る直前 |
| 実装 | 必須 | 実装担当と起動時の解決値を確認した時点 |
| レビュー | 任意 | PR作成前に担当 Agent が会話または解決結果で確定し、値を直接確認できた時点 |
| レビューFB | 任意 | PR作成前に担当 Agent が会話または解決結果で確定し、値を直接確認できた時点 |

必須2役割は全セルが`—`でも行を作る。任意役割はAgent 担当自体が未確定なら行を作らない。取得不能なセルだけ `—` とする。PR作成後に解決した役割を過去の本文へ追加せず、既存のレビューコメント・FB 対応コメントの記録方法も変更しない。

## 5. 実装タスクを渡す

依頼には次を含め、送信・待機・回収は`herdr-agent-delegate`へ任せる。

```text
- 対象Issueまたは実装要求、完了条件、対象外
- 作業ディレクトリの絶対パスと変更可能範囲
- 変更に直接関連する検証
- herdr-github-pr-orchestrateを使わないこと
- commit、push、PR作成、再委譲を行わないこと
- 変更概要、変更ファイル、検証コマンドと結果、未解決事項、ユーザー判断事項を返すこと
- HerdrのCompletion contractに従うこと
```

ユーザー判断事項が返った場合は同じpaneを保持し、親が判断を確認して同じ実装担当へ返す。別Agentや親実装へ切り替えない。

## 6. 親が成果を確認する

- 回収出力に変更概要、変更ファイル、検証、未解決事項、ユーザー判断事項がある。
- 委譲前との差分と未追跡ファイルが要求範囲内で、HEADとremote refが変わっていない。
- 要求と完了条件を満たし、部分実装ではない。
- commit、push、PR作成、再委譲が行われていない。
- 親が変更範囲に必要なformatter、lint、test、buildを実行し、すべて成功する。

親の最終検証が失敗しても親が修正して続行しない。成果確認と最終検証の成功後だけ、新規起動した実装paneを`herdr-agent-delegate`のcleanup契約で閉じる。再利用paneと失敗paneは閉じない。

## 7. 後続工程へ渡す

親Agentは`git-commit-message-suggest`から提案を受け、自身で成果確認済み変更だけを限定stage、commitする。固定済みスナップショットを完成済み`PR_BODY`の最終`## AI Work Metadata`へ渡し、PR作成後は独立したレビュー担当で`review-loop.md`へ進む。
