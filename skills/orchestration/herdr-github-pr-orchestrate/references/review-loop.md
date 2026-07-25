# Herdr レビュー・FB対応・再チェック契約

PR作成成功後に読む。pane配置、Agent起動、送信、待機、出力回収は`herdr-agent-delegate`へ一元化し、ここではAgent選択、分類、反復上限、成果確認、cleanupだけを定める。

## PR Work Metadata スナップショット

レビューとレビューFBも、`implementation-delegation.md`のPR Work Metadata snapshot契約に従う。PR作成前に起動値へ固定済みの完全な3値だけを本文に使い、PR作成後に解決した値を過去のPR本文へ追加・更新しない。

## 1. レビュー担当を解決する

- Agent種別指定なら`cagent-agent-command-resolve`へ明示し、実効3値を固定した`agent-kind`・`native-agent-args`で実装cwdに新規起動する。
- 既存Agent名・ID指定なら`herdr agent get <target>`で解決し、idleの場合だけ再利用する。
- 指定なしなら現在の親Agentと同じ種別をcagentへ明示し、実装cwdで新規起動する。
- 存在しない、自分自身、非idleのAgentでは停止し、自動切替や再試行を行わない。
- 新規レビューAgentは`review-pr-<number>`へrenameする。既存Agent名は変更しない。

## 2. 初回レビューを委譲する

対象PR URL、実装cwd、`github-pr-review`の利用、GitHubへの投稿、重要度・要約・コメントURLまたはIDの返却を依頼する。新規paneの起動時snapshotが完全な場合だけ`build_prompt.py --metadata-json`で標準suffixを付与する。委譲操作は`herdr-agent-delegate`へ任せる。指摘がなく結果確認まで成功した場合だけ、新規レビューpaneを閉じる。

## 3. 親が指摘を分類する

- `対応可能`: `[must]`、`[should]`、`[nit]`のうち確認なしで対応できる。
- `ユーザー判断が必要`: `[ask]`、`[imo]`、仕様・意図の決定が必要。
- `対応不能／対象外`: 権限・環境不足、現行コードに該当しない、Issue/PR範囲外。

独立した対応可能項目を先に処理し、判断待ちだけなら停止してユーザーへ確認する。回答後はコメント単位の決定として再分類する。

## 4. FB対応を直列委譲する

初回FBラウンドでは、同じ回の対応可能項目を新規のFB対応Agent 1体へまとめる。同一branchへの並列変更を禁止する。Agent種別はレビュー担当と同じ値をcagentへ明示し、実効3値を新たに固定して`fb-pr-<number>-r1`へrenameする。

再チェックで確認不要な`partial` / `unresolved`が返った場合、親は前回のFB Agent・pane・sessionを再利用せず、次ラウンド専用の新規Agentを別paneへ起動する。ユーザーが次FB担当のAgentまたはtask levelを明示した場合はその値を優先し、未指定なら`agent=opencode`、task level=`mid`をcagentへ明示する。ModelとEffortは推測せずcagentで解決し、ラウンドごとに新しい`agent-kind`・`native-agent-args`・snapshotを固定して`fb-pr-<number>-r<round>`へrenameする。これは失敗時の自動再試行やAgent切替ではなく、再チェックで確認した対応可能な残件に対する規定の次FBラウンドである。

対象PR、実装cwd、対象コメント、ユーザー決定、`github-pr-feedback-address`の利用、差分・検証・commit・push・返信結果の返却を依頼する。FB担当は新たに解決した自身のsnapshotだけを受け取り、レビュー担当や親の値を転用しない。`question`、`blocked`、timeoutでは停止する。

親は回収後に次を確認する。

- 意図した差分だけが含まれ、必要な検証が成功した。
- コード変更があれば限定stage、commit、pushが完了した。
- 対象コメントへの返信、または変更不要の根拠と返信を確認できた。

確認成功後だけ新規FB paneを閉じる。確認失敗時は保持して停止する。

## 5. 同じレビュー担当で再チェックする

初回レビューと同じAgentへ、初回起動時の同じsnapshotを再送し、元指摘だけを`github-pr-review`で再チェックさせる。出自不明の再利用paneならメタ情報を送らない。PR全体の新論点は探させない。各指摘を`resolved`、`partial`、`unresolved`、`unknown`で返させる。

- 全件`resolved`なら完了する。
- 確認不要な`partial` / `unresolved`は分類へ戻し、前節の別FB Agentによる次ラウンドへ進む。
- `unknown`、判断待ち、対応不能は停止する。
- FB対応は最大3回とする。
- 同一指摘が2回連続で`partial`または`unresolved`なら停止する。

## 6. cleanupと停止報告

- 新規FB paneは正常完了・回収・親確認後だけ閉じる。
- 新規レビューpaneは指摘なし、最終再チェック完了、またはユーザーが残件へ対応しないと決めた後だけ閉じる。
- 再利用pane、失敗、blocked、timeout、判断待ち、診断中のpaneは保持する。

工程失敗をPR作成失敗として扱わない。PR URL、成功済み工程、失敗工程、Agent/pane、各指摘の分類、試行回数、未解決事項、次に必要な判断を報告する。
