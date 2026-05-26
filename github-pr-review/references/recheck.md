# Recheck Workflow

## 対象の特定

- 直前または会話内でこのスキルが投稿したレビュー指摘だけを再チェック対象にする。
- 対象 PR は、会話内に残した PR URL/番号を優先し、なければ現在ブランチ名から特定する。
- 最新状態を確認するため、`gh pr view --json number,url,title,headRefName,baseRefName,commits` と `gh pr diff` を再取得する。
- 返信・Resolve の対象を特定するため、`gh api graphql` で `pullRequest.reviewThreads` を取得し、各 thread の `id`、`isResolved`、コメントの `databaseId`、`body`、`path`、`url`、`author` を確認する。

## review thread 対応付け

前回このスキルが投稿した指摘は、次の優先順で review thread と対応付ける。

1. 会話内に残した comment URL または comment ID が一致する thread。
2. `author` が現在の `gh` 認証ユーザーで、本文にこのスキルの AI エージェント識別メタ情報が含まれる thread。
3. コメント本文の主旨、ファイルパス、差分文脈が一致する thread。

既に `isResolved: true` の thread は原則として再コメントや Resolve 対象から外し、未解決 thread だけを再チェック対象にする。

## 分類

- `resolved`: 指摘内容が改善されている。
- `partial`: 一部改善されたが、まだ問題が残っている。
- `unresolved`: 改善されていない、または別の問題として残っている。
- `unknown`: 前回コメントや thread は特定できるが、最新差分・現在のファイル内容・取得権限のいずれかが不足し、修正有無を根拠付きで判断できない。

`unknown` は Resolve しない。

## アクション

- `resolved` の指摘は、返信できるスレッドであれば改善済みである旨を短く返信し、その review thread を Resolve する。
- `partial` または `unresolved` の指摘は、該当スレッドに再度コメントし、何がまだ問題かと次に直すべき内容を短く伝える。
- `unknown` の指摘は、判断できなかった理由をチャットで報告し、判断できないまま Resolve しない。
- すべての指摘が `resolved` の場合は、返信できるスレッドをすべて返信済みかつ Resolve 済みにする。
- コメント返信や Resolve ができない指摘がある場合は、overall comment で再チェック完了と対象指摘の状態を伝える。
- 返信・追加コメントにも AI エージェント識別メタ情報を欠けなく付け、`references/posting-rules.md` の再チェック用フォーマットに従う。
- `unknown` を overall comment に含めるのは、PR 上で対応履歴を残す必要がある場合、または同じ PR 上で他の再チェック結果を overall comment で報告する場合に限る。チャット報告で十分な場合は投稿しない。

## 禁止事項

- `gh pr review --approve` を実行しない。
- `gh api` で `APPROVE` review event を送らない。
- その他 PR approval に相当する操作を実行しない。
- 改善済みの指摘へ不要な再指摘をしない。

## 最終報告

- 再コメントした件数。
- Resolve した件数。
- overall comment で代替した件数。
- 未解決の有無。
- 判断不能がある場合は、その理由。
