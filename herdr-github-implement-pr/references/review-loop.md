# Herdr レビュー・FB 対応ループ

PR 作成成功後に読み、`herdr-agent-delegate` の直接送信、待機、出力回収手順を適用する。この文書と参照スキルが衝突する場合、このワークフロー固有の Agent 解決、反復上限、cleanup 規則を優先する。

## PR Work Metadata スナップショット

レビューとレビューFBも、`implementation-delegation.md` の「PR Work Metadata スナップショット」と同じ用語・所有者・取得時点の契約に従う。PR 作成前に担当と値が確定していれば、その固定済みスナップショットだけを PR 本文に使う。この文書で PR 作成後に解決した値は、過去の PR 本文へ追加・更新しない。

## 1. プリフライト

- `HERDR_ENV=1`、空でない `HERDR_PANE_ID`、`herdr`、利用する Agent CLI を確認する。
- `herdr pane current --current` から親の pane、tab、cwd、Agent 種別を取得する。
- 実装を行った作業ディレクトリの絶対パスと、確認済み PR URL を保持する。
- Herdr 外、CLI 不足、認証・trust 待ちはレビュー失敗とし、PR 成功を取り消さない。

## 2. レビュー Agent を解決する

ユーザー入力を次の順で判定する。Agent 種別と既存 Agent 名・ID を混同しない。

| 入力 | 解決方法 | 作業ディレクトリ |
| --- | --- | --- |
| Codex、Claude Code、OpenCode など Agent 種別 | 指定種別を同一 tab へ新規起動する | 実装 cwd で起動する |
| 既存 Agent 名または ID | `herdr agent get <target>` で解決し、`idle` の場合だけ再利用する | cwd は変えず、タスクに実装 cwd の絶対パスを書く |
| 指定なし | 現在動作しているエージェントと同じ種別を同一 tab へ新規起動する | 実装 cwd で起動する |

指定された既存 Agent が存在しない、自分自身である、または `idle` でない場合は失敗とする。別 Agent の起動、別の Agent 種別への切り替え、自動再試行はしない。新規 Agent は `herdr-agent-delegate` の4pane単位の固定配置と起動確認に従い、その pane ID を親が管理する。

新規起動するレビュー担当 Agent には `herdr agent rename` で役割と対象 PR を示すセッション名 `review-pr-<number>` を設定する。既存 Agent の再利用時は名前を変更しない。

新規 Agent 用の pane は `herdr-agent-delegate/scripts/split_scoped_pane.py` で作り、新規pane作成後の `workspace_id`・`tab_id` を検証する。その後は同スキルのreadiness契約に従い、Agent起動、semantic検出、Agent別input-ready確認、依頼の直接送信、working遷移確認を別工程で行う。input-readyを確認できなければ何も送信せずpaneを保持する。識別子の欠落・型不正・不一致時にcloseできるのは今回作成した未起動paneだけである。明示指定された既存 Agent の再利用は分割検証と新規起動用readiness待機の対象外とする。

## 3. 初回レビューを同期委譲する

レビュータスクに次を含める。

```text
- 対象 PR URL
- 対象作業ディレクトリの絶対パス
- $github-pr-review を使うこと
- GitHub へレビューコメントを投稿すること
- 各指摘の重要度、要約、コメント URL または ID を返すこと
- Herdr の Completion contract に従って結果を確定すること
```

依頼を直接送って処理開始を確認し、完了まで待つ。`blocked` とtimeoutは成功扱いしない。成功時だけ `herdr pane read --source recent-unwrapped` で結果を回収する。指摘がなく、この結果がレビュー工程の最終結果になる場合は、新規起動したレビュー Agent を結果回収後に閉じる。

## 4. 親が指摘を分類する

回収結果と GitHub 上の投稿を確認し、各指摘を分類する。

- `対応可能`: `[must]`、`[should]`、`[nit]` のうち、ユーザー確認なしで独立して対応できる。
- `ユーザー判断が必要`: `[ask]`、`[imo]`、または仕様・意図の決定が必要である。
- `対応不能／対象外`: 現在の権限・環境では対応不能、根拠が現行コードに該当しない、または Issue / PR の範囲外である。

