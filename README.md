# agent skills

AI エージェント用のカスタムスキル集です。

## Available Skills

| Skill | Description |
|-------|-------------|
| [commit](commit/) | コミットメッセージとブランチ名を提案 |
| [commit-monorepo](commit-monorepo/) | モノレポ向けのコミットメッセージとブランチ名を提案 |
| [pr](pr/) | PR 本文をマークダウン形式で提案 |
| [plan-creator](plan-creator/) | 実装計画の作成と管理 |

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

シンボリックリンクを解除する場合:

```sh
rm "$HOME/.claude/skills"
```

> [!NOTE]
> Claude Code 以外のエージェントでは、設定ディレクトリのパスが異なる場合があります。

## Usage

エージェントにスキルが認識されると、`/skill-name` または `@skill-name` と入力して呼び出せます。

## Project Structure

```
agent-skills/
├── README.md
├── commit/
│   └── SKILL.md
├── commit-monorepo/
│   └── SKILL.md
├── pr/
│   └── SKILL.md
├── plan-creator/
│   └── SKILL.md
└── .samples/
    └── ...
```
