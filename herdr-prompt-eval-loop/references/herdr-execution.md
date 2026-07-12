# Herdr独立実行

## 1. プリフライトする

1. `HERDR_ENV=1`、空でない`HERDR_PANE_ID`、`herdr`、`jq`、固定したAgent CLIを確認する。自動インストールや別種別への切替をしない。
2. `herdr pane current --current`から親のAgent種別とIDを取得する。ユーザー指定がなければこの種別を固定する。
3. ユーザー指定の実行用Gitリポジトリ、または`git -C "$PWD" rev-parse --show-toplevel`の結果を使う。単体プロンプトがGit管理外でも、worktreeの基点にするリポジトリは必要とする。
4. リポジトリ、対象ファイル、参照ファイルの絶対パスと開始時OIDを記録する。既存のbranch、worktree、workspace、tab、paneを一覧化し、今回の資源と区別する。
5. 実行が外部送信、課金、公開、削除、認証変更などworktree外の副作用を起こし得る場合は、シナリオ用の安全な代替へ隔離する。隔離できなければ停止する。

いずれかを満たせず独立Agentを起動できない場合は、自己評価や現在Agent内の模擬実行を行わず、`empirical evaluation skipped: independent execution unavailable`と表示する。

## 2. snapshotを作る

実行ごとに`/tmp`配下へ推測困難で一意なrun directoryを作り、イテレーション単位の`iteration-N/snapshot`を置く。対象プロンプトと必要な参照ファイルだけを元の相対構造を保ってコピーし、通常ファイルを`0444`、directoryを`0555`にする。秘密、チェックリスト、hold-out、前回出力、改善仮説を含めない。

全baselineシナリオへ同じsnapshotの絶対パスを渡す。実行Agentにはsnapshotを変更せず、成果物を自分のシナリオworktree内だけへ書くよう指示する。親は実行後にsnapshotのハッシュと権限を開始時記録と照合する。不一致なら隔離失敗として保持・停止する。

対象プロンプトの修正は親の作業ツリーだけで行う。次回snapshotは修正後の対象から新規作成し、既存snapshotを上書きしない。

## 3. シナリオworktreeを作る

run ID、iteration、scenario slugを含む安全な`/tmp`配下のpathと、一意な`eval/<run-id>-i<N>-<slug>` branchを割り当てる。作成前にpath、branchが存在しないことを確認し、作成対象として台帳へ記録する。

各baselineシナリオについて次を直接実行する。ラッパーを追加しない。複数コマンドを先に起動して並列化してよいが、各JSONを個別に保存・検証する。

```bash
herdr worktree create \
  --path <absolute-scenario-path> \
  --branch <unique-eval-branch> \
  --no-focus \
  --json \
  --cwd <absolute-execution-repository>
```

`--cwd`で実行用Gitリポジトリを作成元に固定し、別workspaceのfocusに依存させない。返却JSONの`result.workspace`、`result.tab`、`result.root_pane`を取得する。各objectのID、cwd、相互のworkspace/tab対応が欠ける、型が違う、指定pathと一致しない場合はAgentを起動せず、その資源を保持して停止する。IDを順番や名前から推測しない。

各シナリオは別workspaceかつ別worktreeであることを全件相互確認する。通常の`pane split`は使わない。

## 4. root paneで新規Agentを実行する

各`root_pane`へ固定種別のCLIを`herdr pane run <pane-id> '<agent-command>'`で起動する。シナリオごと・イテレーションごと・hold-outで必ず新規Agentを使い、既存Agentや前回Agentを再利用しない。

起動後は`../herdr-agent-delegate/SKILL.md`の契約どおり、agent-status検出、Agent別input-ready、直接送信、working遷移を別々に確認する。依頼は同スキルの`scripts/send_request.py`で送る。全シナリオへ送信してから個別にCompletion contractで待ち、`recent-unwrapped`出力を回収する。

依頼には次だけを含める。

```text
- 実際の利用者として遂行するシナリオ本文と入力
- 読み取り専用snapshotの絶対パスと入口ファイル
- 成果物を現在のシナリオworktree内だけへ生成すること
- snapshot、Git履歴、worktree外、外部状態を変更しないこと
- 別Agentへ委譲しないこと
- 実施内容、成果物path、実行コマンド、検証、未解決事項を返すこと
- HerdrのCompletion contractに従って結果を確定すること
```

評価、チェックリスト、critical、期待解、採点式、改善テーマ、他シナリオの情報を含めない。対象がスキルでも、自動トリガーの成否ではなく明示的に対象を使わせて実行内容を評価する。

## 5. 回収して親が検査する

Completion contractで最終状態が`idle`または`done`と確認でき、pane出力を回収できた時だけ成果物検査へ進む。親は各worktreeで次を直接確認する。

- 成果物が指定worktree内だけにある。
- GitのHEAD、追跡差分、未追跡ファイル、外部状態が許容範囲内である。
- snapshotのハッシュと権限が変わっていない。
- 実行Agentの報告と実ファイル・コマンド結果が一致する。
- 非公開チェック項目を証拠付きで採点できる。

durationはworking確認時刻から最終状態確認時刻までを記録する。stepsは回収出力と成果物から評価プロトコルの定義で数える。正常に回収しても採点不能なら成功扱いにしない。

## 6. 成功資源だけcleanupする

正常回収、成果物検査、採点をすべて終えたシナリオだけ次を直接実行する。

```bash
herdr worktree remove --workspace <created-workspace-id> --force --json
```

返却JSONを確認し、対象workspaceとworktreeがなくなったことを読み取り確認する。その後、作成前に不存在を確認し台帳へ記録した今回のbranchだけを、実行用Gitリポジトリで削除する。branch名と対象OIDを再確認し、他branchを削除しない。snapshotは対応する全シナリオのcleanup成功後だけ削除する。

blocked、timeout、送信失敗、回収失敗、Completion contract違反、snapshot不一致、副作用、採点不能、cleanup失敗のworkspace、pane、worktree、branch、snapshotは診断用に保持する。成功した別シナリオの資源は個別にcleanupしてよい。既存資源と今回作成していない資源は操作しない。

## 7. 実行台帳を報告する

各資源についてrun ID、iteration、scenario、workspace ID、tab ID、pane ID、worktree path、branch、作成結果、回収状態、採点状態、cleanup結果を記録する。保持した資源は絶対pathとID、保持理由、次に必要な操作を報告する。
