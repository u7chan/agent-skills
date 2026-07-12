---
name: herdr-worktree-create
description: >
  コーディングエージェント用の独立した worktree を Herdr 公式コマンドで作成するときに使う。
  ブランチ命名、衝突確認、Herdr workspace の作成、実装先の引き継ぎまで扱う。
---

# 概要

コーディングエージェントが並列で安全に作業できるように、現在の作業ツリーを切り替えず、Herdr 管理の独立した worktree と作業ブランチを作成するスキル。ブランチ名は `../git-branch-create/SKILL.md` の命名ルールを使い、作成には Herdr 公式の `herdr worktree create` を使う。

# 使用タイミング

- 実装、検証、コミット、PR 作成までを独立した作業領域で進めたい時
- 現在の作業ツリーに未コミット変更があり、別タスクを安全に開始したい時
- 複数のコーディングエージェントが同じリポジトリで並列作業する時
- `herdr-github-implement-pr` などの Herdr 上位スキルが、PR 実装用の作業領域を用意する時

# 基本方針

- 現在の作業ツリーでは `git switch` しない。新しい worktree の中で実装する。
- worktree はリポジトリの兄弟ディレクトリ配下へ作る。
- 既存の未コミット変更は worktree に持ち込まない。
- 既存ブランチや既存 worktree は自動再利用せず、衝突時は別名を生成するか停止する。
- worktree の作成に `git worktree add` を使わない。必ず `herdr worktree create --cwd <repo-root> --path <絶対パス> --branch <ブランチ名> --base <base>` を使う。
- `herdr worktree create` は worktree checkout と Herdr workspace をまとめて作成するため、作成後は返却された workspace 情報も確認する。

# 停止条件

次の場合は停止し、状況と必要な判断を短くユーザーへ返す。

- 対象リポジトリ、作業内容、ベースブランチが特定できない。
- `git fetch origin` が認証やネットワーク、権限の問題で失敗する。
- `herdr` が利用できない、または `herdr worktree create` が失敗する。
- 既存ブランチや既存 worktree があり、今回の作業専用か判断できない。
- worktree 作成先に無関係なファイルや既存ディレクトリがあり、安全に使えない。
- worktree 作成に破壊的操作や履歴改変が必要になる。

# ワークフロー

## 1. 現在の状態を確認する

- 現在の作業ツリーで `git status --short` を実行し、未コミット変更の有無を把握する。
- 未コミット変更があっても、それを新しい worktree に取り込まない。
- `<repo-root>` は Herdr の repo parent workspace に対応する checkout root とする。現在地が linked worktree の場合も、その linked worktree 自体を作成元にしない。
- `herdr worktree list --cwd <repo-root> --json` で Herdr が認識している既存 worktree を確認する。

## 2. ベースブランチを解決する

- ベースブランチを決める前に `git fetch origin` を実行する。
- ベースブランチは `origin/HEAD` を優先する。
- `origin/HEAD` が取れない場合は、`origin/main`、`origin/master`、`origin/develop` の順で存在するものを使う。
- リモート追跡ブランチが使えない場合は、対応するローカルの `main`、`master`、`develop` の順で存在するものを使う。
- 解決したベースは `herdr worktree create` の `--base` に明示する。

## 3. ブランチ名と worktree パスを決める

- `../git-branch-create/SKILL.md` を読み、ブランチ名の生成ルールを適用する。
- Issue がある場合は、ブランチ名に `issue-123` を含める。
- 標準のブランチ名は `<type>/<description>` とする。
- worktree パス用の `branch-slug` は、ブランチ名の `/` を `-` に置換して作る。
- worktree の既定パスは `<repo-parent>/<repo-name>-worktrees/<branch-slug>` の絶対パスとする。
- worktree の親ディレクトリは `<repo-parent>/<repo-name>-worktrees` の絶対パスとし、存在しない場合は作成する。

例:

```text
repo: agent-skills
branch: feature/issue-91-herdr-worktree-create-skill
branch-slug: feature-issue-91-herdr-worktree-create-skill
worktree-path: /home/user/work/agent-skills-worktrees/feature-issue-91-herdr-worktree-create-skill
```

## 4. 衝突を確認する

- `git branch --list <branch>` で同名ブランチの有無を確認する。
- `herdr worktree list --cwd <repo-root> --json` で同じブランチや同じパスを使う worktree がないか確認する。
- 同名ブランチまたは同じパスの worktree が存在する場合は自動再利用せず、別名を生成するか停止する。
- 作成先ディレクトリが存在し、空でない場合は使わない。
- worktree の親ディレクトリが存在しない場合は作成する。作成に失敗した場合は停止する。

## 5. worktree を作成する

標準コマンド:

```bash
mkdir -p <worktree-parentの絶対パス>
herdr worktree create --cwd <repo-root> --path <worktree-pathの絶対パス> --branch <branch> --base <base>
```

`--cwd` には repo parent workspace の checkout root、`--path` には必ず絶対パス、`--base` には解決済みのベースブランチを渡す。作成済みブランチや worktree を開くだけの場合も、作成処理へ混ぜず停止して再利用可否を確認する。

作成後に、以降の作業場所を明示する。

```text
Worktree: <worktree-path>
Branch: <branch>
Base: <base>
Workspace: <workspace-id>
```

`herdr worktree create` の結果から workspace ID、worktree パス、ブランチを確認し、以降の Herdr Agent の作業ディレクトリには作成した絶対パスを渡す。

## 6. 上位スキルへ引き渡す

- 実装、検証、コミット、push、PR 作成は、作成した worktree 内で実行する。
- 最終報告や PR 本文には、必要に応じて作業ブランチと実行した検証を含める。
- 元の作業ツリーの未コミット変更は stage/commit しない。

# 品質チェック

- [ ] 現在の作業ツリーで `git switch` していない
- [ ] `--cwd` に linked worktree ではなく repo parent workspace の checkout root を使っている
- [ ] `git fetch origin` 後にベースブランチを解決している
- [ ] ブランチ名は `git-branch-create` の命名ルールに従っている
- [ ] worktree パスは `<repo-parent>/<repo-name>-worktrees/<branch-slug>` の絶対パスになっている
- [ ] worktree の親ディレクトリが存在しない場合は作成している
- [ ] 既存ブランチや既存 worktree の衝突確認をしている
- [ ] `git worktree add` ではなく `herdr worktree create` を使っている
- [ ] `--cwd <repo-root>`、`--path <絶対パス>`、`--branch <ブランチ名>`、`--base <base>` を明示している
- [ ] 作成された Herdr workspace の情報を確認している
- [ ] 以降の作業場所として worktree パスを明示している
