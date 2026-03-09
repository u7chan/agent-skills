---
name: github-issue-create-from-plan
description: >
  ユーザーから設計やプラン作成を求められ、その合意後にGitHub Issueを作成する時に使う。
  まずプランを作成して提示し、その直後にIssue作成へ進む旨を伝え、Editモード切替後にユーザーが "OK" と返したら `gh issue create` を実行する。
---

# 概要

設計を先に固め、その内容を承認フロー付きでGitHub Issueへ落とし込むためのスキル。プラン提示と Issue 作成を分離し、ユーザーの明示的な合図があるまで `gh` を実行しない。

# このスキルを使用するタイミング

- ユーザーが「まずプランを作って、その後 Issue にしたい」と依頼した時
- ユーザーがプラン合意後に `gh issue create` で起票する運用を求めた時
- ユーザーが Edit モードへの切替と、その後の `OK` 合図をワークフローに含めたい時

# Agentが行うこと

1. リポジトリを探索し、要求に関係する実装と制約を把握する。
2. 不明点があればプランに影響する事項だけを確認する。
3. 決定完了なプランを `<proposed_plan>` ブロックで提示する。
4. プラン提示直後に、Issue を作成する旨を短く伝える。
5. Edit モードへ切替可能なら切替を行う。
6. Edit モードを自力で切替できない環境では、ユーザーに切替を促す。
7. ユーザーが `OK` と返すまで `gh` コマンドを実行しない。
8. `OK` 受領後、確定済みプランを基に Issue タイトルと本文を作る。
9. `gh issue create` を実行する。
10. 作成した Issue URL を返す。

# 入力と出力

## 入力

- ユーザーの設計依頼または仕様整理依頼
- リポジトリ内の関連コード、README、AGENTS.md、既存 Issue 文脈
- ユーザーの `OK` 合図

## 出力

- `<proposed_plan>` ブロックを含む設計プラン
- Edit モード切替と Issue 作成待ちを示す短い案内
- 作成済み GitHub Issue の URL

# ステップの詳細

## 1. プランを作る

- まず関連コード、設定、ドキュメントを読む。
- プランに影響する事実は探索で確定する。
- 影響の大きい仕様だけをユーザーに確認する。
- 実装担当者が追加判断なしで着手できる粒度までプランを固める。

## 2. プランを提示する

- `<proposed_plan>` ブロックで提示する。
- プランには少なくとも要約、主要変更点、テスト観点、前提を含める。
- 実装はまだ行わない。

## 3. プラン提示後の応答

- `<proposed_plan>` の直後に次の趣旨を短く返す。
  - `Issueを作成します。`
- その上で Edit モード切替を扱う。
  - 環境が Edit モード切替をサポートする場合は切替する。
  - サポートしない場合は、`Editモードに切り替えてください。切替後に OK と送ってください。` と明示する。

## 4. 待機条件

- ユーザーが `OK` と返すまでは Issue を作成しない。
- `OK` 以外の修正依頼が来たら、プラン更新を優先する。

## 5. Issue を作成する

- 直前に確定したプランだけを元に Issue を書く。
- Issue タイトルは内容が一目で分かる具体的な文にする。
- モノレポ運用で対象アプリやパッケージが明確な場合、Issue タイトルの先頭に Prefix を付ける。
- Prefix 形式は `[example-app] title example` のように `[scope] summary` を使う。
- 単一リポジトリ、または対象スコープが1つに定まらない場合は Prefix を付けない。
- Issue 作成時は、対象リポジトリで現在設定されている Label 一覧を確認する。
- Label は確認できた候補の中から、Issue 内容に最も合うものだけを選んで付与する。
- 適切な Label が存在しない場合は、存在しない Label 名を新規に仮定して付けない。
- ただし、既存 Label では運用上どうしても不足し、新規作成が妥当な場合は候補 Label 名と用途をユーザーに一度提案してから作成する。
- Issue 本文は必ず次のテンプレートを使う。

    ## Overview
    <!-- Summarize in about 1–2 lines -->

    ## Objective
    <!-- What will be gained by completing this task -->

    ## Background

    ## Implementation Approach

    ## Tasks

    - [ ] Add to ○○
    - [ ] Modify ○○

    ## Testing

    If the implementation task is large, it may be divided into multiple steps.  
    In such cases, if the project has linters or tests configured, make sure that the linter and tests pass at each step.

    ### Documentation

    <!-- Be sure to update README.md or AGENTS.md if they exist -->

    ## Acceptance Criteria

    - [ ] If a linter command is configured, it completes successfully
    - [ ] If a test command is configured, it completes successfully
    - [ ] If a formatter command is configured, it completes successfully

    ## Test Perspectives

    ## Notes

- ユーザーが README や `AGENTS.md` の更新を要求している場合は、そのタスクを本文に明記する。
- `### Documentation` には README.md や `AGENTS.md` の更新要否を必ず書く。
- `gh issue create` を使い、必要なら対象リポジトリを `--repo` で明示する。
- Label を付ける場合は、事前に確認した既存 Label 名だけを `--label` で明示する。
- 新規 Label が必要な場合は、ユーザー合意前に Label を作成しない。
- `gh issue create` は次の形を優先して使う。

    gh issue create \
      --repo owner/repo \
      --title "Issue title" \
      --body $'## Overview\n...\n'

- タイトルと本文をコマンド内で明示し、対話入力モードには入らない。

## 6. 完了報告

- Issue URL を返す。
- タイトルと含めた主要論点を1文か2文で要約する。

# 品質チェック

- [ ] スキルの説明だけで、プラン作成後に Issue 作成へ進む用途だと分かる
- [ ] `OK` が来る前に `gh issue create` を実行しない
- [ ] プランは `<proposed_plan>` ブロックで提示する
- [ ] モノレポ時の Issue タイトル Prefix ルールが明記されている
- [ ] Issue 作成時に既存 Label から選んで付与するルールが明記されている
- [ ] 新規 Label が必要な場合にユーザー提案と合意を先に取るルールが明記されている
- [ ] Issue 本文が指定テンプレートどおりである
- [ ] ユーザー要求があれば README と `AGENTS.md` 更新が Issue に含まれる
- [ ] Edit モード非対応環境でも破綻しない手順になっている
