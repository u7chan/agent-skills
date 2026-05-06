# agent skills

AI エージェント用のカスタムスキル集です。

## Available Skills

スキルは役割ごとにグルーピングしてあります。グループ内の並びは関連の強さや作業フローの順です。

### Git / GitHub 操作

| Skill | Description |
|-------|-------------|
| [git-branch-create](git-branch-create/) | ブランチ名を提案し、ブランチを作成する |
| [git-commit-message](git-commit-message/) | コミットメッセージを提案する |
| [github-issue-create-from-plan](github-issue-create-from-plan/) | 設計プラン合意後に GitHub Issue を作成する |
| [github-pr-create](github-pr-create/) | PR 本文生成を含めて GitHub に PR を作成する |
| [github-pr-feedback-address](github-pr-feedback-address/) | GitHub PR のレビュー指摘を確認し、実装対応から push まで行う |
| [github-pr-review](github-pr-review/) | 指定した GitHub PR をレビューし、FB 対応後の再チェックまで行う |
| [github-pr-comment-reply](github-pr-comment-reply/) | GitHub PR の review comment や conversation comment に返信する |

### 実装フロー

| Skill | Description |
|-------|-------------|
| [github-implement-pr](github-implement-pr/) | Issue 確認から実装、検証、コミット、push、PR 作成まで自動で進める |

### 依存パッケージ更新

| Skill | Description |
|-------|-------------|
| [bun-dependency-update](bun-dependency-update/) | Bun アプリの依存更新を非メジャー/major の分岐付きで安全に進める |
| [npm-dependency-update](npm-dependency-update/) | npm アプリの依存更新を非メジャー/major の分岐付きで安全に進める |
| [uv-dependency-update](uv-dependency-update/) | uv 管理の Python 依存更新を非メジャー/major の分岐付きで安全に進める |

### UI / フロントエンド

| Skill | Description |
|-------|-------------|
| [tailwind-ui-compose](tailwind-ui-compose/) | 画面構成から始めて Tailwind UI の設計と実装方針を整える |
| [browser-check](browser-check/) | `browser-use` で localhost の画面確認を最小構成で進める |

### アセット変換

| Skill | Description |
|-------|-------------|
| [image-to-svg](image-to-svg/) | **experimental** — 画像（PNG/JPEG）を編集可能な SVG に変換する |

### スキル管理 / セットアップ

| Skill | Description |
|-------|-------------|
| [skill-author](skill-author/) | SKILL.md ファイルの作成と改善を行う |
| [skills-readme-sync](.claude/skills/skills-readme-sync/) | **本リポジトリ専用** — README のスキル一覧を現在のスキル構成へ同期する |
| [codex-skills-link-from-claude](codex-skills-link-from-claude/) | `.claude/skills` を `.codex/skills` から再利用できるようにリンクする |

## Naming Convention

スキル名は原則として `service-target-action` の順で付けます。

- `service`: `git` `github` `bun` `codex` `skill` のような対象領域
- `target`: `branch` `pr` `issue` `dependency` `skills` のような主対象
- `action`: `create` `review` `update` `description` のような操作内容

これにより、一覧を見た時に「どこで」「何に対して」「何をする」スキルかを判断しやすくします。

## Setup

### Claude Code を使用する場合

```sh
git clone git@github.com:u7chan/agent-skills.git
cd agent-skills
mkdir -p "$HOME/.claude/skills"
ln -sf "$(pwd)" "$HOME/.claude/skills"
```

> [!NOTE]
> `$HOME/.claude/skills` ディレクトリが既に存在する場合は、上記コマンドをそのまま実行してください。

### Codex を使用する場合

```sh
git clone git@github.com:u7chan/agent-skills.git
cd agent-skills
mkdir -p "$HOME/.codex"
ln -sfn "$(pwd)" "$HOME/.codex/skills"
```

> [!NOTE]
> `"$HOME/.codex/skills"` が既に存在する場合は、上記コマンドをそのまま実行してください。

### シンボリックリンクを解除する場合

```sh
rm "$HOME/.claude/skills"
rm "$HOME/.codex/skills"
```

> [!NOTE]
> Claude Code 以外のエージェントでは、設定ディレクトリのパスが異なる場合があります。

## Usage

エージェントにスキルが認識されると、`/skill-name` または `$skill-name` と入力して呼び出せます。
