---
name: github-issue-decompose
description: >
  既存のGitHub Issueを本文と全コメントを根拠にレビュー可能な作業単位へ分解し、GitHubネイティブのSub-issueとして登録するときに使う。
  単一Issue作成や合意前の設計作業には使わない。
---

# GitHub Issue Decompose

既存Issueの本文・全コメント・既存Sub-issueを取得し、独立して完了・レビューできる単位へ分解し、GitHubネイティブSub-issueとして登録する。
親IssueはEpicとして要点だけを残し、具体的な作業はSub-issueへ移す。

## 責務境界と停止条件

- 既存Issueの分解とSub-issue登録、親IssueのEpic化だけを行う。
- 単一Issue作成が目的なら`github-issue-create-from-plan`を単体で使い、本Skillは起動しない。
- 合意前の設計・壁打ち・要件補完は行わない。設計が必要なら`design-plan-grill`へ別依頼する。
- Issue本文やコメントにない要件・ブランチ名・依存関係を推測で追加しない。
- 分割単位によって意図やスコープが変わる場合は書き込み前に停止して確認する。
- 途中失敗時は親本文を変更せず、部分結果と復旧対象を報告する。
- 対象リポジトリ、`gh`認証、対象Issueを確認できなければ停止する。

## 必須ルール

- Issue本文やコメントにない要件を推測で追加しない。
- 既存コメントは編集・削除しない。
- 既存Sub-issueと同一目的のIssueを重複作成しない。
- GitHubネイティブのSub-issue関係を正本とし、重複するMarkdownチェックリストは作らない。
- 親Issueの詳細を削る前に、その情報が親またはSub-issueのどこかへ保持されていることを確認する。
- 新しいラベルは作成せず、既存ラベルのうち明確に合うものだけを使う。
- 汎用スキル本文に特定のエージェント製品名を含めない。

## 処理順序: Fetch → Analyze → Preflight → Create → Link → Verify → Compact → FinalVerify

各工程の成功後にだけ次へ進む。失敗時は親本文を変更せず、部分結果と復旧対象を報告して停止する。

### 1. Fetch - 親Issueの情報を取得する

- `gh issue view`で本文・全コメントを取得し、`gh issue list`で既存Sub-issueを取得する。
- コマンドオプションとJSONフィールドの詳細は`references/github-api-details.md`参照。
- 取得データから以下を抽出する: 背景・目的、全体方針、共通制約、完了条件、具体的作業、実装詳細、テスト方法、Phase区分、既存Sub-issue一覧。

### 2. Analyze - 分割案を作成する

- 抽出内容を独立して完了・レビューできる成果物単位へ分割する。
- 分割基準: (1) 独立した成果物、(2) 依存順（明示されたPhaseを優先）、(3) 変更範囲（同一モジュールへの変更は1つにまとめる）。
- 過剰に細分化せず、各Sub-issueが明確なAcceptance Criteriaを持つ単位とする。

### 3. Preflight - 書き込み前の確認を行う

- 書き込み権限を確認する。
- `gh issue edit --help` で `--parent` フラグの存在を確認する。非対応なら書き込み前に停止する。
- 利用するJSONフィールド（`gh issue view --json parent`、`gh issue view --json subIssues`）が取得可能か確認し、非対応なら停止する。
- 既存Sub-issueのタイトル・本文・目的を分割提案と照合し、同一目的の重複を除外する。
- `gh label list`で既存Labelを確認し、各Sub-issueに明確に合うものを特定する。
- 分割案・ラベル割り当て・情報の移動先マッピングを提示し、ユーザー確認を得る。
- 分割単位によって意図やスコープが変わる場合は停止して確認する。

### 4. Create - Sub-issueを作成する

- Preflightで確定した各分割単位を「確定済みプラン」として`github-issue-create-from-plan`へ渡す。
- 既存Skillのテンプレート選択・本文生成・Issue作成・結果確認に任せ、本Skill側で重複実装しない。
- 作成されたIssueのURLと確認結果をLink工程へ引き継ぐ。

### 5. Link - ネイティブSub-issueとして親子付けする

- `gh issue edit <child> --parent <parent>`でGitHubネイティブ親子関係を設定する。
- Markdownチェックリストは作らず、GitHub Sub-issue関係を正本とする。
- 依存順がある場合はSub-issueの作成順をそれに合わせる。

### 6. Verify - 作成結果を再取得して確認する

- 各Sub-issueを`gh issue view --json url,title,body,labels,parent`で再取得する。
- URL、title、labels、本文、親子関係が正しいことを確認する。
- 元の情報が親またはSub-issueのどこかに保持されていることを確認する。
- 確認失敗時は親本文を変更せず、作成済みIssue URLと差異を報告して停止する。

### 7. Compact - 親IssueをEpicへ短縮する

- 全Sub-issueの作成・親子付け・確認が成功した後にだけ実行する。
- 実行前に親Issueの元本文を退避し、復旧に備える。
- 親に残す情報: 背景・目的、全体方針、共通制約、完了条件、Phase区分。
- Sub-issueへ移す情報: 具体的作業、実装詳細、個別Acceptance Criteria、テスト方法。
- `gh issue edit <parent> --body-file`で本文を更新し、Sub-issue progressが保持されることを確認する。

### 8. FinalVerify - 最終確認する

- `gh issue view <parent> --json url,title,body,subIssues`でEpicと全Sub-issue progressを確認する。
- 情報保持、親子関係、ラベルを最終確認する。
- **失敗時の復旧**: Compactで親本文がすでに変更済みのため、以下の手順で復旧する。
  1. 再取得不能、情報欠落、親子不一致の「変更済み」状態を報告する。
  2. 退避した元本文を`gh issue edit <parent> --body-file`で書き戻し、Compact前の状態に復旧する。
  3. 作成済みSub-issue URL（リンク済みの「状態不明」を含む）、復旧操作の成否を報告して停止する。

## 出力

- 親Issue URL、Epic化後のtitle/body概要
- 作成したSub-issue一覧（URL、title、labels、親子関係）
- 情報の移動先マッピング（親→子）
- 未解決事項、ユーザー判断事項
- 部分失敗時は作成済みIssue URLと未完了操作

## 完了条件

- 親IssueがEpicの要点に整理され、詳細情報が失われていない
- 全Sub-issueがGitHubネイティブ親子関係で登録されている
- 既存Sub-issueと重複するIssueが作成されていない
- `github-issue-create-from-plan`と責務が重複していない
- 汎用スキル本文に特定エージェント製品名が含まれていない
