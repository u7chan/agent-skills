---
name: github-pr-create
description: >
  PR対象の変更がすべてcommit済みのGitHub PR作成を依頼されたときに使う。「PR作って」「pushしてPR」も対象。
  前提確認、非書き込み品質チェック、push、本文生成、PR作成、結果確認を行い、変更の修正・stage・commitは行わない。
---

# GitHub PR Create

既にcommit済みの変更を品質確認し、`gh`でpushとPR作成を行う。

## 責務境界

- 前提確認、必要な品質チェック、push、PR本文生成、PR作成、結果確認だけを行う。
- ファイル修正、`git add`、`git commit`、amend、rebaseは行わない。
- 未コミットの対象変更からcommitとPR作成まで一連で求められた場合は`github-pr-orchestrate`へルーティングする。
- lint、typecheck、test、buildの失敗を修正しない。失敗内容を報告して停止する。
- formatを含め、未コミット変更を意図的に作る品質確認は実行しない。

## 1. 前提を確認する

- `gh auth status`、対象リポジトリ、remote、現在branch、base branchを確認する。
- `main`、`master`、`develop`上では停止し、作業branchの準備を依頼する。
- `BASE..HEAD`にcommitがなければ停止する。このSkillでcommitを作らない。
- `git status --short`を記録する。既存の未コミット変更をstage、commit、push対象へ混ぜない。
- 既存PRがあればURLを返し、重複作成せず停止する。
- PR本文はファイル経由で渡し、Markdownをシェル引数やコマンド置換へ埋め込まない。

## 2. 必要な品質チェックを実行する

会話で未実施のチェックを`AGENTS.md`、package設定、CI設定から解決する。存在し、この責務境界で安全に実行できるものだけをformat、lint/typecheck、test、buildの順で実行する。

- formatは`format:check`や`prettier --check`等の非書き込みコマンドだけを実行する。`prettier --write`等の書き込み型しか見つからない場合は実行せず、未実施として本文に理由を記録する。
- 実行前後の`git status --short`と`git diff`を比較する。
- いずれかのチェックが失敗した場合は、コマンドとエラー概要を報告して停止する。
- コマンドが見つからない項目は未実施として本文へ記録する。
- すべて成功し、作業ツリーに新しい差分がない場合だけpushへ進む。

## 3. PR本文を用意する

完成済み`PR_BODY`があればそのまま使う。なければcommit差分、Issue、検証結果から次の構造を基本に生成する。

```markdown
## Issues

- Close #123

## Why

変更が必要な背景。

## Summary

変更の要約。

## Changes

- 変更点

## Verification

- `command` - passed
```

- Issueを閉じない関連付けは`Refs #123`とする。
- `Summary`は2〜3文以内とし、何を・なぜに集中する。
- 未実施チェックは未実施理由を明記する。
- 呼び出し側が完成済みの最終セクションを渡した場合、順序や内容を勝手に変更しない。

## 4. pushしてPRを作成する

- upstreamがなければ`git push -u origin <branch>`、あれば通常の`git push`を行う。force pushしない。
- push失敗時は変更を加えず停止する。
- 一時ファイルは常にワーキングディレクトリ配下（. または $PWD）に作成する。/tmp は使わない。
- PR本文を一時ファイルへ保存し、`gh pr create --base <base> --title <title> --body-file <file>`で作成する。
- 対話入力や`--web`を既定にせず、タイトル・base・本文を明示する。

## 5. 結果を確認する

- `gh pr view <branch> --json title,body,url,baseRefName,headRefName`で確認する。
- title、body、base、headが意図した値と一致しなければ、作成済みPR URLと差異を報告して停止する。
- 成功時はPR URL、title、base/head、実行した品質チェックと結果を返す。

## 停止時の報告

失敗した工程、コマンド、エラー概要、既存の未コミット変更、push済みか、PR作成済みか、次に必要な対応を報告する。このSkill自身で修正や追加commitを行わない。
