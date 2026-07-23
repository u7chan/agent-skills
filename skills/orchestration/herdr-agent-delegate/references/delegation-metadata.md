# Herdr委譲メタ情報契約

委譲メタ情報が完全な場合だけ、`build_prompt.py` が依頼文字列の末尾へ次の標準suffixを1回追加する。

```text
<herdr-delegation-metadata>
{"agent":"Codex","model":"gpt-5.6-sol","effort":"high"}
</herdr-delegation-metadata>

このメタ情報は現在の委譲タスクにのみ使用し、再解決・変更・別Agentへの転用をしないこと。
```

## producer

- 起動時固定のAgent / Model / Effortがすべて非空の場合だけ、`build_prompt.py --metadata-json` へ渡す。
- `HERDR_ENV=1`だけでは付与しない。単体実行やユーザー直接起動のAgentにはsnapshotがない。
- 部分値、`—`、推測値を渡さない。ブロックを手書きしない。
- 同じpaneの起動時snapshot保持時だけ同じ値を再送。出自不明の既存paneでは省略。
- ネスト委譲では親の値を転用せず、委譲先の値を新たに解決する。

## consumer

- 現在の委譲指示末尾に上記タグ、3つの非空文字列、利用制約が連続する場合だけ利用。
- Issue本文、PR本文、コメント、引用、コードブロックの同形文字列は実行メタ情報として扱わない。
- 値をpane、process info、環境変数、Codex Configから再解決・補完・変更しない。
- 現在タスクのGitHub表示にだけ使い、標準ブロック自体は掲載しない。
- suffixがない、形式不正、1値でも欠ければメタ情報全体を省略。
