# Setup

## Claude Code を使用する場合

```sh
git clone git@github.com:u7chan/agent-skills.git
cd agent-skills
mkdir -p "$HOME/.claude/skills"
ln -sf "$(pwd)" "$HOME/.claude/skills"
```

> [!NOTE]
> `$HOME/.claude/skills` ディレクトリが既に存在する場合は、上記コマンドをそのまま実行してください。

## Codex を使用する場合

```sh
git clone git@github.com:u7chan/agent-skills.git
cd agent-skills
mkdir -p "$HOME/.codex"
ln -sfn "$(pwd)" "$HOME/.codex/skills"
```

> [!NOTE]
> `"$HOME/.codex/skills"` が既に存在する場合は、上記コマンドをそのまま実行してください。

## シンボリックリンクを解除する場合

```sh
rm "$HOME/.claude/skills"
rm "$HOME/.codex/skills"
```

> [!NOTE]
> Claude Code 以外のエージェントでは、設定ディレクトリのパスが異なる場合があります。
