# Posting Rules

## 返信本文の作り方

- ユーザーが返信本文を明示している場合は、その文面を使う。
- 明示がない場合は、対象コメントの論点と直近の修正内容から返信案をドラフトする。
- AI エージェント識別メタ情報は既定で付ける。ユーザーが明示的に不要と言った場合のみ省略する。
- 返信本文に改行が必要な場合は、実改行のテキストとして組み立てる。文字列としての `\n` をそのまま投稿しない。

## 投稿前のユーザー確認

- 投稿前に、対象コメント URL、返信種別、返信本文のプレビューをユーザーへ見せる。
- 投稿前確認は必須とし、ユーザーの承認があるまで外部投稿しない。
- 推奨確認文は次の形式とする。

```text
この内容で返信します。
対象: <comment-url>
種別: review comment reply / PR comment follow-up

<reply body preview>

"OK" と返信いただければ投稿します。
```

## 本文の渡し方

- 本文は原則として一時ファイル経由で渡す。単純な 1 行本文以外をシェル引数へ直接埋め込まない。
- バッククォート、`$()`、引用符、改行を含む本文はシェルに解釈されるため、`--body "..."` や `--field body="$(cat ...)"` の形を使わない。
- 推奨パターンは次のとおり。

```bash
TMP=$(mktemp)
trap 'rm -f "$TMP"' EXIT
printf '%s\n' "$BODY" > "$TMP"
```

## 投稿 API

- review comment への返信は、次のエンドポイントに固定する。

```bash
gh api -X POST "repos/$OWNER/$REPO/pulls/$PR_NUMBER/comments/$COMMENT_ID/replies" \
  -F "body=@$TMP"
```

- top-level PR comment には threaded reply がないため、新しい PR comment を追加する。
- その場合は、本文の冒頭に元コメント URL か comment ID を入れて関連を明示する。
- URL が分かっている場合の推奨フォーマット例:

```text
> Re: <comment-url>
```

```bash
gh api -X POST "repos/$OWNER/$REPO/issues/$PR_NUMBER/comments" \
  -F "body=@$TMP"
```

- `gh api` の実行後は、API 応答または再取得で本文が崩れていないことを確認する。
