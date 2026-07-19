---
name: git-changes-commit
description: >
  現在のタスクで作成した変更だけを安全にcommitする依頼、または上位SkillがPR作成前の限定commitを必要とするときに使う。
  差分確認、対象pathの限定stage、commit、結果確認を行い、pushやPR作成は行わない。
---

# Git Changes Commit

現在のタスクに属する変更だけを限定してstageし、1つのcommitを作成する。

## 必須ルール

- 会話の要求、変更前の状態、実装結果、差分から今回の対象pathを確定する。単に作業ツリーに存在するという理由で対象にしない。
- `git add .`、`git add -A`、repository全体を指すpathspec、無関係な整形を使わない。`git add -- <path>...`で対象を明示する。
- 未追跡ファイルは、今回の成果物だと確認できるものだけを対象にする。出自や必要性を判断できないファイルはstageしない。
- 既にstage済みの変更も今回の対象か確認する。対象外のstage済み変更があれば、indexを変更せず停止する。
- commit前にstaged patchとpath一覧が対象集合へ完全一致することを確認する。一致しなければcommitしない。
- 空commit、amend、rebase、push、PR作成は行わない。既存commitや対象外の変更を変更しない。

## 停止条件

次の場合はindexと作業ツリーを勝手に修復せず、対象、差異、必要な判断を報告して停止する。

- 今回の変更と既存・無関係な変更をpath単位またはpatch単位で安全に分離できない。
- 対象外のstage済み変更がある。
- 対象pathを確定できない、または対象に機密情報・生成物など意図不明の内容がある。
- 呼び出し側が必須とした品質チェックが未完了または失敗している。
- stage後の確認で対象外、欠落、意図しない差分が見つかる。

## ワークフロー

### 1. 対象を確定する

- `git status --short`、`git diff --name-status`、`git diff`、`git diff --cached`を確認する。
- 呼び出し側が対象path、実施済み検証、変更前の状態を渡した場合は、それらと実際の差分を照合する。
- 同一pathに今回の変更と無関係な変更が混在し、安全に分離できない場合は停止する。対話的stageを推測で行わない。
- commit対象と除外対象を明示してからstageへ進む。

### 2. commit messageを決める

- `../git-commit-message-suggest/SKILL.md`を適用し、変更目的に合う1案を得る。
- 通常変更はConventional Commits、レビュー指摘対応だけは`fb:`を使う。
- ユーザーがmessageを指定した場合は、明らかな誤りがない限り優先する。

### 3. 限定stageする

- 対象pathだけを`git add -- <path>...`でstageする。
- 削除を含む場合もrepository全体ではなく、削除された対象pathを明示する。
- 対象外のunstaged・untracked変更はそのまま保持する。

### 4. stage結果を検証してcommitする

- `git diff --cached --name-status`と`git diff --cached`を確認する。
- staged pathが対象集合と完全一致し、patchが今回の変更だけであることを確認する。
- `git diff --cached --quiet`なら空commitを作らず停止する。
- 確認済みmessageで`git commit`し、成功した場合だけ結果確認へ進む。

### 5. 結果を確認する

- `git status --short`と`git show --stat --oneline --decorate -1`を確認する。
- commit hash、message、commitしたpath、残した未コミット変更、実施済み検証を返す。
- commit失敗時は、indexと作業ツリーの現在状態、エラー概要、次に必要な対応を返す。

## 完了条件

- 今回の対象pathとcommitされたpath・patchが一致する。
- 無関係な変更と未追跡ファイルがcommitにも新規stageにも含まれない。
- commitが1つ作成され、hash、message、残存変更を確認できる。
- pushとPR作成を行っていない。
