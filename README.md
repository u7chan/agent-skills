# agent skills

AI エージェント用のカスタムスキル集です。

## Available Skills

| Skill | Description |
|-------|-------------|
| [commit-message](commit-message/) | コミットメッセージとブランチ名を提案 |
| [commit-message-monorepo](commit-message-monorepo/) | モノレポ向けのコミットメッセージとブランチ名を提案 |

## Setup

Claude Code を使用する場合:

```sh
git clone git@github.com:u7chan/agent-skills.git
cd agent-skills
mkdir -p "$HOME/.claude/skills"
ln -sf "$(pwd)" "$HOME/.claude/skills"
```

> **Note:** `$HOME/.claude/skills` ディレクトリが既に存在する場合は、上記コマンドをそのまま実行してください。

シンボリックリンクを解除する場合:

```sh
rm "$HOME/.claude/skills"
```

> **Note:** Claude Code 以外のエージェントでは、設定ディレクトリのパスが異なる場合があります。

## Usage

エージェントにスキルが認識されると、`/skill-name` または `@skill-name` と入力して呼び出せます。

## Project Structure

```
agent-skills/
├── README.md
├── commit-message/
│   └── SKILL.md
├── commit-message-monorepo/
│   └── SKILL.md
└── .samples/
    └── ...
```
