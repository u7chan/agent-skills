# Playwright CLI コマンド

公式の最新版は [Microsoft Playwright CLI Skill](https://github.com/microsoft/playwright-cli/blob/main/skills/playwright-cli/SKILL.md) で確認する。
この表は日常的な画面検証に必要な入口であり、全コマンドの複製ではない。

| 用途 | コマンド例 | 注意点 |
| --- | --- | --- |
| セッション開始・移動 | `open URL` / `goto URL` | 終了時は必ず `close` |
| 状態取得 | `snapshot` / `find "文字列"` | 操作前・DOM更新後に再取得 |
| ref操作 | `click e15` / `fill e5 "値"` / `press Enter` | refは最新snapshotのものだけ使う |
| semantic locator | `click "getByRole('button', { name: '送信' })"` | role / label / test idを優先 |
| 遷移 | `go-back` / `go-forward` / `reload` | 完了後にsnapshot |
| キーボード | `press Enter` / `keydown Shift` / `keyup Shift` | 修飾キーは必ず解放する |
| マウス | `hover e4` / `drag e2 e8` / `mousewheel 0 100` | 実行後に表示状態を確認 |
| 選択・入力 | `select e9 "value"` / `check e12` / `upload file` | 変更後に結果を確認 |
| タブ | `tab-list` / `tab-new URL` / `tab-select 0` | 操作対象タブを明示 |
| state | `state-save auth.json` / `state-load auth.json` | 認証情報を含むため扱いに注意 |
| network | `route "**/*.jpg" --status=404` / `unroute` | モックは必要な検証だけに限定 |
| 証跡・診断 | `screenshot` / `console` / `requests` / `tracing-start` | 必要なときだけ採取 |

## 旧 `browser-use` からの対応

| 旧操作 | Playwright CLI |
| --- | --- |
| `open URL` | `open URL` |
| `state` | `snapshot` |
| `click 番号` | `click eNN` |
| `input 番号 "値"` | `fill eNN "値"` |
| `keys "Enter"` | `press Enter` |
| `screenshot` | `screenshot` |
| `close` | `close` |

待機専用コマンドに頼らず、操作後のsnapshotで画面状態を確認する。追加のコマンド、
`--raw` / `--json`、ネットワークrouteは公式仕様を確認してから使う。
