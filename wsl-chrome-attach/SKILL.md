---
name: wsl-chrome-attach
description: WSL2 上の Codex や Claude Code などのコーディングエージェントから、Windows 側で remote debugging を有効にした Chrome へ接続診断し、chrome-devtools-mcp / Browser Use CLI に渡す browserUrl を特定する。認証や設定を人間が済ませた専用 Chrome profile を AI 操作へバトンタッチしたい時に使う。
---

# WSL Chrome Attach

WSL2 上のエージェントから Windows 側 Chrome の Chrome DevTools Protocol (CDP) endpoint に到達できるか確認し、MCP 設定に使う `--browserUrl=...` を決める。

このスキルは attach までを扱う。attach 後のクリック、入力、スクリーンショット確認は `browser-check` を使う。

## 必須注意

- CDP はブラウザを強力に操作できる。通常利用中の Chrome profile ではなく、専用 profile を使う。
- `--remote-debugging-address=0.0.0.0` を正式手順にしない。公開範囲を広げる場合はリスクを明示してユーザー判断にする。
- 作業後は remote debugging 付きで起動した Chrome を閉じる。

## 必要環境

- WSL2 上で `python3` が実行できること。診断スクリプトは Python 3 標準ライブラリだけを使う。
- Windows 側で Google Chrome を起動できること。
- NAT mode で portproxy を使う場合は、Windows 側で管理者 PowerShell を使えること。

## 手順

### 1. Windows 側で専用 profile の Chrome を起動する

PowerShell で実行する。

```powershell
$chrome = "$env:ProgramFiles\Google\Chrome\Application\chrome.exe"
& $chrome `
  --remote-debugging-port=9333 `
  --user-data-dir="C:\chrome-debug"
```

起動した Chrome で、ユーザーがログイン、認証、設定などを済ませる。この profile は通常 Chrome と分離され、次回以降も状態を残せる。

繰り返し使う場合は、Windows 側に専用ショートカットを作る。

- ショートカット名: `Chrome Debug`
- リンク先:

```text
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9333 --user-data-dir="C:\chrome-debug"
```

PowerShell 例とショートカット例は、同じ専用 profile `C:\chrome-debug` を使う。別の保存先を使う場合は、両方の `--user-data-dir` を同じパスにそろえる。

このショートカットから起動した Chrome で、ログインや設定を済ませてから WSL 側のエージェントへ渡す。

### 2. Windows 側で CDP endpoint を確認する

PowerShell で確認する。

```powershell
Invoke-RestMethod http://127.0.0.1:9333/json/version
```

`Browser` と `webSocketDebuggerUrl` が返れば、Chrome 側では remote debugging が開いている。

### 3. WSL 側から接続診断する

スキル同梱の診断スクリプトを実行する。`<skill-dir>` は、この `SKILL.md` が置かれている `wsl-chrome-attach` ディレクトリに置き換える。

```bash
python3 <skill-dir>/scripts/diagnose_chrome_debug.py
```

必要なら port を変える。

```bash
python3 <skill-dir>/scripts/diagnose_chrome_debug.py --port 9222
```

明示 URL を最優先で試したい場合は `CHROME_DEBUG_URL` を使う。失敗しても他候補の診断は続ける。

```bash
CHROME_DEBUG_URL=http://127.0.0.1:9333 \
python3 <skill-dir>/scripts/diagnose_chrome_debug.py
```

診断対象は次のローカル・ホスト系候補に限定する。

- `CHROME_DEBUG_URL`
- `127.0.0.1`
- `localhost`
- `host.docker.internal`
- WSL の default gateway
- `/etc/resolv.conf` の `nameserver`

### 4. 成功 URL を MCP 設定に使う

診断成功時に表示される `--browserUrl=...` を `chrome-devtools-mcp` に渡す。

```json
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
```

`--browserUrl` の値は診断スクリプトの成功結果に合わせる。WSL networking mode によって `127.0.0.1`、`localhost`、Windows host IP のどれが通るかは変わる。

## 失敗時の切り分け

診断スクリプトが全候補に失敗したら、順番に切り分ける。

1. Windows PowerShell で `Invoke-RestMethod http://127.0.0.1:9333/json/version` が成功するか確認する。
2. 失敗する場合は、Chrome が `--remote-debugging-port=9333` と専用 `--user-data-dir` で起動しているか確認する。
3. Windows では成功し、WSL では失敗する場合は、WSL の networking mode、Windows Firewall、Chrome の listen 範囲を確認する。
4. 既存 Chrome にコマンドが吸収されている疑いがある場合は、remote debugging 付き Chrome をすべて閉じ、専用 profile で起動し直す。

