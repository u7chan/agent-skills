---
name: github-issue-create-from-plan
description: >
  ユーザーから設計やプラン作成を求められ、その合意後にGitHub Issueを作成する時に使う。
  まずプランを作成して提示し、現在モードが plan の場合は切替案内を出し、edit または auto の場合はそのまま `gh issue create` を実行する。
---

# Overview / 概要

設計を先に固め、その内容をGitHub Issueへ落とし込むためのスキル。現在モードに応じて、plan では実行前の切替案内を出し、edit または auto では余計な案内を挟まず Issue 作成まで進める。

# When to Use / 使用タイミング

- ユーザーが「まずプランを作って、その後 Issue にしたい」と依頼した時
- ユーザーがプラン合意後に `gh issue create` で起票する運用を求めた時
- ユーザーが現在モードに応じた Issue 作成フローを求めた時

# Agent Responsibilities / Agentが行うこと

1. リポジトリを探索し、要求に関係する実装と制約を把握する。
2. 不明点があればプランに影響する事項だけを確認する。
3. 決定完了なプランを `<proposed_plan>` ブロックで提示する。
4. 現在モードを判断し、plan の場合だけ Edit/Auto への切替案内を出す。
5. edit または auto の場合は、Issue の規模を判定し、`references/` 配下のテンプレートを **片方だけ** 読み込む。
6. edit または auto の場合は、確定済みプランを基に Issue タイトルと本文を作る。
7. edit または auto の場合は、`gh issue create` を実行する。
8. 作成した Issue URL を返す。

# Inputs and Outputs / 入力と出力

## Inputs / 入力

- ユーザーの設計依頼または仕様整理依頼
- リポジトリ内の関連コード、README、AGENTS.md、既存 Issue 文脈
- plan モード時のみ、ユーザーの `OK` 合図

## Outputs / 出力

- `<proposed_plan>` ブロックを含む設計プラン
- plan モード時のみ、Edit/Auto モード切替と Issue 作成待ちを示す短い案内
- 作成済み GitHub Issue の URL

# Detailed Steps / ステップの詳細

## 1. Create the Plan / プランを作る

- まず関連コード、設定、ドキュメントを読む。
- プランに影響する事実は探索で確定する。
- 影響の大きい仕様だけをユーザーに確認する。
- 実装担当者が追加判断なしで着手できる粒度までプランを固める。

## 2. Present the Plan / プランを提示する

- `<proposed_plan>` ブロックで提示する。
- プランには少なくとも要約、主要変更点、テスト観点、前提を含める。
- 設計説明は箇条書きだけで終わらせず、フロー、データ構造、ロジック、DB関係などを最も伝わる具体表現で示す。
- 実装はまだ行わない。

## 3. Respond After Presenting the Plan / プラン提示後の応答

- `<proposed_plan>` の直後に現在モードを見て分岐する。
- plan モードの場合は、`Edit または Auto モードに切り替えてください。切替後に OK と送ってください。` と明示し、ここでは `gh issue create` を実行しない。
- edit または auto モードの場合は、切替案内や `OK` 待ちを挟まず、Issue 作成へ進む。
- 現在モードを判定できない場合は安全側に倒し、plan モードと同じ案内を出す。

## 4. Wait Conditions / 待機条件

- plan モードでは、ユーザーが `OK` と返すまでは Issue を作成しない。
- plan モードで `OK` を受け取った場合は、切替後の edit または auto モードとして Issue 作成へ進む。
- edit または auto モードでは、`OK` を待たずに Issue を作成する。
- plan モードで `OK` 以外の修正依頼が来たら、プラン更新を優先する。

## 5. Choose the Template / テンプレートを選ぶ

Issue の規模に応じて、`references/` 配下のテンプレートを **どちらか片方だけ** 読み込む。両方を同時に読まない。Context を節約するため、判定前にテンプレ本文を投機的に読まない。

判定基準:

| 判定 | 参照ファイル | 適用例 |
| --- | --- | --- |
| Light / 軽量 | `references/issue-template-light.md` | typo、コメント修正、文言変更、命名のみのリファクタ、依存パッケージの軽微なバージョン更新、単一箇所で完結する明らかなバグ修正、ドキュメントの小さな追記 |
| Standard / 標準 | `references/issue-template-standard.md` | 機能追加、API 変更、DB スキーマ変更、設計判断を含む変更、複数ファイル横断の修正、パフォーマンス改善、セキュリティ修正 |

判断に迷う場合は Standard を選ぶ。Light で書き始めて設計説明や Out of Scope が必要だと判明したら、Standard に切り替えて読み直す。

## 6. Create the Issue / Issue を作成する

- 直前に確定したプランと、選んだテンプレートだけを元に Issue を書く。
- Issue タイトルは内容が一目で分かる具体的な文にする。
- モノレポ運用で対象アプリやパッケージが明確な場合、Issue タイトルの先頭に Prefix を付ける。
- Prefix 形式は `[example-app] title example` のように `[scope] summary` を使う。
- 単一リポジトリ、または対象スコープが1つに定まらない場合は Prefix を付けない。
- Issue 作成時は、対象リポジトリで現在設定されている Label 一覧を確認する。
- Label は確認できた候補の中から、Issue 内容に最も合うものだけを選んで付与する。
- 適切な Label が存在しない場合は、存在しない Label 名を新規に仮定して付けない。
- ただし、既存 Label では運用上どうしても不足し、新規作成が妥当な場合は候補 Label 名と用途をユーザーに一度提案してから作成する。
- ユーザーが README や `AGENTS.md` の更新を要求している場合は、本文の `### Documentation / ドキュメント` セクションに明記する。
- `gh issue create` を使い、必要なら対象リポジトリを `--repo` で明示する。
- Label を付ける場合は、事前に確認した既存 Label 名だけを `--label` で明示する。
- 新規 Label が必要な場合は、ユーザー合意前に Label を作成しない。
- `gh issue create` は次の形を優先して使う。

    gh issue create \
      --repo owner/repo \
      --title "Issue title" \
      --body $'## Overview / 概要\n...\n'

- タイトルと本文をコマンド内で明示し、対話入力モードには入らない。

## 7. Report Completion / 完了報告

- Issue URL を返す。
- タイトルと含めた主要論点を1文か2文で要約する。

# Quality Checklist / 品質チェック

- [ ] スキルの説明だけで、プラン作成後に Issue 作成へ進む用途だと分かる
- [ ] plan モードでは `OK` が来る前に `gh issue create` を実行しない
- [ ] edit または auto モードでは切替案内や `OK` 待ちを挟まず `gh issue create` を実行する
- [ ] プランは `<proposed_plan>` ブロックで提示する
- [ ] Issue 規模を判定し、`references/issue-template-light.md` または `references/issue-template-standard.md` のどちらか片方だけを読み込む
- [ ] モノレポ時の Issue タイトル Prefix ルールが明記されている
- [ ] Issue 作成時に既存 Label から選んで付与するルールが明記されている
- [ ] 新規 Label が必要な場合にユーザー提案と合意を先に取るルールが明記されている
- [ ] ユーザー要求があれば README と `AGENTS.md` 更新が Issue に含まれる
- [ ] 現在モードを判定できない場合は plan モード相当の安全な案内になる
