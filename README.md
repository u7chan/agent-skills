# agent skills

AI エージェント用のカスタムスキル集です。

## Available Skills

| Skill | Description |
|-------|-------------|
| [branch](branch/) | ブランチ名を提案し、ブランチを作成 |
| [commit](commit/) | コミットメッセージを提案 |
| [pr](pr/) | コンテキストからPR本文をマークダウン形式で提案 |
| [pr-github](pr-github/) | PR本文作成後にGitHubにPRを作成 |
| [plan-to-issue-skill](plan-to-issue-skill/) | 設計プラン合意後に Issue を作成 |
| [my-skill-author](my-skill-author/) | SKILL.md ファイルの作成と改善 |

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

## Project Structure

```
agent-skills/
├── README.md
├── branch/
│   └── SKILL.md
├── commit/
│   └── SKILL.md
├── pr/
│   └── SKILL.md
├── pr-github/
│   └── SKILL.md
├── plan-to-issue-skill/
│   └── SKILL.md
├── my-skill-author/
│   └── SKILL.md
└── .samples/
    └── ...
```
