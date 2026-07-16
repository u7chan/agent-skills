---
name: wsl-chrome-attach
description: WSL2 上の Codex や Claude Code などのコーディングエージェントから、Windows 側で remote debugging を有効にした Chrome へ接続診断し、chrome-devtools-mcp に渡す browserUrl を特定する。認証や設定を人間が済ませた専用 Chrome profile を AI 操作へバトンタッチしたい時に使う。
---

# WSL Chrome Attach

WSL2 上のエージェントから Windows 側 Chrome の Chrome DevTools Protocol (CDP) endpoint に到達できるか確認し、MCP 設定に使う `--browserUrl=...` を決める。

このスキルは CDP endpoint の接続診断とMCP設定用URLの特定までを扱う。ブラウザ操作は対象外とする。

# 必須注意

- CDP はブラウザを強力に操作できる。通常利用中の Chrome profile ではなく、専用 profile を使う。
- `--remote-debugging-address=0.0.0.0` を正式手順にしない。公開範囲を広げる場合はリスクを明示してユーザー判断にする。
- 作業後は remote debugging 付きで起動した Chrome を閉じる。
- WSL から届かないからといって、すぐに `--remote-debugging-address=0.0.0.0` を使わない。

# 必要環境

- WSL2 上で `python3` が実行できること。診断スクリプトは Python 3 標準ライブラリだけを使う。
- Windows 側で Google Chrome を起動できること。
- NAT mode で portproxy を使う場合は、Windows 側で管理者 PowerShell を使えること。

# 参照マップ

- Windows 側の専用 Chrome profile 起動: `references/windows-profile.md`
- mirrored networking / portproxy / NAT mode の詳細: `references/networking-options.md`
- 失敗時の切り分けと推奨判断: `references/troubleshooting.md`

# 手順

## 1. Windows 側で専用 profile の Chrome を起動する

PowerShell で remote debugging 用の専用 profile を起動する。詳細とショートカット例は `references/windows-profile.md` を読む。

    $chrome = "$env:ProgramFiles\Google\Chrome\Application\chrome.exe"
    & $chrome `
      --remote-debugging-port=9333 `
      --user-data-dir="C:\chrome-debug"

起動した Chrome で、ユーザーがログイン、認証、設定などを済ませる。この profile は通常 Chrome と分離され、次回以降も状態を残せる。

## 2. Windows 側で CDP endpoint を確認する

PowerShell で確認する。

    Invoke-RestMethod http://127.0.0.1:9333/json/version

`Browser` と `webSocketDebuggerUrl` が返れば、Chrome 側では remote debugging が開いている。

## 3. WSL 側から接続診断する

スキル同梱の診断スクリプトを実行する。`<skill-dir>` は、この `SKILL.md` が置かれている `wsl-chrome-attach` ディレクトリに置き換える。

    python3 <skill-dir>/scripts/diagnose_chrome_debug.py

必要なら port を変える。

    python3 <skill-dir>/scripts/diagnose_chrome_debug.py --port 9222

明示 URL を最優先で試したい場合は `CHROME_DEBUG_URL` を使う。失敗しても他候補の診断は続ける。

    CHROME_DEBUG_URL=http://127.0.0.1:9333 \
    python3 <skill-dir>/scripts/diagnose_chrome_debug.py

診断対象は次のローカル・ホスト系候補に限定する。

- `CHROME_DEBUG_URL`
- `127.0.0.1`
- `localhost`
- `host.docker.internal`
- WSL の default gateway
- `/etc/resolv.conf` の `nameserver`

既定 port `9333` で診断する場合は、WSL NAT mode と Windows portproxy の実用構成向けに `http://<default-gateway>:9334` も自動で候補に含める。これは `0.0.0.0:9334 -> 127.0.0.1:9333` の portproxy が残っている環境を検出するための候補であり、成功した場合だけ `--browserUrl=http://<default-gateway>:9334` として使う。

## 4. 成功 URL を MCP 設定に使う

診断成功時に表示される `--browserUrl=...` を `chrome-devtools-mcp` に渡す。

    {
      "mcpServers": {
        "chrome-devtools": {
          "command": "npx",
          "args": [
            "chrome-devtools-mcp@latest",
            "--browserUrl=http://127.0.0.1:9333"
          ]
        }
      }
    }

`--browserUrl` の値は診断スクリプトの成功結果に合わせる。WSL networking mode によって `127.0.0.1`、`localhost`、Windows host IP のどれが通るかは変わる。

MCP 設定を反映するには、利用中のエージェントを再起動して MCP サーバーを読み込ませる。再起動後のブラウザ操作は、このスキルの対象外とする。

# 失敗時の切り分け

診断スクリプトが全候補に失敗したら、`references/troubleshooting.md` を読み、順番に切り分ける。

1. Windows PowerShell で `Invoke-RestMethod http://127.0.0.1:9333/json/version` が成功するか確認する。
2. 失敗する場合は、Chrome が `--remote-debugging-port=9333` と専用 `--user-data-dir` で起動しているか確認する。
3. Windows では成功し、WSL では失敗する場合は、WSL の networking mode、Windows Firewall、Chrome の listen 範囲を確認する。
4. 既存 Chrome にコマンドが吸収されている疑いがある場合は、remote debugging 付き Chrome をすべて閉じ、専用 profile で起動し直す。

# 解決策の選び方

- WSL mirrored networking を使う場合は、`references/networking-options.md` の「案1」を読む。
- NAT mode のまま使う場合は、Windows portproxy を使う。詳細は `references/networking-options.md` の「案2」と「NAT mode で成功した実用フロー」を読む。
- `portproxy` 設定が残っていても、専用 profile の Chrome が未起動なら attach は失敗する。まず Chrome 起動と Windows 側 `/json/version` の成功を確認する。

# 品質チェック

- 専用 Chrome profile を使う注意が先頭にある
- `0.0.0.0` bind を正式手順にしない注意が先頭にある
- 診断スクリプトの実行方法と成功 URL の使い方が本文だけで分かる
- NAT mode / portproxy の詳細は `references/` に分離されている
- 接続診断とMCP設定用URLの特定までが対象であることが明記されている
