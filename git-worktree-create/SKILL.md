---
name: git-worktree-create
description: >
  Create an isolated git worktree for coding-agent work, including base branch
  resolution, branch naming, collision checks, and the handoff path for
  implementation.
---

# 概要

コーディングエージェントが並列で安全に作業できるように、現在の作業ツリーを切り替えず、独立した `git worktree` と作業ブランチを作成するスキル。ブランチ名は `../git-branch-create/SKILL.md` の命名ルールを使い、実際の作業領域作成はこのスキルで行う。

# 使用タイミング

- 実装、検証、コミット、PR 作成までを独立した作業領域で進めたい時
- 現在の作業ツリーに未コミット変更があり、別タスクを安全に開始したい時
- 複数のコーディングエージェントが同じリポジトリで並列作業する時
- `github-implement-pr` などの上位スキルが、PR 実装用の作業領域を用意する時

# 基本方針

- 現在の作業ツリーでは `git switch` しない。新しい worktree の中で実装する。
- worktree はリポジトリの兄弟ディレクトリ配下へ作る。
- 既存の未コミット変更は worktree に持ち込まない。
- 既存ブランチや既存 worktree は、今回の作業専用だと判断できる場合だけ再利用する。
- 既存スキルのブランチ名ルールは参照するが、作業ブランチ作成手順は `git worktree add` を優先する。

# 停止条件

次の場合は停止し、状況と必要な判断を短くユーザーへ返す。

- 対象リポジトリ、作業内容、ベースブランチが特定できない。
- `git fetch origin` が認証やネットワーク、権限の問題で失敗する。
- 既存ブランチや既存 worktree があり、今回の作業専用か判断できない。
- worktree 作成先に無関係なファイルや既存ディレクトリがあり、安全に使えない。
- worktree 作成に破壊的操作や履歴改変が必要になる。

# ワークフロー

## 1. 現在の状態を確認する

- 現在の作業ツリーで `git status --short` を実行し、未コミット変更の有無を把握する。
- 未コミット変更があっても、それを新しい worktree に取り込まない。
- `git worktree list` で既存 worktree を確認する。

## 2. ベースブランチを解決する

- ベースブランチを決める前に `git fetch origin` を実行する。
- ベースブランチは `origin/HEAD` を優先する。
- `origin/HEAD` が取れない場合は、`origin/main`、`origin/master`、`origin/develop` の順で存在するものを使う。
- リモート追跡ブランチが使えない場合は、対応するローカルの `main`、`master`、`develop` の順で存在するものを使う。

## 3. ブランチ名と worktree パスを決める

- `../git-branch-create/SKILL.md` を読み、ブランチ名の生成ルールを適用する。
- Issue がある場合は、ブランチ名に `issue-123` を含める。
- 標準のブランチ名は `<type>/<description>` とする。
- worktree パス用の `branch-slug` は、ブランチ名の `/` を `-` に置換して作る。
- worktree の既定パスは `../<repo-name>-worktrees/<branch-slug>` とする。
- worktree の親ディレクトリは `../<repo-name>-worktrees` とし、存在しない場合は `mkdir -p ../<repo-name>-worktrees` で作成する。

例:

```text
repo: agent-skills
branch: feature/issue-91-git-worktree-create-skill
branch-slug: feature-issue-91-git-worktree-create-skill
worktree-path: ../agent-skills-worktrees/feature-issue-91-git-worktree-create-skill
```

## 4. 衝突を確認する

- `git branch --list <branch>` で同名ブランチの有無を確認する。
- `git worktree list` で同じブランチや同じパスを使う worktree がないか確認する。
- 既存ブランチや既存 worktree が今回の作業専用で、ベースからの差分も今回の作業だけだと判断できる場合は再利用してよい。
- 別タスクの変更や別 PR のコミットが含まれる可能性がある場合は、別名を生成するか停止する。
- 作成先ディレクトリが存在し、空でない場合は使わない。
- worktree の親ディレクトリが存在しない場合は作成する。作成に失敗した場合は停止する。

## 5. worktree を作成する

標準コマンド:

```bash
mkdir -p ../<repo-name>-worktrees
git worktree add -b <branch> <worktree-path> <base>
```

既存ブランチを今回の作業専用として再利用できる場合だけ、次の形を使う。

```bash
mkdir -p ../<repo-name>-worktrees
git worktree add <worktree-path> <branch>
```

作成後に、以降の作業場所を明示する。

```text
Worktree: <worktree-path>
Branch: <branch>
Base: <base>
```

## 6. 上位スキルへ引き渡す

- 実装、検証、コミット、push、PR 作成は、作成した worktree 内で実行する。
- 最終報告や PR 本文には、必要に応じて作業ブランチと実行した検証を含める。
- 元の作業ツリーの未コミット変更は stage/commit しない。

# 品質チェック

- [ ] 現在の作業ツリーで `git switch` していない
- [ ] `git fetch origin` 後にベースブランチを解決している
- [ ] ブランチ名は `git-branch-create` の命名ルールに従っている
- [ ] worktree パスは `../<repo-name>-worktrees/<branch-slug>` 形式になっている
- [ ] worktree の親ディレクトリが存在しない場合は作成している
- [ ] 既存ブランチや既存 worktree の衝突確認をしている
- [ ] 以降の作業場所として worktree パスを明示している
