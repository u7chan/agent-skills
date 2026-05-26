# Networking Options

## 案1: WSL mirrored networking を使う

Windows のユーザープロファイル直下にある `.wslconfig` に設定する。

    [wsl2]
    networkingMode=mirrored
    localhostForwarding=true

PowerShell で WSL を再起動する。

    wsl --shutdown

WSL 側で `wslinfo --networking-mode` が `mirrored` になったことを確認し、再度診断スクリプトを実行する。

期待値は WSL 側から `http://127.0.0.1:9333/json/version` または該当 port の `/json/version` が通ること。

## 案2: Windows portproxy で中継する

WSL を NAT mode のまま使う場合は、Windows 側で portproxy を使って Windows localhost の CDP を WSL から届く address へ中継する。

管理者 PowerShell で実行する。

    netsh interface portproxy add v4tov4 listenaddress=0.0.0.0 listenport=9334 connectaddress=127.0.0.1 connectport=9333

複数行で貼り付けられる環境では、同じ内容を次のように書いてもよい。

    netsh interface portproxy add v4tov4 `
      listenaddress=0.0.0.0 `
      listenport=9334 `
      connectaddress=127.0.0.1 `
      connectport=9333

設定を確認する。

    netsh interface portproxy show all

WSL 側で default gateway を確認する。

    ip route | grep default

既定 port `9333` の通常診断では、診断スクリプトが `http://<default-gateway>:9334` も自動で試す。成功した場合は、その URL が `--browserUrl` として表示される。

明示的に portproxy 側だけを確認したい場合や、候補を固定して優先したい場合は candidate として渡す。

    python3 <skill-dir>/scripts/diagnose_chrome_debug.py \
      --candidate http://172.28.160.1:9334 \
      --port 9334

成功した場合、MCP には portproxy 側の URL を渡す。

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

portproxy は CDP を Windows host 側で受けるため、作業後に不要なら削除する。

    netsh interface portproxy delete v4tov4 `
      listenaddress=0.0.0.0 `
      listenport=9334

## NAT mode で成功した実用フロー

1. `Chrome Debug` ショートカットで専用 profile の Chrome を起動する。
2. Windows 側で `http://127.0.0.1:9333/json/version` が成功することを確認する。
3. 管理者 PowerShell で `netsh interface portproxy add v4tov4 listenaddress=0.0.0.0 listenport=9334 connectaddress=127.0.0.1 connectport=9333` を実行する。
4. WSL 側で `python3 <skill-dir>/scripts/diagnose_chrome_debug.py` を実行する。
5. 成功した `http://<default-gateway>:9334` を `chrome-devtools-mcp` の `--browserUrl` に渡す。
6. エージェントを再起動して MCP 設定を読み込み、`wsl-chrome-attach-use` で attach 済み Chrome を操作する。

`portproxy` 設定は Windows 側に残る。2回目以降は、多くの場合 `Chrome Debug` ショートカットで専用 profile の Chrome を起動するだけで、WSL 側から同じ `http://<default-gateway>:9334` に再接続できる。
