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
5. edit または auto の場合は、確定済みプランを基に Issue タイトルと本文を作る。
6. edit または auto の場合は、`gh issue create` を実行する。
7. 作成した Issue URL を返す。

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

## 5. Create the Issue / Issue を作成する

- 直前に確定したプランだけを元に Issue を書く。
- Issue タイトルは内容が一目で分かる具体的な文にする。
- モノレポ運用で対象アプリやパッケージが明確な場合、Issue タイトルの先頭に Prefix を付ける。
- Prefix 形式は `[example-app] title example` のように `[scope] summary` を使う。
- 単一リポジトリ、または対象スコープが1つに定まらない場合は Prefix を付けない。
- Issue 作成時は、対象リポジトリで現在設定されている Label 一覧を確認する。
- Label は確認できた候補の中から、Issue 内容に最も合うものだけを選んで付与する。
- 適切な Label が存在しない場合は、存在しない Label 名を新規に仮定して付けない。
- ただし、既存 Label では運用上どうしても不足し、新規作成が妥当な場合は候補 Label 名と用途をユーザーに一度提案してから作成する。
- Issue の性質に合わせてテンプレートの重さを調整する。バグ修正、typo、軽微なリファクタでは、該当しない設計系セクションを削除してよい。
- ただし、軽微な Issue でも `Overview / 概要`、`Tasks / タスク`、`Acceptance Criteria / 完了条件`、`Testing / テスト` は最小限残す。
- 関連情報がない場合は `Related Issues/PRs / 関連Issue・PR` を削除してよい。残す場合は `None` と明記する。
- スコープ外を明示する必要がない軽微な Issue では `Out of Scope / スコープ外` を削除してよい。
- 設計に関する記述が必要な場合は、箇条書きだけで済ませない。次のように対象に合う表現を1つ以上含める。

    | Design target / 対象 | Preferred representation / 推奨表現 |
    | --- | --- |
    | Flow or state transition / フロー・状態遷移 | Mermaid `flowchart` or `stateDiagram-v2` |
    | User/API interaction / ユーザー操作・API連携 | Mermaid `sequenceDiagram` |
    | Database relationship / DB関係 | Mermaid `erDiagram` |
    | Data shape / データ構造 | TypeScript, JSON, SQL, or schema code block |
    | Core logic / 主要ロジック | Source-like pseudocode or small code snippet |

