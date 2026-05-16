# Issue Template (Light) / 軽量Issueテンプレート

軽微な修正向けの最小テンプレート。

## 本文テンプレート

    ## Overview / 概要
    <!-- Summarize in about 1–2 lines -->

    ## Tasks / タスク

    - [ ] Modify ○○

    ## Examples / サンプル

    <!--
    Include this section only when the confirmed plan contains examples,
    code blocks, tables, Mermaid, or concrete input/output samples.
    Keep those details close to the original wording.
    Place code blocks, tables, Mermaid, or concrete examples here.
    -->

    ## Testing / テスト

    ### Validation Policy / 検証方針
    If the project has linters or tests configured, make sure that the linter and tests pass.

    ### Documentation / ドキュメント

    <!-- Update README.md or AGENTS.md if needed. Write "None" if not applicable. -->

    ## Acceptance Criteria / 完了条件

    - [ ] Expected behavior is implemented
    - [ ] If a linter command is configured, it completes successfully
    - [ ] If a test command is configured, it completes successfully
    - [ ] If a formatter command is configured, it completes successfully

## 注意事項

- `Overview / 概要`、`Tasks / タスク`、`Acceptance Criteria / 完了条件`、`Testing / テスト` は省略しない。
- 軽量テンプレートでは `Background / 背景`、`Implementation Approach / 実装方針`、`Design Details / 設計詳細`、`Out of Scope / スコープ外`、`Test Perspectives / テスト観点`、`Related Issues/PRs / 関連Issue・PR`、`Notes / 補足` は使わない。
- `Examples / サンプル` は、Plan 原文にサンプル例、コードブロック、表、Mermaid、具体的な入出力例がある場合だけ使う。
- サンプル量が多い、または設計判断を含む場合は Standard テンプレートへ切り替える。
- ユーザーが README や `AGENTS.md` の更新を求めている場合は `### Documentation / ドキュメント` に明記する。不要なら `None` と書く。
