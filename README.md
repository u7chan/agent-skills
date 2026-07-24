# agent skills

[![Skills](https://badgen.net/static/skills/33/2ea44f)](#available-skills)
[![Validation](https://github.com/u7chan/agent-skills/actions/workflows/validate-skills.yml/badge.svg?branch=main)](https://github.com/u7chan/agent-skills/actions/workflows/validate-skills.yml)

コーディングエージェント用のカスタムスキル集です。

スキルの命名・メンテナンス規約は [AGENTS.md](AGENTS.md) を参照してください。

## Available Skills

スキルは利用目的ごとにグルーピングしてあります。グループ内の並びは関連の強さや作業フローの順です。
 `External Dependencies` は実行に必要な CLI、ランタイム、外部サービスを示します。`—` は外部依存が1件もない場合だけ使います。依存の種別定義は `.rules/skill-categories.yaml` を正本とします。

### Git ローカル操作

| Skill | Description | External Dependencies |
|-------|-------------|-----------------------|
| [git-branch-create](skills/git/git-branch-create/SKILL.md) | ブランチ名を提案し、ブランチを作成する | Git, POSIX shell |
| [git-worktree-create](skills/git/git-worktree-create/SKILL.md) | 独立した git worktree を作成し、並列作業用の作業領域を用意する | Git, POSIX shell |
| [git-commit-message-suggest](skills/git/git-commit-message-suggest/SKILL.md) | 変更内容に合うコミットメッセージだけを提案し、stageやcommitは行わない | Git, POSIX shell |
| [git-changes-commit](skills/git/git-changes-commit/SKILL.md) | 今回の変更だけを限定stageし、安全にcommitして結果を確認する | Git, POSIX shell |

### GitHub Issue / PR

| Skill | Description | External Dependencies |
|-------|-------------|-----------------------|
| [github-issue-decompose](skills/github/github-issue-decompose/SKILL.md) | 既存Issueを本文・全コメントを根拠にSub-issueへ分解し、親をEpic化する | `gh`, GitHub, POSIX shell |
| [github-issue-create-from-plan](skills/github/github-issue-create-from-plan/SKILL.md) | 確定済みプランからテンプレートを選び、GitHub Issueを作成・確認する | `gh`, GitHub, POSIX shell |
| [github-pr-orchestrate](skills/orchestration/github-pr-orchestrate/SKILL.md) | 未コミット変更の確認から限定commit、PR作成、指定レビュー工程まで統括する | `gh`, `jq`, Git, GitHub, POSIX shell |
| [github-pr-create](skills/github/github-pr-create/SKILL.md) | 非修正型の品質チェック後、commit済み変更をpushしてPRを作成・確認する | `gh`, Git, GitHub, POSIX shell |
| [github-pr-feedback-address](skills/github/github-pr-feedback-address/SKILL.md) | GitHub PR のレビュー指摘を確認し、実装対応から返信まで行う | `gh`, Git, GitHub API, POSIX shell |
| [github-pr-review](skills/github/github-pr-review/SKILL.md) | 指定した GitHub PR をレビューし、FB 対応後の再チェックまで行う | `gh`, `jq`, GitHub API, POSIX shell |
| [github-pr-comment-reply](skills/github/github-pr-comment-reply/SKILL.md) | GitHub PR の review comment や conversation comment に返信する | `gh`, GitHub API, POSIX shell |
| [github-pr-post-merge-cleanup](skills/github/github-pr-post-merge-cleanup/SKILL.md) | マージ済み PR の基準ブランチへ戻り、ローカル作業ブランチを安全に整理する | `gh`, Git, POSIX shell |

### Agent委譲 / オーケストレーション

| Skill | Description | External Dependencies |
|-------|-------------|-----------------------|
| [herdr-worktree-create](skills/orchestration/herdr-worktree-create/SKILL.md) | Herdr 公式コマンドで独立した worktree と workspace を作成する | Herdr, Git, POSIX shell |
| [cagent-agent-command-resolve](skills/orchestration/cagent-agent-command-resolve/SKILL.md) | cagentの実効Agent・Model・Effortをagent-kind・native-agent-argsへ固定し、任意の委譲メタ情報を返す | Herdr, `cagent`, Python 3, selected Agent CLI, POSIX shell |
| [herdr-agent-delegate](skills/orchestration/herdr-agent-delegate/SKILL.md) | Herdr 0.7.5公式API（agent start/prompt/wait/read/send-keys）でCLI Agentを配置し、任意の起動時メタ情報付きで送信・待機・出力回収を行う | Herdr, `jq`, Python 3, POSIX shell, Agent CLI |
| [herdr-github-create-issue](skills/orchestration/herdr-github-create-issue/SKILL.md) | 確定済みプランのIssue作成をHerdrの新規Agentへ委譲する | Herdr, `cagent`, `gh`, `jq`, Git, Python 3, POSIX shell, selected Agent CLI |
| [herdr-github-pr-orchestrate](skills/orchestration/herdr-github-pr-orchestrate/SKILL.md) | Issue確認から実装委譲、commit、push、PR作成、レビュー・FB対応・再チェックまで統括する | Herdr, `cagent`, `gh`, `jq`, Git, Python 3, POSIX shell, Agent CLI |
| [herdr-prompt-evaluate](skills/orchestration/herdr-prompt-evaluate/SKILL.md) | Herdrの独立Agentでプロンプトを実証評価し、観測した1テーマを最小改善する | Herdr, `jq`, Git, Python 3, POSIX shell, Agent CLI |

### 実装 / 成果物生成

| Skill | Description | External Dependencies |
|-------|-------------|-----------------------|
| [html-artifact-format](skills/tool/html-artifact-format/SKILL.md) | AI向けMarkdownと人間向けHTMLを判断し、視覚化要素入りの単一HTMLを生成する | POSIX shell |

### 要件定義 / 設計対話

| Skill | Description | External Dependencies |
|-------|-------------|-----------------------|
| [grilling](skills/design/grilling/SKILL.md) | 計画・意思決定・アイデアを領域を問わず一問ずつ徹底的に掘り下げる | — |
| [design-plan-grill](skills/design/design-plan-grill/SKILL.md) | 通常・docs-backedの両モードで設計を一問ずつ壁打ちし、実装前に合意を固める | — |

### 文章チェック / 校正

| Skill | Description | External Dependencies |
|-------|-------------|-----------------------|
| [japanese-text-refine](skills/tool/japanese-text-refine/SKILL.md) | 日本語文書の校正・自然化・執筆・推敲を目的に応じて扱う | — |

### 品質 / テスト設計

| Skill | Description | External Dependencies |
|-------|-------------|-----------------------|
| [qa-test-design](skills/tool/qa-test-design/SKILL.md) | QA観点とテストケースを体系的に洗い出し、テスト実装前の設計を整える | — |

### 依存パッケージ更新

| Skill | Description | External Dependencies |
|-------|-------------|-----------------------|
| [bun-dependency-update](skills/dependency/bun-dependency-update/SKILL.md) | Bun アプリの依存更新を非メジャー/major の分岐付きで安全に進める | Bun, `rg`, POSIX shell, web access |
| [npm-dependency-update](skills/dependency/npm-dependency-update/SKILL.md) | npm アプリの依存更新を非メジャー/major の分岐付きで安全に進める | Node.js, npm, `rg`, POSIX shell, web access |
| [uv-dependency-update](skills/dependency/uv-dependency-update/SKILL.md) | uv 管理の Python 依存更新を非メジャー/major の分岐付きで安全に進める | `uv`, Python, `rg`, POSIX shell, web access |

### UI / フロントエンド

| Skill | Description | External Dependencies |
|-------|-------------|-----------------------|
| [apple-interface-design](skills/tool/apple-interface-design/SKILL.md) | Appleの設計思想をWebへ翻案し、流体モーションとアクセシブルなUIを設計・レビューする | — |
| [tailwind-ui-compose](skills/tool/tailwind-ui-compose/SKILL.md) | 画面構成から始めて Tailwind UI の設計と実装方針を整える | Tailwind CSS project |

### ブラウザ操作 / 検証

| Skill | Description | External Dependencies |
|-------|-------------|-----------------------|
| [playwright-cli](skills/tool/playwright-cli/SKILL.md) | Playwright CLI の独立ブラウザで localhost などの画面検証を進める | Playwright CLI, browser, POSIX shell, Node.js, `npx` |

### Experimental

| Skill | Description | External Dependencies |
|-------|-------------|-----------------------|
| [image-to-svg](skills/tool/image-to-svg/SKILL.md) | 画像（PNG/JPEG）を編集可能な SVG に変換する | librsvg, Inkscape, browser |

### スキル作成 / メンテナンス

| Skill | Description | External Dependencies |
|-------|-------------|-----------------------|
| [agent-skill-design](skills/skill/agent-skill-design/SKILL.md) | Agent Skillの新規作成、仕様変更、全面再設計、設計レビューを行う | — |
| [agent-skill-refine](skills/skill/agent-skill-refine/SKILL.md) | 既存Agent Skillを挙動を変えず短く高密度に改善する | — |
| [codex-skills-link](skills/tool/codex-skills-link/SKILL.md) | `.codex/skills`だけを操作し、`.claude/skills`をCodexから再利用できるようにリンクする | POSIX shell, coreutils |

`image-to-svg` は `librsvg`、Inkscape、browser のいずれか1つが必要です。候補を個別に記載し、複数導入を必須とはしません。

## Validation

検証は次の順で実行します。

```sh
bash .scripts/run-tests.sh
bash .scripts/validate-skills.sh
bash .scripts/validate-skills.sh --graph /tmp/skill-dependency-graph.md
```

`--graph PATH` は `.rules/skill-categories.yaml` の `depends_on` と `external_dependencies` から決定的なグラフを生成します。ERROR が1件でもあれば終了コード1、WARNINGだけなら終了コード0です。検証ERROR時は既存の出力を変更せず、出力先I/Oエラーは通常diagnosticを表示した上で終了コード2にします。

カテゴリ、スキル間依存、全スキルの外部依存の正本は `.rules/skill-categories.yaml`、検証基準は `.rules/skill-rules.yaml` です。README の `External Dependencies` 列は参照用です。スキルや依存を変更したときは `python3 .scripts/inventory.py` で4つのinventory YAMLを再生成します。通常検証は一時生成した期待値とchecked-in版を比較し、陳腐化をERRORにします。

例外は `.rules/skill-rules.yaml` の `validation.exceptions` に記録します。WARNING と `V-STR-002` に限り、`check_id`、`target`、非空の具体的な`reason`が揃った一意な記録だけを認め、抑制結果も理由付きWARNINGとして表示します。他のERROR、未知ID、存在しないtargetは禁止です。

## Setup

セットアップ手順は [SETUP.md](SETUP.md) を参照してください。

## Usage

エージェントにスキルが認識されると、`/skill-name` または `$skill-name` と入力して呼び出せます。
