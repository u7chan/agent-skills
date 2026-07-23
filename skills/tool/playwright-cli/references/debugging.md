# 診断と証跡

## 最小の切り分け

1. `snapshot` でURL、表示内容、最新refを確認する。
2. 操作を一つだけ再実行し、直後に再度snapshotを取る。
3. 問題が続く場合だけconsole、requests、traceを採取する。
4. 診断後も必ず `close` する。

```bash
playwright-cli console
playwright-cli requests
playwright-cli tracing-start
# 再現操作
playwright-cli tracing-stop
playwright-cli close
```

視覚的な差分が必要な場合だけ `screenshot --filename=after.png` を使う。snapshotは構造・
操作対象の確認を優先するため、通常はこちらを使う。

## CLIが見つからない場合

グローバルの `playwright-cli` がなければ、依存関係を追加せずにローカル版を確認する。

```bash
npx --no-install playwright cli
```

この確認に失敗した場合は、原因を断定せず「ローカルCLIの可用性を確認できなかった」と
案内する。自動インストール、ブラウザダウンロード、代替操作は行わない。必要なら
Playwright CLIの導入または環境修正をユーザーに依頼する。

## 出力の扱い

`--raw` は出力を他ツールへ渡すとき、`--json` は構造化した結果が必要なときに使う。

```bash
playwright-cli --raw snapshot
playwright-cli list --json
```

認証情報、cookie、フォーム入力値、trace、screenshotには機微情報が含まれ得るため、
必要な範囲だけ保存し、成果物へ含めない。
