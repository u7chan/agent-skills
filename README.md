# agent skills

AI エージェント用のカスタムスキル集です。

## Available Skills

| Skill | Description |
|-------|-------------|
| [bun-dependency-major-upgrade](bun-dependency-major-upgrade/) | Bun アプリの依存関係をメジャーバージョン更新する際の調査・確認・適用手順 |
| [bun-dependency-update](bun-dependency-update/) | Bun アプリの依存関係を非メジャーで広めにまとめて更新する際の手順 |
| [codex-skills-link-from-claude](codex-skills-link-from-claude/) | `.claude/skills` を `.codex/skills` から再利用できるようにリンクする |
| [git-branch-create](git-branch-create/) | ブランチ名を提案し、ブランチを作成する |
| [git-commit-message](git-commit-message/) | コミットメッセージを提案する |
| [git-pr-description](git-pr-description/) | コンテキストから PR 本文をマークダウン形式で提案する |
| [github-issue-create-from-plan](github-issue-create-from-plan/) | 設計プラン合意後に GitHub Issue を作成する |
| [github-pr-create](github-pr-create/) | PR 本文作成後に GitHub に PR を作成する |
| [github-pr-review](github-pr-review/) | 指定した GitHub PR をレビューし、PR 上にコメントを投稿する |
| [npm-dependency-major-upgrade](npm-dependency-major-upgrade/) | npm アプリの依存関係をメジャーバージョン更新する際の調査・確認・適用手順 |
| [npm-dependency-update](npm-dependency-update/) | npm アプリの依存関係を非メジャーで安全に更新する際の手順 |
| [skill-author](skill-author/) | SKILL.md ファイルの作成と改善を行う |
| [start-implementation](start-implementation/) | Issue 確認から実装、検証、コミット、PR 準備までを進行管理する |
| [skills-readme-sync](.claude/skills/skills-readme-sync/) | README のスキル一覧を現在のスキル構成へ同期する |
| [uv-dependency-major-upgrade](uv-dependency-major-upgrade/) | uv 管理の Python 依存関係をメジャーバージョン更新する際の調査・確認・適用手順 |
| [uv-dependency-update](uv-dependency-update/) | uv 管理の Python 依存関係を非メジャーで広めにまとめて更新する際の手順 |

## Naming Convention

スキル名は原則として `service-target-action` の順で付けます。

- `service`: `git` `github` `bun` `codex` `skill` のような対象領域
- `target`: `branch` `pr` `issue` `dependency` `skills` のような主対象
- `action`: `create` `review` `update` `description` のような操作内容

これにより、一覧を見た時に「どこで」「何に対して」「何をする」スキルかを判断しやすくします。

## Setup

Claude Code を使用する場合:

```sh
git clone git@github.com:u7chan/agent-skills.git
cd agent-skills
mkdir -p "$HOME/.claude/skills"
ln -sf "$(pwd)" "$HOME/.claude/skills"
```

> [!NOTE]
> `$HOME/.claude/skills` ディレクトリが既に存在する場合は、上記コマンドをそのまま実行してください。

Codex を使用する場合:

```sh
git clone git@github.com:u7chan/agent-skills.git
cd agent-skills
mkdir -p "$HOME/.codex"
ln -sfn "$(pwd)" "$HOME/.codex/skills"
```

> [!NOTE]
> `"$HOME/.codex/skills"` が既に存在する場合は、上記コマンドをそのまま実行してください。

シンボリックリンクを解除する場合:

```sh
rm "$HOME/.claude/skills"
rm "$HOME/.codex/skills"
```

> [!NOTE]
> Claude Code 以外のエージェントでは、設定ディレクトリのパスが異なる場合があります。

## Usage

エージェントにスキルが認識されると、`/skill-name` または `@skill-name` と入力して呼び出せます。
