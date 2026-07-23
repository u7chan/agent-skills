---
name: herdr-github-pr-orchestrate
description: >
  GitHub Issueや実装タスクについて、Issue確認、作業領域準備、Herdr Agentへの実装委譲、成果確認、
  共通Skillによる限定commit・PR作成、レビュー、FB対応、再チェックを統括するときに使う。
  pane配置、送信、待機、出力回収の詳細はherdr-agent-delegateへ委ねる。
---

# Herdr GitHub PR Orchestrate

Issue または実装指示を受け、実装担当 Agent への委譲から PR 作成後のレビュー結果と対応状況まで管理する。既存スキルがある工程では、そのスキルを読んで適用する。ユーザーが作業方式を明示しない限り、現在の作業ツリーに専用ブランチを作り、停止条件に当たるまで確認を挟まず進める。

## 必須ルール

- 既存コード、Issue、会話から要求と完了条件を読み取る。探索で解決できる不明点は質問しない。
- `main`、`master`、`develop` へ直接実装・push しない。既存ブランチや worktree は今回専用だと判断できる場合だけ再利用する。
- 無関係な未コミット変更を取り込まず、今回の変更だけを stage、commit する。
- PR 操作、レビュー投稿、返信は `gh` / `gh api` を使う。GitHub コネクタは使わない。
- Markdown の長文はファイル経由で渡す。本文をシェル引数やコマンド置換へ直接埋め込まない。
- PR作成時点で有効な委譲snapshotが1件以上ある場合だけ、PR本文末尾へ`## AI Work Metadata`を付ける。メタ情報のないrootオーケストレーター行は作らない。
- 作業領域の準備後は Herdr で 1 体の実装担当 Agent へ同期委譲する。親 Agent は実装せず、成果確認と最終検証後に commit、push、PR 作成を行う。
- 実装担当とレビュー担当は役割ごとに独立して解決する。指定のない役割は現在動作しているエージェントと同じ種別を新規起動する。ユーザーが明示的に指定した場合はその種別を優先する。
- PR 作成後は Herdr で同期レビューし、親 Agent が指摘の分類、FB 対応の成果確認、再チェック、pane cleanup まで管理する。
- pane配置、Agent起動、依頼送信、完了待機、出力回収は`herdr-agent-delegate`の契約を適用し、本Skillでは再定義しない。
- 限定stage・commitは`git-changes-commit`、push・PR作成は`github-pr-create`の契約を適用し、本Skillでは共通手順を再定義しない。
- 実装委譲の失敗では自動再試行、親による代替実装、別 Agent への切り替えを行わない。
- レビュー、FB 対応、再チェックの失敗を PR 作成失敗と混同しない。自動再試行、Herdr 外での代替実行はしない。ただし再チェックで対応可能な残件が返った場合は失敗扱いにせず、規定の次FBラウンドとして別の新規Agentセッションへ委譲する。

## 参照するスキル

- worktree: `herdr-worktree-create`
- ブランチ: `git-branch-create`
- 限定stage / commit: `git-changes-commit`
- push / PR 作成: `github-pr-create`
- Herdr 委譲: `herdr-agent-delegate`
- cagent解決: `cagent-agent-command-resolve`
- レビュー / 再チェック: `github-pr-review`
- FB 対応: `github-pr-feedback-address`

実装前に `references/implementation-delegation.md`、PR 作成後に `references/review-loop.md` を必ず読む。各ファイルの Agent 解決、タスク内容、成果確認、pane 管理に従う。

## 停止条件

次の場合は停止し、現在の状態、理由、必要な判断を報告する。

- 要求、完了条件、対象リポジトリ、対象 Issue を特定できない。
- 破壊的操作、履歴改変、無関係な変更の巻き込みが必要になる。
- 既存ブランチ、worktree、未コミット変更が今回専用か判断できず、安全に分離できない。
- `git fetch origin`、品質確認、`gh` 認証、push、PR 作成が失敗し、自力で解消できない。
- 実装委譲で Herdr 外、CLI 不足、指定 Agent の不存在・非 idle、起動・送信・待機・回収の失敗、部分実装、成果確認の失敗、または `herdr agent wait` 違反が起きる。
- 実装担当が `blocked`、`timeout`、またはユーザー判断事項を返す。
- レビュー工程で Herdr 外、CLI 不足、指定 Agent の不存在・非 idle、起動・送信・待機・投稿・回収・成果確認の失敗、または `herdr agent wait` 違反が起きる。
- FB 対応または再チェックが `question`、`blocked`、`timeout`、上限到達、同一指摘の連続未解消に至る。

実装委譲の停止では作業ツリーと pane を保持する。レビュー工程の停止では作成済み PR と失敗した pane を診断用に保持する。

## ワークフロー

### 1. 要求と作業状態を確認する

- Issue があれば `gh issue view` などで本文、コメント、関連情報を確認する。なければ会話から目的、範囲、完了条件、検証観点を抽出する。
- 設計合意が必要なほど曖昧なら停止する。自動で Issue 化しない。
- `git status --short` で既存変更を確認する。

### 2. 作業領域を用意する

worktree が明示された場合:

- `herdr-worktree-create` を適用し、`herdr worktree create --cwd <repo-root> --path <絶対パス> --branch <ブランチ名> --base <base>` で Herdr 管理の worktree と workspace を作成する。現在の作業ツリーでは `git switch` しない。
- Issue があればブランチ名に `issue-123` を含め、以降は作成した worktree で行う。

それ以外の場合:

- `git-branch-create` を適用し、`git fetch origin` 後に専用ブランチを作る。
- ベースは `origin/HEAD`、取得不能なら `origin/main`、`origin/master`、`origin/develop` の順で選ぶ。
- 保護対象ブランチ上なら `git switch -c <branch> <base>` で最新のリモートベースから分岐する。

