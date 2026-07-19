# agent skills

[![Skills](https://img.shields.io/badge/skills-32-2ea44f?style=flat-square)](#available-skills)
[![Validation](https://img.shields.io/github/actions/workflow/status/u7chan/agent-skills/validate-skills.yml?branch=main&style=flat-square&label=validation)](https://github.com/u7chan/agent-skills/actions/workflows/validate-skills.yml)

コーディングエージェント用のカスタムスキル集です。

スキルの命名・メンテナンス規約は [AGENTS.md](AGENTS.md) を参照してください。

## Available Skills

スキルは利用目的ごとにグルーピングしてあります。グループ内の並びは関連の強さや作業フローの順です。
`External Dependencies` は実行に必要な CLI、ランタイム、外部サービスを示します。`—` は必須の外部依存がないこと、`conditional` は特定フローでのみ必要なこと、`optional` は代替手段、`fallback` は最終的な代替取得元であることを表します。

### Git ローカル操作

| Skill | Description | External Dependencies |
|-------|-------------|-----------------------|
| [git-branch-create](git-branch-create/SKILL.md) | ブランチ名を提案し、ブランチを作成する | Git, POSIX shell |
| [git-worktree-create](git-worktree-create/SKILL.md) | 独立した git worktree を作成し、並列作業用の作業領域を用意する | Git, POSIX shell |
| [git-commit-message-suggest](git-commit-message-suggest/SKILL.md) | 変更内容に合うコミットメッセージだけを提案し、stageやcommitは行わない | Git, POSIX shell |
| [git-changes-commit](git-changes-commit/SKILL.md) | 今回の変更だけを限定stageし、安全にcommitして結果を確認する | Git, POSIX shell |

### GitHub Issue / PR

| Skill | Description | External Dependencies |
|-------|-------------|-----------------------|
| [github-issue-create-from-plan](github-issue-create-from-plan/SKILL.md) | 確定済みプランからテンプレートを選び、GitHub Issueを作成・確認する | `gh`, GitHub, POSIX shell |
| [github-pr-orchestrate](github-pr-orchestrate/SKILL.md) | 未コミット変更の確認から限定commit、PR作成、指定レビュー工程まで統括する | `gh`, `jq` (conditional), Git, GitHub, POSIX shell |
| [github-pr-create](github-pr-create/SKILL.md) | 非修正型の品質チェック後、commit済み変更をpushしてPRを作成・確認する | `gh`, Git, GitHub, POSIX shell |
| [github-pr-feedback-address](github-pr-feedback-address/SKILL.md) | GitHub PR のレビュー指摘を確認し、実装対応から返信まで行う | `gh`, Git, GitHub API, POSIX shell |
| [github-pr-review](github-pr-review/SKILL.md) | 指定した GitHub PR をレビューし、FB 対応後の再チェックまで行う | `gh`, `jq`, GitHub API, POSIX shell |
| [github-pr-comment-reply](github-pr-comment-reply/SKILL.md) | GitHub PR の review comment や conversation comment に返信する | `gh`, GitHub API, POSIX shell |
| [github-pr-post-merge-cleanup](github-pr-post-merge-cleanup/SKILL.md) | マージ済み PR の基準ブランチへ戻り、ローカル作業ブランチを安全に整理する | `gh`, Git, POSIX shell |

### Agent委譲 / オーケストレーション

| Skill | Description | External Dependencies |
|-------|-------------|-----------------------|
| [herdr-worktree-create](herdr-worktree-create/SKILL.md) | Herdr 公式コマンドで独立した worktree と workspace を作成する | Herdr, Git, POSIX shell |
| [cagent-agent-command-resolve](cagent-agent-command-resolve/SKILL.md) | cagentの実効Agent・Model・Effortを起動コマンドへ固定し、任意の委譲メタ情報を返す | Herdr, `cagent`, Python 3, selected Agent CLI, POSIX shell |
| [herdr-agent-delegate](herdr-agent-delegate/SKILL.md) | Herdr公式プリミティブでCLI Agentを配置し、任意の起動時メタ情報付きで送信・待機・出力回収を行う | Herdr, `jq`, Python 3, POSIX shell, Agent CLI |
| [herdr-github-create-issue](herdr-github-create-issue/SKILL.md) | 確定済みプランのIssue作成をHerdrの新規Agentへ委譲する | Herdr, `cagent`, `gh`, `jq`, Git, Python 3, POSIX shell |
| [herdr-github-pr-orchestrate](herdr-github-pr-orchestrate/SKILL.md) | Issue確認から実装委譲、commit、push、PR作成、レビュー・FB対応・再チェックまで統括する | Herdr, `gh`, `jq`, Git, Python 3, POSIX shell, Agent CLI |
| [herdr-prompt-evaluate](herdr-prompt-evaluate/SKILL.md) | Herdrの独立Agentでプロンプトを実証評価し、観測した1テーマを最小改善する | Herdr, `jq`, Git, Python 3, POSIX shell, Agent CLI |

### 実装 / 成果物生成

| Skill | Description | External Dependencies |
|-------|-------------|-----------------------|
| [html-artifact-format](html-artifact-format/SKILL.md) | AI向けMarkdownと人間向けHTMLを判断し、視覚化要素入りの単一HTMLを生成する | POSIX shell |

### 要件定義 / 設計対話

| Skill | Description | External Dependencies |
|-------|-------------|-----------------------|
| [grilling](grilling/SKILL.md) | 計画・意思決定・アイデアを領域を問わず一問ずつ徹底的に掘り下げる | — |
| [design-plan-grill](design-plan-grill/SKILL.md) | 通常・docs-backedの両モードで設計を一問ずつ壁打ちし、実装前に合意を固める | — |

### 文章チェック / 校正

| Skill | Description | External Dependencies |
|-------|-------------|-----------------------|
| [japanese-text-refine](japanese-text-refine/SKILL.md) | 日本語文書の校正・自然化・執筆・推敲を目的に応じて扱う | — |

### 品質 / テスト設計

| Skill | Description | External Dependencies |
|-------|-------------|-----------------------|
| [qa-test-design](qa-test-design/SKILL.md) | QA観点とテストケースを体系的に洗い出し、テスト実装前の設計を整える | — |

### 依存パッケージ更新

| Skill | Description | External Dependencies |
|-------|-------------|-----------------------|
| [bun-dependency-update](bun-dependency-update/SKILL.md) | Bun アプリの依存更新を非メジャー/major の分岐付きで安全に進める | Bun, `rg`, POSIX shell, web access (conditional) |
| [npm-dependency-update](npm-dependency-update/SKILL.md) | npm アプリの依存更新を非メジャー/major の分岐付きで安全に進める | Node.js / npm, `rg`, POSIX shell, web access (conditional) |
| [uv-dependency-update](uv-dependency-update/SKILL.md) | uv 管理の Python 依存更新を非メジャー/major の分岐付きで安全に進める | `uv`, Python, `rg`, POSIX shell, web access (conditional) |

### UI / フロントエンド

| Skill | Description | External Dependencies |
|-------|-------------|-----------------------|
| [apple-interface-design](apple-interface-design/SKILL.md) | Appleの設計思想をWebへ翻案し、流体モーションとアクセシブルなUIを設計・レビューする | — |
| [tailwind-ui-compose](tailwind-ui-compose/SKILL.md) | 画面構成から始めて Tailwind UI の設計と実装方針を整える | Tailwind CSS project |

### ブラウザ操作 / 検証

| Skill | Description | External Dependencies |
|-------|-------------|-----------------------|
| [playwright-cli](playwright-cli/SKILL.md) | Playwright CLI の独立ブラウザで localhost などの画面検証を進める | Playwright CLI, browser, POSIX shell, Node.js / `npx` (fallback) |

### Experimental

| Skill | Description | External Dependencies |
|-------|-------------|-----------------------|
| [image-to-svg](image-to-svg/SKILL.md) | 画像（PNG/JPEG）を編集可能な SVG に変換する | librsvg / Inkscape / browser (one required) |

### スキル作成 / メンテナンス

| Skill | Description | External Dependencies |
|-------|-------------|-----------------------|
| [agent-skill-design](agent-skill-design/SKILL.md) | Agent Skillの新規作成、仕様変更、全面再設計、設計レビューを行う | — |
| [agent-skill-refine](agent-skill-refine/SKILL.md) | 既存Agent Skillを挙動を変えず短く高密度に改善する | — |
| [codex-skills-link](codex-skills-link/SKILL.md) | `.codex/skills`だけを操作し、`.claude/skills`をCodexから再利用できるようにリンクする | POSIX shell, coreutils |

## Setup

セットアップ手順は [SETUP.md](SETUP.md) を参照してください。

## Usage

エージェントにスキルが認識されると、`/skill-name` または `$skill-name` と入力して呼び出せます。