- Issue 本文は次のベーステンプレートを使う。該当しない項目は、上記ルールに従って削除してよい。

    ## Overview / 概要
    <!-- Summarize in about 1–2 lines -->

    ## Objective / 目的
    <!-- What will be gained by completing this task -->

    ## Background / 背景

    ## Related Issues/PRs / 関連Issue・PR

    <!--
    Optional for small typo fixes or trivial refactors.
    Link related issues, PRs, discussions, or external specs.
    If there are no related items, write "None" instead of leaving this ambiguous.
    -->

    ## Implementation Approach / 実装方針

    <!--
    Describe the high-level approach here:
    - Architecture or module boundaries to adopt
    - Libraries, tools, or framework features to use
    - Overall request/user/system flow
    Keep concrete schemas, API contracts, edge-case handling, and detailed logic in Design Details.
    -->

    ## Design Details / 設計詳細

    <!--
    Optional when the issue has no meaningful design detail, such as typo fixes.
    Describe concrete design specifications here:
    - Data structures, schemas, API contracts, and DB relationships
    - Edge-case handling, validation rules, and important branching logic
    - Implementation-level examples needed to remove ambiguity
    Use concrete representations instead of bullet-only prose.
    Choose the most relevant format, such as:
    - Mermaid flowchart or sequence diagram for process and interaction
    - Mermaid ERD for database relationships
    - TypeScript, JSON, SQL, or schema code block for data structures
    - Source-like pseudocode or code snippet for important logic
    -->

    ```mermaid
    flowchart TD
      A[Current behavior] --> B[Required change]
      B --> C[Expected outcome]
    ```

    ```ts
    type ExampleData = {
      id: string;
      status: "draft" | "published";
    };
    ```

    ## Tasks / タスク

    - [ ] Add to ○○
    - [ ] Modify ○○

    ## Out of Scope / スコープ外

    <!--
    Optional for small, self-contained issues.
    Explicitly list work that this issue will not cover.
    This prevents implicit expectations from expanding the review scope.
    -->

    ## Testing / テスト

    ### Validation Policy / 検証方針
    If the implementation task is large, it may be divided into multiple steps.  
    In such cases, if the project has linters or tests configured, make sure that the linter and tests pass at each step.

    ### Documentation / ドキュメント

    <!-- Be sure to update README.md or AGENTS.md if they exist -->

    ## Acceptance Criteria / 完了条件

    <!--
    Define what must be true for this issue to be considered Done.
    These should be observable and reviewable, not vague goals.
    -->

    - [ ] User-facing or developer-facing expected behavior is implemented
    - [ ] If a linter command is configured, it completes successfully
    - [ ] If a test command is configured, it completes successfully
    - [ ] If a formatter command is configured, it completes successfully

    ## Test Perspectives / テスト観点

    | Area / 観点 | What to Verify / 確認内容 | Method / 確認方法 |
    | --- | --- | --- |
    | Normal path / 正常系 | Primary user flow and expected result | Unit, integration, or manual verification |
    | Edge cases / 境界条件 | Empty, missing, invalid, or maximum/minimum inputs | Focused test cases or manual reproduction |
    | Regression / 回帰 | Existing behavior that must not change | Existing tests or targeted smoke checks |
    | Operations / 運用 | Logs, errors, permissions, docs, or migration impact | Command output, UI check, or documentation review |

    ## Notes / 補足

- ユーザーが README や `AGENTS.md` の更新を要求している場合は、そのタスクを本文に明記する。
- `### Documentation / ドキュメント` には README.md や `AGENTS.md` の更新要否を必ず書く。
- `gh issue create` を使い、必要なら対象リポジトリを `--repo` で明示する。
- Label を付ける場合は、事前に確認した既存 Label 名だけを `--label` で明示する。
- 新規 Label が必要な場合は、ユーザー合意前に Label を作成しない。
- `gh issue create` は次の形を優先して使う。

    gh issue create \
      --repo owner/repo \
      --title "Issue title" \
      --body $'## Overview / 概要\n...\n'

- タイトルと本文をコマンド内で明示し、対話入力モードには入らない。

## 6. Report Completion / 完了報告

- Issue URL を返す。
- タイトルと含めた主要論点を1文か2文で要約する。

# Quality Checklist / 品質チェック

- [ ] スキルの説明だけで、プラン作成後に Issue 作成へ進む用途だと分かる
- [ ] plan モードでは `OK` が来る前に `gh issue create` を実行しない
- [ ] edit または auto モードでは切替案内や `OK` 待ちを挟まず `gh issue create` を実行する
- [ ] プランは `<proposed_plan>` ブロックで提示する
- [ ] モノレポ時の Issue タイトル Prefix ルールが明記されている
- [ ] Issue 作成時に既存 Label から選んで付与するルールが明記されている
- [ ] 新規 Label が必要な場合にユーザー提案と合意を先に取るルールが明記されている
- [ ] Issue 本文がベーステンプレートに沿い、軽微な Issue では該当しない項目を削除できる
- [ ] Issue 本文に `Acceptance Criteria / 完了条件` が含まれ、Done の判定条件が明確である
- [ ] 必要な場合は `Out of Scope / スコープ外`、`Related Issues/PRs / 関連Issue・PR` が含まれる
- [ ] 設計説明が必要な場合は、箇条書きだけでなく Mermaid、ERD、コードブロック、擬似コードなどの具体表現を含む
- [ ] ユーザー要求があれば README と `AGENTS.md` 更新が Issue に含まれる
- [ ] 現在モードを判定できない場合は plan モード相当の安全な案内になる
