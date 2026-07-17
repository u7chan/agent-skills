# セットアップ

このリポジトリをローカルにクローンし、各エージェントのスキルディレクトリから参照できるようにシンボリックリンクを作成します。

## Claude Code

次のコマンドを実行します。

```sh
git clone git@github.com:u7chan/agent-skills.git
cd agent-skills
mkdir -p "$HOME/.claude/skills"
ln -sf "$(pwd)" "$HOME/.claude/skills"
```

これにより、`$HOME/.claude/skills/agent-skills` からこのリポジトリを参照できるようになります。`$HOME/.claude/skills` がすでに存在していても、そのまま実行できます。

## Codex

次のコマンドを実行します。

```sh
git clone git@github.com:u7chan/agent-skills.git
cd agent-skills
mkdir -p "$HOME/.codex"
ln -sfn "$(pwd)" "$HOME/.codex/skills"
```

これにより、`$HOME/.codex/skills` からこのリポジトリを参照できるようになります。既存のシンボリックリンクがある場合は、新しいリンク先に更新されます。

## その他のエージェント

`.claude/skills` と互換性があるエージェントでは、Claude Code と同じ手順でセットアップできます。対応状況は、使用するエージェントのドキュメントを確認してください。

## シンボリックリンクを解除する

使用しているエージェントに合わせて、対象のシンボリックリンクを削除します。

```sh
rm "$HOME/.claude/skills/agent-skills"
rm "$HOME/.codex/skills"
```

リポジトリ本体も不要な場合は、シンボリックリンクを解除したあとに、クローンしたディレクトリを別途削除してください。