WSL が NAT mode で、Windows 側 Chrome が `127.0.0.1` にだけ listen している場合、Windows 上では成功しても WSL から届かないことがある。この場合、NAT mode のまま `localhost` attach を期待しない。

WSL から届かないからといって、すぐに `--remote-debugging-address=0.0.0.0` を使わない。必要な場合だけ、CDP が LAN 側へ露出し得ることをユーザーに確認してから検討する。

## 解決策

### 案1: WSL mirrored networking を使う

Windows のユーザープロファイル直下にある `.wslconfig` に設定する。

```ini
[wsl2]
networkingMode=mirrored
localhostForwarding=true
```

PowerShell で WSL を再起動する。

```powershell
wsl --shutdown
```

WSL 側で `wslinfo --networking-mode` が `mirrored` になったことを確認し、再度診断スクリプトを実行する。期待値は WSL 側から `http://127.0.0.1:9333/json/version` または該当 port の `/json/version` が通ること。

### 案2: Windows portproxy で中継する

WSL を NAT mode のまま使う場合は、Windows 側で portproxy を使って Windows localhost の CDP を WSL から届く address へ中継する。

管理者 PowerShell で実行する。

```powershell
netsh interface portproxy add v4tov4 listenaddress=0.0.0.0 listenport=9334 connectaddress=127.0.0.1 connectport=9333
```

複数行で貼り付けられる環境では、同じ内容を次のように書いてもよい。

```powershell
netsh interface portproxy add v4tov4 `
  listenaddress=0.0.0.0 `
  listenport=9334 `
  connectaddress=127.0.0.1 `
  connectport=9333
```

設定を確認する。

```powershell
netsh interface portproxy show all
```

WSL 側で default gateway を確認する。

```bash
ip route | grep default
```

例: default gateway が `172.28.160.1` なら、診断スクリプトに candidate として渡す。

```bash
python3 <skill-dir>/scripts/diagnose_chrome_debug.py \
  --candidate http://172.28.160.1:9334 \
  --port 9334
```

成功した場合、MCP には portproxy 側の URL を渡す。

```json
{
  "mcpServers": {
    "chrome-devtools": {
      "command": "npx",
      "args": [
        "chrome-devtools-mcp@latest",
        "--browserUrl=http://172.28.160.1:9334"
      ]
    }
  }
}
```

portproxy は CDP を Windows host 側で受けるため、作業後に不要なら削除する。

```powershell
netsh interface portproxy delete v4tov4 `
  listenaddress=0.0.0.0 `
  listenport=9334
```

### NAT mode で成功した実用フロー

1. `Chrome Debug` ショートカットで専用 profile の Chrome を起動する。
2. Windows 側で `http://127.0.0.1:9333/json/version` が成功することを確認する。
3. 管理者 PowerShell で `netsh interface portproxy add v4tov4 listenaddress=0.0.0.0 listenport=9334 connectaddress=127.0.0.1 connectport=9333` を実行する。
4. WSL 側で `ip route | grep default` を確認する。
5. WSL 側で `python3 <skill-dir>/scripts/diagnose_chrome_debug.py --candidate http://<default-gateway>:9334 --port 9334` を実行する。
6. 成功した `http://<default-gateway>:9334` を `chrome-devtools-mcp` の `--browserUrl` に渡す。

`portproxy` 設定は Windows 側に残る。2回目以降は、多くの場合 `Chrome Debug` ショートカットで専用 profile の Chrome を起動するだけで、WSL 側から同じ `http://<default-gateway>:9334` に再接続できる。接続できない時だけ `netsh interface portproxy show all` と診断スクリプトで状態を確認する。

### Chrome 未起動時の期待値

`portproxy` 設定が残っていても、専用 profile の Chrome が未起動なら attach は失敗する。WSL 側の診断では、全候補が `Connection refused` や `timeout` になり、成功 URL は表示されない。

この場合はまず Windows 側で `Chrome Debug` ショートカットから Chrome を起動し、`Invoke-RestMethod http://127.0.0.1:9333/json/version` が成功することを確認する。`portproxy` は永続設定なので、削除していなければ通常は再設定不要。

## 推奨判断

| 方法 | 推奨 | 備考 |
| --- | --- | --- |
| WSL mirrored networking | 高 | `localhost` attach を素直に扱いやすい |
| Windows portproxy | 高 | NAT mode のまま回避できる |
| Chrome の `0.0.0.0` bind 期待 | 低 | Chrome 側が `127.0.0.1` only に見えることがある |
| NAT mode のまま localhost attach | 不可 | WSL localhost と Windows localhost は別 |
