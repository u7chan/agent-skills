---
name: herdr-prompt-eval-loop
description: Herdr上の独立した新規Agentで、スキル、コマンドプロンプト、タスクプロンプト、Agent向け指示をシナリオ実行し、非公開要件で採点して曖昧さと暗黙の裁量を1テーマずつ最小改善する。プロンプトの実行精度・安定性を実証評価したい時や、実行せず記述構造だけを確認したい時に使う。成果物の主観的品質評価やスキルのトリガー最適化には使わない。
---

# Herdr Prompt Eval Loop

対象プロンプトを独立Agentで反復実行し、親Agentだけが知る要件チェックリストで評価する。成果物の好みや表現品質を採点せず、指示の明確さと再現性だけを改善する。

最初に `references/evaluation-protocol.md` と `references/herdr-execution.md` を最後まで読む。Herdr操作前に `../herdr-worktree-create/SKILL.md`、`../herdr-agent-delegate/SKILL.md`、`../herdr-agent-delegate/references/agent-cli.md` を読む。worktreeの作成元解決、base解決、衝突確認、公式create、返却workspace検証は `herdr-worktree-create` を適用し、Agent起動、input-ready、直接送信、完了待機、出力回収は `herdr-agent-delegate` を適用する。本スキル固有の一時path、評価branch、シナリオごとの分離、新規Agent、cleanup規則を優先する。

## 1. 評価条件を固定する

1. 対象プロンプト、変更可能範囲、必要な参照ファイル、実行要否、実行用Gitリポジトリ、保存レポートの要否を解決する。記述だけの確認なら構造審査モードへ進む。
2. ユーザー指定のAgent種別を使い、未指定なら現在の親Agentと同じ種別を使う。評価開始後は種別を変更しない。
3. 最大イテレーションを開始前だけ変更可能とし、未指定なら6回に固定する。
4. 対象がskillなら、baseline前にfrontmatterのdescriptionと本文の対象範囲を照合する。用途の不足・過剰だけを最小修正し、責務変更が必要なら停止する。
5. 標準1件、エッジ1〜2件、未使用hold-out 1件を作り、開始時に固定する。各シナリオへ3〜7件の客観的チェック項目を作り、1件以上をcriticalにする。
6. シナリオ、チェックリスト、期待観測、採点基準を親だけに保持する。実行Agentへチェックリストや改善仮説を渡さない。

実行用Gitリポジトリはユーザー指定を優先し、未指定なら現在cwdから解決する。非Git管理の単体プロンプトも、実行用Gitリポジトリを解決できれば対象にする。独立実行に必要な条件を満たせなければ自己評価へ切り替えず、`empirical evaluation skipped: independent execution unavailable` と表示して終了する。

## 2. 構造だけを審査する

ユーザーが実行を求めず記述だけの確認を依頼した場合は、`references/evaluation-protocol.md`の構造審査モードを使う。descriptionと本文の整合、用語、矛盾、未定義条件、手順欠落、重複、評価不能な抽象表現だけを確認する。Herdr実行、シナリオ採点、改善イテレーション、hold-out、収束判定を行わず、実証評価の回数や連続クリア回数へ含めない。

## 3. baselineを実行する

各イテレーションで次を行う。

1. 対象プロンプトと必要な参照ファイルから、その回専用の読み取り専用スナップショットを作る。
2. 標準・エッジの各シナリオへ一意なbranch、別Herdr worktree、別workspaceを作る。
3. 各workspaceのroot paneへ、固定した種別の新規Agentを起動する。既存Agentを再利用せず、通常のpane splitを使わない。
4. チェックリストを伏せたタスクを全Agentへ先に送り、並列完了を待つ。
5. 出力とシナリオworktree内の成果物を親が直接検査し、チェック項目、不明瞭点、裁量補完、steps、duration、retriesを記録する。

実行のコマンド、JSON検証、snapshot、依頼内容、失敗保持、cleanupは `references/herdr-execution.md` に従う。採点と比較は `references/evaluation-protocol.md` に従う。

## 4. 1テーマだけ改善する

全baseline結果を横断し、新規不明瞭点または暗黙の裁量から影響が最大の1テーマを選ぶ。対象プロンプトだけを最小限修正し、要件チェックリストとシナリオは変えない。複数テーマを同時に直さない。

要件変更、責務変更、構成刷新が必要なら修正せず停止し、根拠とユーザー判断事項を示す。修正後は新しいスナップショット、新しいworktree、新しいworkspace、新しいAgentで次のイテレーションを行う。

## 5. 収束または停止を判定する

全baselineシナリオについて、critical完全達成、新規不明瞭点0、前回との精度差3ポイント以下、steps差±10%以内を満たす安定回を連続2回要求する。並列実行のdurationは記録だけに使う。

baseline収束後に初めてhold-outを1回実行する。全critical達成かつ精度が直近baseline平均より15ポイント以上低くなければ合格とする。hold-out結果を使って修正を続けない。

次の場合は停止する。

- 3回以上連続して不明瞭点が減らない。
- Herdrの起動、送信、待機、回収、JSON検証が失敗する。
- 副作用をシナリオworktree内へ隔離できない。
- blocked、timeout、Completion contract違反になる。
- 最大イテレーションへ到達する。
- 最小修正の範囲を超える。

## 6. 結果を確定する

正常に回収・採点したworkspaceだけを削除し、今回作成したbranchだけを確認して削除する。blocked、timeout、回収失敗、未採点のworkspace、pane、worktree、branchは診断用に保持する。既存資源を削除しない。

各イテレーションの採点後、変更点、シナリオ別の成功・accuracy・steps・duration・retries、新規不明瞭点、新規裁量補完、次の修正、連続クリア回数を提示する。通常は会話へ、ユーザー指定時だけMarkdownファイルへ次を報告する。

- 対象、固定Agent種別、シナリオ構成、実施回数
- 各回の改善テーマ、シナリオ別の成功・accuracy・critical・不明瞭点・裁量補完・steps・duration・retries、連続クリア回数
- baseline収束判定とhold-out結果
- 最終変更、停止理由、未解決事項、ユーザー判断事項
- 削除した資源と診断用に保持したworkspace、pane、worktree、branch

実行Agentの報告だけで成功を判断せず、HerdrのCompletion contract、回収出力、成果物、採点結果を親が確認して最終状態を確定する。
