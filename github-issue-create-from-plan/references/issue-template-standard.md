# Issue Template (Standard)

設計判断や横断的な影響を伴う通常の Issue 向けのフルテンプレート。

## 設計記述ルール

設計に関する記述は箇条書きだけで終わらせない。次の表から対象に合う表現を 1 つ以上選んで含める。

| Design target | Preferred representation |
| --- | --- |
| Flow or state transition | Mermaid `flowchart` or `stateDiagram-v2` |
| User/API interaction | Mermaid `sequenceDiagram` |
| Database relationship | Mermaid `erDiagram` |
| Data shape | TypeScript, JSON, SQL, or schema code block |
| Core logic | Source-like pseudocode or small code snippet |

Plan 原文にサンプル例、コードブロック、表、Mermaid、具体的な入出力例がある場合は、要約で消さずに原文に近い形で残す。主な配置先は `Design Details` とし、補足的な例だけ `Notes` に置く。

## 本文テンプレート

    ## Related Issues / PRs

    <!--
    Link related issues, PRs, discussions, or external specs.
    If there are no related items, write "None" instead of leaving this ambiguous.
    -->

    ## Summary

    <!--
    Summarize the current context, expected outcome, and why this work is needed.
    Keep these points together instead of splitting them into Overview, Objective,
    and Background sections.
    -->

    ## Implementation Approach

    <!--
    Describe the high-level approach here:
    - Architecture or module boundaries to adopt
    - Libraries, tools, or framework features to use
    - Overall request/user/system flow
    Keep concrete schemas, API contracts, edge-case handling, and detailed logic in Design Details.
    -->

    ## Design Details

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

    ## Tasks

    - [ ] Add to ○○
    - [ ] Modify ○○

    ## Out of Scope

    <!--
    Explicitly list work that this issue will not cover.
    This prevents implicit expectations from expanding the review scope.
    -->

    ## Testing

    ### Validation Policy
    If the implementation task is large, it may be divided into multiple steps.
    In such cases, if the project has linters or tests configured, make sure that the linter and tests pass at each step.

    ### Documentation

    <!-- Be sure to update README.md or AGENTS.md if they exist -->

    ## Acceptance Criteria

    <!--
    Define what must be true for this issue to be considered Done.
    These should be observable and reviewable, not vague goals.
    -->

    - [ ] User-facing or developer-facing expected behavior is implemented
    - [ ] If a linter command is configured, it completes successfully
    - [ ] If a test command is configured, it completes successfully
    - [ ] If a formatter command is configured, it completes successfully

    ## Test Perspectives

    | Area | What to Verify | Method |
    | --- | --- | --- |
    | Normal path | Primary user flow and expected result | Unit, integration, or manual verification |
    | Edge cases | Empty, missing, invalid, or maximum/minimum inputs | Focused test cases or manual reproduction |
    | Regression | Existing behavior that must not change | Existing tests or targeted smoke checks |
    | Operations | Logs, errors, permissions, docs, or migration impact | Command output, UI check, or documentation review |

    ## Notes

## 注意事項

- テンプレートの見出し構成と順序に従い、本文は日本語で記述する。
- `Related Issues / PRs` は本文の先頭に置き、関連がなければ `None` と書く。
- 背景、目的、変更概要は `Summary` にまとめ、個別セクションへ分割しない。
- ユーザーが README や `AGENTS.md` の更新を求めている場合は `### Documentation` に明記する。
- 設計記述は表に従い、Mermaid・コードブロック・擬似コードのいずれかを必ず含める。
- Plan 原文のサンプル例、コードブロック、表、Mermaid、具体的な入出力例は削らず、実装判断に必要か迷う場合は残す。
- 本文テンプレート内の Mermaid や TypeScript はプレースホルダーなので、実際の Issue では Plan 原文の具体例で置き換える。
