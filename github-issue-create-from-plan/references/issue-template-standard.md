# Issue Template (Standard) / 標準Issueテンプレート

設計判断や横断的な影響を伴う通常の Issue 向けのフルテンプレート。

## 設計記述ルール

設計に関する記述は箇条書きだけで終わらせない。次の表から対象に合う表現を 1 つ以上選んで含める。

| Design target / 対象 | Preferred representation / 推奨表現 |
| --- | --- |
| Flow or state transition / フロー・状態遷移 | Mermaid `flowchart` or `stateDiagram-v2` |
| User/API interaction / ユーザー操作・API連携 | Mermaid `sequenceDiagram` |
| Database relationship / DB関係 | Mermaid `erDiagram` |
| Data shape / データ構造 | TypeScript, JSON, SQL, or schema code block |
| Core logic / 主要ロジック | Source-like pseudocode or small code snippet |

Plan 原文にサンプル例、コードブロック、表、Mermaid、具体的な入出力例がある場合は、要約で消さずに原文に近い形で残す。主な配置先は `Design Details / 設計詳細` とし、補足的な例だけ `Notes / 補足` に置く。

## 本文テンプレート

    ## Overview / 概要
    <!-- Summarize in about 1–2 lines -->

    ## Objective / 目的
    <!-- What will be gained by completing this task -->

    ## Background / 背景

    ## Related Issues/PRs / 関連Issue・PR

    <!--
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
    Replace the placeholder examples below with concrete examples from the confirmed plan.
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

## 注意事項

- ユーザーが README や `AGENTS.md` の更新を求めている場合は `### Documentation / ドキュメント` に明記する。
- `Related Issues/PRs / 関連Issue・PR` は関連がなければ `None` と書く。
- 設計記述は表に従い、Mermaid・コードブロック・擬似コードのいずれかを必ず含める。
- Plan 原文のサンプル例、コードブロック、表、Mermaid、具体的な入出力例は削らず、実装判断に必要か迷う場合は残す。
- 本文テンプレート内の Mermaid や TypeScript はプレースホルダーなので、実際の Issue では Plan 原文の具体例で置き換える。
