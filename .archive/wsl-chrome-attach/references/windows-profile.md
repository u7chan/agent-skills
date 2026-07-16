# Windows Profile

## 専用 profile の Chrome を起動する

PowerShell で実行する。

    $chrome = "$env:ProgramFiles\Google\Chrome\Application\chrome.exe"
    & $chrome `
      --remote-debugging-port=9333 `
      --user-data-dir="C:\chrome-debug"

起動した Chrome で、ユーザーがログイン、認証、設定などを済ませる。この profile は通常 Chrome と分離され、次回以降も状態を残せる。

## 専用ショートカット

繰り返し使う場合は、Windows 側に専用ショートカットを作る。

- ショートカット名: `Chrome Debug`
- リンク先:

    "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9333 --user-data-dir="C:\chrome-debug"

PowerShell 例とショートカット例は、同じ専用 profile `C:\chrome-debug` を使う。別の保存先を使う場合は、両方の `--user-data-dir` を同じパスにそろえる。

このショートカットから起動した Chrome で、ログインや設定を済ませてから WSL 側のエージェントへ渡す。
