# agent skills

コーディングエージェント用のカスタムスキル集です。

## Available Skills

スキルは利用目的ごとにグルーピングしてあります。グループ内の並びは関連の強さや作業フローの順です。

### Git ローカル操作

| Skill | Description |
|-------|-------------|
| [git-branch-create](git-branch-create/SKILL.md) | ブランチ名を提案し、ブランチを作成する |
| [git-worktree-create](git-worktree-create/SKILL.md) | 独立した git worktree を作成し、並列作業用の作業領域を用意する |
| [git-commit-message](git-commit-message/SKILL.md) | コミットメッセージを提案する |

### GitHub Issue / PR

| Skill | Description |
|-------|-------------|
| [github-issue-create-from-plan](github-issue-create-from-plan/SKILL.md) | 設計プラン合意後に GitHub Issue を作成する |
| [github-pr-create](github-pr-create/SKILL.md) | PR 本文生成を含めて GitHub に PR を作成する |
| [github-pr-feedback-address](github-pr-feedback-address/SKILL.md) | GitHub PR のレビュー指摘を確認し、実装対応から返信まで行う |
| [github-pr-review](github-pr-review/SKILL.md) | 指定した GitHub PR をレビューし、FB 対応後の再チェックまで行う |
| [github-pr-comment-reply](github-pr-comment-reply/SKILL.md) | GitHub PR の review comment や conversation comment に返信する |
| [ai-identity-resolve](ai-identity-resolve/SKILL.md) | AIレビュー補助コメント用のエージェント名・モデル名を推測せず取得する |

### 実装 / 成果物生成

| Skill | Description |
|-------|-------------|
| [github-implement-pr](github-implement-pr/SKILL.md) | 既存スキルを参照しつつ Issue 確認から PR 作成まで進める |
| [html-artifact-format](html-artifact-format/SKILL.md) | AI向けMarkdownと人間向けHTMLを判断し、視覚化要素入りの単一HTMLを生成する |

### 要件定義 / 設計対話

| Skill | Description |
|-------|-------------|
| [grilling](grilling/SKILL.md) | 計画や設計を実装前に徹底的に壁打ちし、意思決定と前提を明確にする |
| [grill-with-docs](grill-with-docs/SKILL.md) | 既存ドキュメントと照合しながら設計を厳しく壁打ちする |

### 文章チェック / 校正

| Skill | Description |
|-------|-------------|
| [japanese-text-proofread](japanese-text-proofread/SKILL.md) | 日本語の文章や Markdown 原稿の誤字脱字・表記ゆれを点検する |
| [japanese-ai-text-naturalize](japanese-ai-text-naturalize/SKILL.md) | AI生成っぽい技術・業務文を自然で実用的な日本語へ整える |

### 品質 / テスト設計

| Skill | Description |
|-------|-------------|
| [qa-test-design](qa-test-design/SKILL.md) | QA観点とテストケースを体系的に洗い出し、テスト実装前の設計を整える |

### 依存パッケージ更新

| Skill | Description |
|-------|-------------|
| [bun-dependency-update](bun-dependency-update/SKILL.md) | Bun アプリの依存更新を非メジャー/major の分岐付きで安全に進める |
| [npm-dependency-update](npm-dependency-update/SKILL.md) | npm アプリの依存更新を非メジャー/major の分岐付きで安全に進める |
| [uv-dependency-update](uv-dependency-update/SKILL.md) | uv 管理の Python 依存更新を非メジャー/major の分岐付きで安全に進める |

### UI / フロントエンド

| Skill | Description |
|-------|-------------|
| [tailwind-ui-compose](tailwind-ui-compose/SKILL.md) | 画面構成から始めて Tailwind UI の設計と実装方針を整える |

### ターミナル操作

| Skill | Description |
|-------|-------------|
| [tmux-codex-split](tmux-codex-split/SKILL.md) | 現在の tmux ウィンドウを左右分割し、新しいペインで Codex CLI を起動する |

### ブラウザ操作 / 検証

| Skill | Description |
|-------|-------------|
| [browser-use](browser-use/SKILL.md) | browser-use CLI の独自ブラウザで localhost などの画面確認を進める |
| [wsl-chrome-attach](wsl-chrome-attach/SKILL.md) | WSL2 上のエージェントから Windows Chrome の remote debugging へ接続診断する |
| [wsl-chrome-attach-use](wsl-chrome-attach-use/SKILL.md) | attach 済み Windows Chrome を chrome-devtools-mcp 経由で操作する |

### Experimental

| Skill | Description |
|-------|-------------|
| [image-to-svg](image-to-svg/SKILL.md) | 画像（PNG/JPEG）を編集可能な SVG に変換する |

### スキル作成 / メンテナンス

| Skill | Description |
|-------|-------------|
| [skill-author](skill-author/SKILL.md) | SKILL.md ファイルの作成と改善を行う |
| [skills-readme-sync](.claude/skills/skills-readme-sync/SKILL.md) | **本リポジトリ専用** — README のスキル一覧を現在のスキル構成へ同期する |
| [codex-skills-link-from-claude](codex-skills-link-from-claude/SKILL.md) | `.claude/skills` を `.codex/skills` から再利用できるようにリンクする |

## Naming Convention

スキル名は原則として `service-target-action` の順で付けます。

- `service`: `git` `github` `bun` `codex` `skill` のような対象領域
- `target`: `branch` `pr` `issue` `dependency` `skills` のような主対象
- `action`: `create` `review` `update` `description` のような操作内容

これにより、一覧を見た時に「どこで」「何に対して」「何をする」スキルかを判断しやすくします。

README のグルーピングはスキル名の prefix ではなく、利用目的を優先して決めます。

## Skill Maintenance

`SKILL.md` は原則として180行以内に収め、必須ルール・禁止事項・主要ワークフローは先頭150行以内に置きます。
長い例、詳細手順、CLI/APIサンプル、トラブルシュートは `references/` に用途別で分割します。

ローカル検証は次のコマンドで実行できます。

```sh
bash scripts/validate-skills.sh
```

この検証では、`SKILL.md` の行数、`references/` の参照切れ、README の `Available Skills` と実スキル一覧の一致を確認します。

## Setup

セットアップ手順は [SETUP.md](SETUP.md) を参照してください。

## Usage

エージェントにスキルが認識されると、`/skill-name` または `$skill-name` と入力して呼び出せます。
