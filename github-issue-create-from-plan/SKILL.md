---
name: github-issue-create-from-plan
description: >
  合意済み・確定済みの設計プランからテンプレートを選び、GitHub Issueを作成して結果を確認するときに使う。
  プラン作成・再設計・壁打ち・HTML生成は行わない。
---

# GitHub Issue Create From Plan

確定済みプランを内容を落とさずGitHub Issueへ変換し、`gh`で作成して作成結果を確認する。

## 責務境界と停止条件

- 入力は合意済みの`<proposed_plan>`または同等に最終版と明示されたプラン原文とする。
- プラン作成、補完、再設計、合意形成は行わない。未確定事項があればIssueを作らず停止する。
- HTMLの提案、確認質問、生成は行わない。HTML化は`html-artifact-format`への別依頼とする。
- 設計が必要なら`design-plan-grill`などの設計系Skillへの別依頼とする。
- 対象リポジトリ、`gh`認証、確定済みプランのいずれかを確認できなければ停止する。

## ワークフロー

### 1. 入力を確認する

- 対象リポジトリと確定済みプラン原文を確認する。
- サンプル、入出力例、コード、擬似コード、スキーマ、表、Mermaid、具体値、対象外を保持対象として抽出する。
- プランの内容を変える判断が必要なら作成せず、未解決事項として返す。

### 2. テンプレートを1つ選ぶ

判定後に該当ファイルだけを読む。迷う場合はStandardを選ぶ。

| 判定 | 参照ファイル | 基準 |
| --- | --- | --- |
| Light | `references/issue-template-light.md` | typo、文言、命名、小さな単一箇所の修正 |
| Standard | `references/issue-template-standard.md` | 機能・API・DB変更、設計判断、複数ファイル、性能・セキュリティ |

Lightで保持対象が多い、または設計判断を説明する必要があればStandardへ切り替える。

### 3. Issueを作成する

- 選択したテンプレートの見出し順に従い、本文を日本語で書く。
- `Related Issues / PRs`を先頭に置き、関連がなければ`None`とする。
- 確定済みプランの保持対象を要約で消さず、適切なセクションへ移す。
- モノレポでscopeが一意ならタイトルを`[scope] summary`とし、それ以外はprefixを付けない。
- `gh label list`で既存Labelを確認し、明確に合うものだけを使う。新規Labelは作成しない。
- 本文は一時ファイルへ書き、`gh issue create --body-file <file>`で渡す。Markdownをシェル引数へ埋め込まない。
- Mermaidの特殊文字を含むノード・エッジラベルは引用符で囲み、作成前に構文を読み返す。

### 4. 結果を確認する

- `gh issue view <url> --json url,title,body,labels`で作成結果を取得する。
- URL、title、labels、本文が意図した値と一致し、保持対象が欠落していないことを確認する。
- 不一致や確認不能があれば成功扱いせず、作成済みIssueのURLと差異を報告して停止する。

## 出力

- Issue URL、title、labels
- 使用したテンプレート
- 結果確認の成否
- 未解決事項、ユーザー判断事項

HTML生成や追加の確認質問は出力に含めない。
