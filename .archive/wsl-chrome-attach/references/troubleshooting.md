# Troubleshooting

## 基本切り分け

診断スクリプトが全候補に失敗したら、順番に切り分ける。

1. Windows PowerShell で `Invoke-RestMethod http://127.0.0.1:9333/json/version` が成功するか確認する。
2. 失敗する場合は、Chrome が `--remote-debugging-port=9333` と専用 `--user-data-dir` で起動しているか確認する。
3. Windows では成功し、WSL では失敗する場合は、WSL の networking mode、Windows Firewall、Chrome の listen 範囲を確認する。
4. 既存 Chrome にコマンドが吸収されている疑いがある場合は、remote debugging 付き Chrome をすべて閉じ、専用 profile で起動し直す。

WSL が NAT mode で、Windows 側 Chrome が `127.0.0.1` にだけ listen している場合、Windows 上では成功しても WSL から届かないことがある。この場合、NAT mode のまま `localhost` attach を期待しない。

WSL から届かないからといって、すぐに `--remote-debugging-address=0.0.0.0` を使わない。必要な場合だけ、CDP が LAN 側へ露出し得ることをユーザーに確認してから検討する。

## Chrome 未起動時の期待値

`portproxy` 設定が残っていても、専用 profile の Chrome が未起動なら attach は失敗する。WSL 側の診断では、全候補が `Connection refused` や `timeout` になり、成功 URL は表示されない。

この場合はまず Windows 側で `Chrome Debug` ショートカットから Chrome を起動し、`Invoke-RestMethod http://127.0.0.1:9333/json/version` が成功することを確認する。`portproxy` は永続設定なので、削除していなければ通常は再設定不要。

## 推奨判断

| 方法 | 推奨 | 備考 |
| --- | --- | --- |
| WSL mirrored networking | 高 | `localhost` attach を素直に扱いやすい |
| Windows portproxy | 高 | NAT mode のまま回避できる |
| Chrome の `0.0.0.0` bind 期待 | 低 | Chrome 側が `127.0.0.1` only に見えることがある |
| NAT mode のまま localhost attach | 不可 | WSL localhost と Windows localhost は別 |
