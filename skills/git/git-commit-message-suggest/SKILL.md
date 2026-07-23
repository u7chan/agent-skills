---
name: git-commit-message-suggest
description: Gitの変更内容に合うコミットメッセージの提案を依頼されたときに使う。stageやcommitは実行しない。
---

# Git Commit Message Suggest

変更内容を読み取り、Conventional Commits形式のコミットメッセージだけを提案する。

## 責務境界

- 会話、`git status --short`、staged・unstagedの`git diff`から変更の目的と範囲を把握する。
- titleと必要なbodyを提案する。
- `git add`、`git commit`、amend、pushは実行しない。
- ユーザーが提案へ同意しても、自動でstageやcommitを行わない。
- 呼び出し側は提案を受け取り、自身で対象を限定してstageし、commitする。

## ワークフロー

1. 会話に変更目的と範囲が十分あれば、それを優先する。
2. 不足する場合は`git diff --name-status`、`git diff`、必要に応じて`git diff --staged`で差分を確認する。差分と会話のどちらからも提案対象を特定できなければ確認する。
3. 主な変更種別と、モノレポの場合は対象scopeを決める。
4. 次の形式で1案を返す。複数案を求められた場合だけ候補を増やす。

## メッセージ規則

- titleは英語、命令形、小文字始まり、60文字以内を基本とする。
- typeは`feat`、`fix`、`docs`、`style`、`refactor`、`test`、`chore`から選ぶ。
- PRレビュー指摘への対応では変更種別よりfeedback対応を優先し、`fb:`を使う。
- モノレポで対象が一意なら`type(scope): summary`、feedbackなら`fb(scope): summary`にする。
- bodyは必要な場合だけ英語で、何を変えたかと理由を簡潔に書く。

## 出力

```text
<type>(<optional-scope>): <summary>

<optional body>
```

最後に、stageとcommitは呼び出し側が行うことを短く明記する。コマンドの実行や実行確認は行わない。
