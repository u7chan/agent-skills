---
name: github-pr-orchestrate
description: >
  未コミットの対象変更からcommit・push・GitHub PR作成まで、またはPR作成後のレビューまで一連で完了する依頼に使う。
  未コミット変更がある状態での「PRまで」「PR作ってレビュー依頼出して」などが対象。Herdrでの委譲やpane管理は行わない。
---

# GitHub PR Orchestrate

現在のAgentが、対象変更の確認と品質チェックから限定commit、push、PR作成、明示されたレビュー工程までを継続して統括する。

## ルーティングと責務境界

- 未コミットの対象変更を含むPR完了依頼、またはPR作成と後続レビューをまとめた依頼で起動する。
- PR対象がすべてcommit済みでpush・PR作成だけを求められた場合は、`github-pr-create`を単体で使い、本Skillは起動しない。
- commitだけを求められた場合は`git-changes-commit`、既存PRのレビューだけなら`github-pr-review`を単体で使う。
- 変更の実装や修正は依頼範囲に含まれる場合だけ行う。PR作成準備を理由に無関係な修正を追加しない。
- Herdr、pane、Agent委譲、委譲メタ情報を使用しない。Herdr利用が指定された場合は`herdr-github-pr-orchestrate`へルーティングする。

## 必須ルール

- Issue、会話、差分、変更前の状態から今回の対象pathを確定し、対象外の変更と未追跡ファイルを除外する。
- `main`、`master`、`develop`へ直接commit・pushしない。専用branchか判断できない場合は停止する。
- 品質チェック、commit、PR作成は順序を守り、各工程の成功後だけ次へ進む。
- commitは`git-changes-commit`、pushとPR作成は`github-pr-create`へ委ね、その手順を再定義しない。
- ユーザーが明示したレビュー工程だけを行う。PR作成だけの依頼からレビューやFB対応を推測して追加しない。
- GitHub操作は下位Skillの契約に従い、PR URLと投稿結果を確認する。

## 停止条件

次の場合は、完了済み工程を取り消さず、状態と次に必要な判断を報告して停止する。

- 要求、対象Issue、対象変更、base、専用branchを特定できない。
- 今回の変更を既存・無関係な変更から安全に分離できない。
- 品質チェック、限定commit、push、PR作成、または指定レビュー工程が失敗する。
- 破壊的操作、履歴改変、force push、対象外変更の取り込みが必要になる。
- ユーザー判断が必要な仕様差、レビュー指摘、認証・権限不足が見つかる。

## ワークフロー

### 1. 要求と状態を確認する

- Issueがあれば本文と完了条件を確認し、会話から対象外、PR title/base、レビュー工程の指定を抽出する。
- `git status --short`、branch、remote、base、`BASE..HEAD`、既存PRを確認する。
- 変更開始前の状態または会話上の作業内容と照合し、commit対象と残す変更をpath単位で明示する。
- PR対象がすべてcommit済みでPR作成だけなら`github-pr-create`へルーティングして終了する。

### 2. 品質チェックを完了する

- `AGENTS.md`、プロジェクト設定、IssueのAcceptance Criteriaから必要な検証を解決する。
- 会話内で成功済みの同一HEAD・同一差分に対する検証は再利用できる。不足分だけを実行する。
- 書き込み型formatterを実行する場合は、生成差分が今回の対象か確認し、対象集合を更新する。
- 失敗時は原因が今回の変更にあるかを切り分ける。依頼範囲内で安全に修正できなければ停止する。
- commit直前に`git status --short`と差分を再確認する。

### 3. 今回の変更だけをcommitする

- `../git-changes-commit/SKILL.md`を適用し、対象path、除外path、実施済み検証を渡す。
- 下位Skillが返したcommit hash、commit対象、残存変更を確認する。
- 対象外の変更がcommitまたはstageされた場合は、pushせず停止する。

### 4. pushしてPRを作成する

- `../github-pr-create/SKILL.md`を適用し、Issue、title/base、変更概要、検証結果、完成済み本文があればそれを渡す。
- PR URL、title、base/head、本文、品質チェック結果を確認する。
- 既存PRが返った場合は重複作成せず、そのPRを後続工程の対象にする。

### 5. 指定されたレビュー工程を行う

- レビューが明示されていなければPR作成成功で完了する。
- 「レビューして」「レビュー依頼出して」などPRレビューの実行が明示されていれば、作成済みPRへ`../github-pr-review/SKILL.md`を適用し、投稿結果を確認する。
- reviewerの割り当てが明示された場合は対象accountを特定し、`gh pr edit --add-reviewer`で依頼して結果を確認する。対象を推測できなければ確認する。
- FB対応や再チェックも明示された場合だけ、それぞれ`github-pr-feedback-address`と`github-pr-review`の再チェック契約を適用する。
- レビュー工程が失敗してもPR作成成功と混同せず、PR URLと失敗工程を保持する。

## 最終報告

- 変更概要、commit hash、PR URL、実行した品質チェックと結果を返す。
- commit対象と残した未コミット変更、レビュー・reviewer割り当て・FB対応・再チェックの各状態を区別する。
- 未解決事項、失敗工程、ユーザー判断事項があれば明記する。

## 完了条件

- 今回の変更だけがcommitされ、対象外の変更と未追跡ファイルが保持されている。
- pushとPR作成が成功し、作成済みまたは既存のPRを確認できる。
- ユーザーが指定したレビュー工程まで完了し、指定していない工程を追加していない。
- Herdr、pane、Agent委譲、委譲メタ情報を使用していない。
