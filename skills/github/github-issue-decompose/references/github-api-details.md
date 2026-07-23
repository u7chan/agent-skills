# GitHub API / CLI Reference

github-issue-decompose が使用する `gh` コマンドとGitHub APIの詳細。

## 前提

- GitHubのSub-issue機能が有効なリポジトリであること
- `gh auth status` が成功し、対象リポジトリへの読み取り・書き込み権限があること
- `--parent` オプションおよび `--json subIssues` フィールドは `gh` の比較的新しいバージョンで提供される
- 必要ghバージョン: `gh` v2.94.0 以降（`--parent` フラグ、`parent` / `subIssues` JSONフィールド対応のため）

## 使用コマンド一覧

### 1. 親Issueの取得

```sh
gh issue view <issue-number> \
  --repo <owner/repo> \
  --json number,title,body,labels,comments,url,state,projectItems
```

- `comments` フィールドには全コメントの本文・作成者の配列が含まれる
- `--comments` フラグではなく `--json` に `comments` を含める

### 2. 既存Sub-issueの取得

GitHub CLIでネイティブSub-issueを検索する:

```sh
gh issue list \
  --repo <owner/repo> \
  --search "is:issue parent-issue:\"<owner>/<repo>#<parent-number>\"" \
  --json number,title,body,url,labels,state \
  --state all
```

- `parent-issue:` 検索はGitHubのSub-issue機能に依存する
- `--state all` でOpen/Closed両方を取得し、重複防止に使う

### 3. 既存ラベルの取得

```sh
gh label list --repo <owner/repo> --json name --jq '.[].name'
```

- 新しいラベルは作成しない
- 既存ラベルのうち、Sub-issueの内容に明確に合うものだけを使う

### 4. Sub-issueの作成

```sh
gh issue create \
  --repo <owner/repo> \
  --title "<title>" \
  --body-file <temp-file> \
  --label "<label1>,<label2>"
```

- `--body-file` を使い、Markdownをシェル引数へ埋め込まない
- ラベルはカンマ区切りで指定する

### 5. Sub-issueの親子付け

```sh
gh issue edit <child-number> \
  --repo <owner/repo> \
  --parent <parent-number>
```

- GitHubネイティブの親子関係が設定される
- 親子付け後、親Issueに自動でSub-issue progressが表示される
- この操作はMarkdownチェックリストの代わりになる

### 6. Sub-issueの再取得確認

```sh
gh issue view <child-number> \
  --repo <owner/repo> \
  --json url,title,body,labels,state,parent
```

- `parent` フィールドで親子関係を確認する

### 7. 親Issue本文の更新

```sh
gh issue edit <parent-number> \
  --repo <owner/repo> \
  --body-file <temp-file>
```

- 全Sub-issueの作成・親子付け・確認が成功した後にだけ実行する
- `--body-file` を使い、Markdownをシェル引数へ埋め込まない

### 8. 最終確認

```sh
gh issue view <parent-number> \
  --repo <owner/repo> \
  --json url,title,body,labels,state,subIssues
```

- `subIssues` フィールドで全Sub-issueの一覧とprogressを確認する
- 各Sub-issueのURL、title、stateが含まれる

## エラーハンドリング

| 状況 | 対応 |
|------|------|
| `gh` 未認証 | 停止。`gh auth status` で確認を促す |
| 書き込み権限なし | 停止。読み取りは可能でも親子付け・作成は不可 |
| Sub-issue機能未対応 | 停止。GitHubのSub-issueが有効か確認を促す |
| `--parent` オプション非対応 | 停止。`gh` のバージョンアップデートを促す |
| 作成途中のAPI失敗 | 親本文変更せず、成功したIssue URLと失敗操作を報告 |
| 再実行時の重複 | 既存Sub-issueを再取得し、同一目的の重複作成を防止 |

## 冪等性

- 再実行時は Fetch 工程で既存Sub-issueをすべて取得する
- Analyze で提案した分割単位のうち、既存Sub-issueと同一目的のものはCreate対象から除外する
- すでにEpic化済みの親Issueを再分解しようとした場合は、現状のSub-issue構成を報告し、追加工のみ確認する