### 3. Herdr で実装して検証する

- `cagent-agent-command-resolve`で新規実装担当の実効値を固定し（`agent-kind`・`native-agent-args`・`delegation-metadata`）、`references/implementation-delegation.md`に従って実装と変更に直接関連する検証を同期委譲する。
- `references/implementation-delegation.md`のPR Work Metadata snapshot契約に従い、有効な標準メタ情報を持つ役割だけを保持する。現在の委譲指示に標準suffixがない親自身の行は作らない。
- 実装担当へ `herdr-github-pr-orchestrate` を使わせず、commit、push、PR 作成、別の実装 Agent への再委譲を禁止する。
- 成功結果を保持したまま回収し、`herdr agent wait` の結果、差分、未追跡ファイル、要求充足、検証結果を親が確認する。
- 親が formatter、lint、test、build から変更範囲に必要な最終検証を実行する。成果確認と最終検証の成功後だけ新規起動した pane を閉じて commit へ進む。
- ユーザー判断事項があれば同じ実装担当へ回答を返す。失敗時は自動再試行や親による代替実装を行わず停止する。

### 4. commit する

- `git-changes-commit`を適用し、今回の対象path、除外path、最終検証結果を渡す。通常のIssue実装は原則1 commitとする。
- 返されたcommit hash、対象path、残存変更を確認し、今回の変更だけがcommitされた場合に限り次へ進む。

### 5. push して PR を作成する

- `github-pr-create`を適用し、PR作成後に`gh pr view --json title,body,url`で確認する。メタ情報がある場合は最終セクションと各行が固定済みsnapshotに一致し、ない場合はセクション自体がないことを確認する。
- Issue を閉じるなら `Close #123`、関連付けだけなら `Refs #123` を使う。
- PR本文は次の構造を基本とし、有効な役割行がある場合だけ最後にAI作業メタ情報を追加してファイルから渡す。

```markdown
## Issues

- Close #123

## Why

変更が必要な背景。

## Summary

変更の要約。

## Changes

- 変更点

## Verification

- `command` - passed

## AI Work Metadata

| Role | Agent | Model | Effort |
| --- | --- | --- | --- |
| `<metadata-backed role>` | `<agent>` | `<model>` | `<effort>` |
```

- 固定済みPR Work Metadata snapshotから、3値が揃う役割だけを追加する。部分行、`—`、pane/process info調査、Codex Config fallback、他役割からの補完は禁止する。
- オーケストレーター行は、現在の親タスク自体が有効な標準suffixを受け取っている場合だけ追加する。単体実行やHerdr直接起動のrootには追加しない。
- 実装、レビュー、レビューFBは、それぞれの起動値を固定した委譲snapshotがPR作成前に存在する場合だけ追加する。出自不明の既存paneや未確定の後続役割は推測しない。
- 1行以上ある場合だけ`## AI Work Metadata`をPR本文の最終セクションにする。PR作成後に解決した役割を理由に本文を更新しない。

### 6. Herdr でレビューする

- 新規担当は`cagent-agent-command-resolve`で実効値を固定し（`agent-kind`・`native-agent-args`）、`references/review-loop.md`に従ってレビューAgentへ`github-pr-review`を同期委譲する。
- 結果を回収し、各指摘を `対応可能`、`ユーザー判断が必要`、`対応不能／対象外` に分類する。
- 確認不要で対応可能な指摘を 1 体の専用 FB 対応 Agent へまとめて委譲する。同一ブランチへ並列変更させない。
- 差分、検証、commit、push、返信を親が確認してから、同じレビュー Agent へ元指摘だけの再チェックを依頼する。
- 再チェックで確認不要な`partial` / `unresolved`が返った次FBラウンドは前回FB Agentを再利用せず、別paneの新規セッションへ委譲する。ユーザー指定がなければ`codex`・task level `high`をcagentへ明示して解決する。
- 解消まで反復する。FB 対応は最大 3 回、同一指摘が 2 回連続で解消しなければ停止する。
- 成功時だけ、親が新規起動した pane を規定の時点で閉じる。再利用 pane と失敗・待機中の pane は閉じない。

## 最終報告

- 変更概要、検証結果、PR URL を報告する。
- `実装委譲`、`親の成果確認・最終検証`、`PR 作成`、`レビュー`、`FB 対応`、`再チェック` を別々の状態として示す。
- 未解決指摘、分類、試行回数、失敗理由、保持した pane、必要な判断があれば明記する。

## 品質チェック

- [ ] 実装担当と親の責務、成果確認、最終検証、共通Skillによるcommit、PR 作成の順序が明確である
- [ ] 実装とレビューを独立して Agent 解決でき、種別、既存 Agent、未指定時は現在のエージェント種別を使う分岐と作業ディレクトリが明確である
- [ ] 同じ作業ディレクトリへ複数の実装担当が書き込まず、失敗時の変更と診断情報が保持される
- [ ] レビュー結果の分類、直列 FB 対応、再指摘時の別FB Agent、親の成果確認、同じレビュー Agent の再チェックが明確である
- [ ] 最大 3 回、連続 2 回未解消、ユーザー判断待ち、工程失敗の停止条件がある
- [ ] 新規・再利用、成功・失敗で pane cleanup が区別される
- [ ] PR 成功とレビュー工程の失敗が区別され、診断情報が保持される
- [ ] PR本文のAI Work Metadataは有効な委譲snapshotのある役割だけを含み、メタ情報のないroot行、部分値、`—`を含まない
- [ ] skill validation、`bash .scripts/validate-skills.sh`、`git diff --check` が成功する
