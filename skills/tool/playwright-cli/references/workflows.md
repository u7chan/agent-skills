# ワークフロー例

## localhost smoke test

```bash
playwright-cli open http://localhost:3000
playwright-cli snapshot
playwright-cli click e15
playwright-cli snapshot
playwright-cli close
```

実行前に対象アプリのdev serverが起動していることを確認する。クリック後に遷移・保存・
DOM更新が起きたら、古いrefを使わずsnapshotから対象を取り直す。

## フォーム送信

```bash
playwright-cli open http://localhost:3000/sign-in
playwright-cli snapshot
playwright-cli fill e5 "user@example.com"
playwright-cli fill e6 "password"
playwright-cli click "getByRole('button', { name: 'Sign in' })"
playwright-cli snapshot
playwright-cli close
```

入力値や認証情報をログ・証跡へ不必要に残さない。

## 複数タブ

```bash
playwright-cli tab-new https://example.com/other
playwright-cli tab-list
playwright-cli tab-select 0
playwright-cli snapshot
```

タブを切り替えるたびに現在のページとsnapshotを確認する。

## 認証状態の保存と復元

明示的な許可がある場合だけ、必要最小限の場所へ保存する。

```bash
playwright-cli state-save auth.json
playwright-cli close
playwright-cli open http://localhost:3000
playwright-cli state-load auth.json
playwright-cli snapshot
```

`auth.json` はcookie・localStorage等を含み得る。共有、コミット、長期保存はしない。
