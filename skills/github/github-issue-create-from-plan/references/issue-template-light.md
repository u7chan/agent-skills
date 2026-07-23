# Issue Template (Light)

軽微な修正向けの最小テンプレート。

## 本文テンプレート

    ## Related Issues / PRs

    <!--
    Link related issues or PRs.
    Write "None" if there are no related items.
    -->

    ## Summary
    <!-- Summarize the current context and expected outcome in about 1–3 lines -->

    ## Tasks

    - [ ] Modify ○○

    ## Examples

    <!--
    Include this section only when the confirmed plan contains examples,
    code blocks, tables, Mermaid, or concrete input/output samples.
    Keep those details close to the original wording.
    Place code blocks, tables, Mermaid, or concrete examples here.
    -->

    ## Testing

    ### Validation Policy
    If the project has linters or tests configured, make sure that the linter and tests pass.

    ### Documentation

    <!-- Update README.md or AGENTS.md if needed. Write "None" if not applicable. -->

    ## Acceptance Criteria

    - [ ] Expected behavior is implemented
    - [ ] If a linter command is configured, it completes successfully
    - [ ] If a test command is configured, it completes successfully
    - [ ] If a formatter command is configured, it completes successfully

## 注意事項

- テンプレートの見出し構成と順序に従い、本文は日本語で記述する。
- `Related Issues / PRs` は本文の先頭に置き、関連がなければ `None` と書く。
- `Related Issues / PRs`、`Summary`、`Tasks`、`Acceptance Criteria`、`Testing` は省略しない。
- 軽量テンプレートでは `Implementation Approach`、`Design Details`、`Out of Scope`、`Test Perspectives`、`Notes` は使わない。
- `Examples` は、Plan 原文にサンプル例、コードブロック、表、Mermaid、具体的な入出力例がある場合だけ使う。
- サンプル量が多い、または設計判断を含む場合は Standard テンプレートへ切り替える。
- ユーザーが README や `AGENTS.md` の更新を求めている場合は `### Documentation` に明記する。不要なら `None` と書く。