確認不要な指摘と判断待ちが混在する場合、依存しない `対応可能` を先に処理する。対応可能な指摘がなく判断待ちだけなら、必要な判断をユーザーへ確認して待機する。

ユーザー回答後は、回答を対象コメントごとの決定内容として記録し、その内容に基づいて各指摘を再分類する。`対応可能` へ移った指摘は次の FB 対応対象に含め、引き続き判断が必要な指摘が残る場合は再び待機する。

## 5. 専用 Agent へ FB 対応を委譲する

同じ回の `対応可能` な指摘を、毎回新規起動する 1 体の専用 FB 対応 Agent へまとめる。同一ブランチへの並列変更は禁止する。Agent 種別はレビュー Agent と同じ種別を使い、実装 cwd で起動する。

新規起動する FB 対応 Agent には `herdr agent rename` で役割と対象 PR を示すセッション名 `fb-pr-<number>` を設定する。

FB 対応タスクに次を含める。

```text
- 対象 PR URL
- 対象作業ディレクトリの絶対パス
- 対象レビューコメント URL または ID の一覧
- ユーザー判断を経た対象は、対象コメントごとの決定内容
- 対象外コメントには対応しないこと
- $github-pr-feedback-address を使うこと
- 差分、検証、commit、push、返信の結果を返すこと
- Herdr の Completion contract に従って結果を確定すること
```

FB 対応 Agent も新規起動する。`herdr-agent-delegate/scripts/split_scoped_pane.py` と上記の新規起動readiness契約を適用する。分割またはinput-ready確認に失敗した場合は何も送信せずpaneを保持する。closeできるのは今回作成した未起動paneだけである。`question` または `blocked` が返った場合は自動対応を止める。正常完了時は `herdr pane read --source recent-unwrapped` で結果を回収し、親が子の報告だけでなく次を確認する。

- 意図した差分だけが含まれる。
- 必要な検証が成功している。
- コード変更がある場合、commit と PR ブランチへの push が完了している。
- 対象コメントへの返信が完了している。
- コード変更がない場合、その判断根拠と返信を確認できる。

確認成功後だけFB 対応 Agent のpaneを閉じて次へ進む。確認失敗時はpaneを保持して停止する。

## 6. 同じレビュー Agent へ再チェックを委譲する

初回レビューを行った同じ Agent へ、`github-pr-review` で元指摘だけを再チェックするよう依頼する。新しい論点を探す PR 全体レビューは依頼しない。各元指摘について `resolved`、`partial`、`unresolved`、`unknown` と、コメント URL または ID を返させる。

```text
- 対象 PR URL
- 対象作業ディレクトリの絶対パス
- 元指摘のコメント URL または ID の一覧
- $github-pr-review で元指摘だけを再チェックすること
- PR 全体の新しい論点を探さないこと
- 各指摘の判定と根拠を返すこと
- Herdr の Completion contract に従って結果を確定すること
```

同じpaneへ直接送信し、待機、回収する。失敗時はpaneを保持する。結果を回収してから次を判定し、レビュー工程が正常終了した時だけ新規起動したレビュー Agent を閉じる。

- 全件 `resolved` なら完了する。
- 確認不要な `partial` / `unresolved` は分類へ戻す。
- `unknown`、ユーザー判断が必要な残件、対応不能な残件は停止して報告する。
- FB 対応は最大 3 回とする。
- 同一指摘が 2 回連続で `partial` または `unresolved` なら、3 回未満でも停止する。

各回の分類、対象コメント、試行回数、再チェック結果を保持する。

## 7. pane と失敗状態を管理する

- 親が新規起動した FB 対応 Agent は、正常完了、結果回収、親の成果確認後に閉じる。
- 親が新規起動したレビュー Agent は、初回レビューに指摘がある間は閉じず、指摘なし、最終再チェック完了、またはユーザーが残件へ対応しないと決めた後の結果回収時に閉じる。
- 明示指定により再利用した既存 Agent は閉じない。
- 失敗、`blocked`、`timeout`、ユーザー判断待ち、診断中の pane は保持する。

工程失敗時は自動再試行せず、PR URL、成功済み工程、失敗工程、Agent / pane、状態、経過、未解決指摘、次に必要な判断を報告する。
