# セットアップ

このリポジトリをローカルにクローンし、各エージェントのスキルディレクトリから参照できるようにシンボリックリンクを作成します。

## Claude Code

次のコマンドを実行します。

```sh
git clone git@github.com:u7chan/agent-skills.git
cd agent-skills
python3 .scripts/setup-skills.py --agent claude --home "$HOME"
```

`$HOME/.claude/skills/` に各スキルへのシンボリックリンクが作成されます。

## Codex

次のコマンドを実行します。

```sh
git clone git@github.com:u7chan/agent-skills.git
cd agent-skills
python3 .scripts/setup-skills.py --agent codex --home "$HOME"
```

## その他のエージェント

`.claude/skills` と互換性があるエージェントでは、`--agent` オプションに `claude` を指定して Claude Code と同じ手順でセットアップできます。

## リンクを解除する

```sh
python3 .scripts/setup-skills.py --agent claude --home "$HOME" --uninstall
python3 .scripts/setup-skills.py --agent codex --home "$HOME" --uninstall
```

リポジトリ本体も不要な場合は、シンボリックリンクを解除したあとに、クローンしたディレクトリを別途削除してください。
