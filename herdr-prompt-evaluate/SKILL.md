---
name: herdr-prompt-evaluate
description: Herdr上の独立した新規Agentで、スキル、コマンドプロンプト、タスクプロンプト、Agent向け指示をシナリオ実行し、非公開要件で採点して曖昧さと暗黙の裁量を1テーマずつ最小改善するときに使う。Herdrを使わない構造審査、成果物の主観評価、Skillの構造設計や意味保存refineには使わない。
---

# Herdr Prompt Evaluate

対象プロンプトを独立Agentで反復実行し、親Agentだけが知る要件チェックリストで評価する。成果物の好みや表現品質を採点せず、指示の明確さと再現性だけを改善する。

最初に`references/evaluation-protocol.md`と`references/herdr-execution.md`を最後まで読む。Herdr操作前に`../herdr-worktree-create/SKILL.md`、`../herdr-agent-delegate/SKILL.md`、`../herdr-agent-delegate/references/agent-cli.md`を読む。worktree作成は`herdr-worktree-create`、Agent起動・送信・待機・回収は`herdr-agent-delegate`へ委ね、本Skill固有の隔離、評価、最小改善、cleanup規則だけを追加する。

## 責務境界

- Herdrを使わない記述構造だけの審査は行わない。
- Agent Skillの新規設計、責務・起動条件・構成の変更は`agent-skill-design`へ引き渡す。
- 期待する判断・行動・成果物を変えない意味保存refineは`agent-skill-refine`へ引き渡す。
- 本Skillは独立Agentによる実証結果から観測した1テーマの最小改善だけを行う。

## 1. 評価条件を固定する

1. 対象プロンプト、変更可能範囲、必要な参照ファイル、実行用Gitリポジトリ、保存レポートの要否を解決する。
2. ユーザー指定のAgent種別を使い、未指定なら現在の親Agentと同じ種別を使う。評価開始後は変更しない。
3. 最大イテレーションを開始前だけ変更可能とし、未指定なら6回に固定する。
4. 対象がSkillなら、baseline前にfrontmatterのdescriptionと本文の対象範囲を照合する。用途の表現だけで直せない場合は設計変更として停止する。
5. 標準1件、エッジ1〜2件、未使用hold-out 1件を作り、開始時に固定する。各シナリオへ3〜7件の客観的チェック項目を作り、1件以上をcriticalにする。
6. シナリオ、チェックリスト、期待観測、採点基準を親だけに保持し、実行Agentへ渡さない。

実行用Gitリポジトリはユーザー指定を優先し、未指定なら現在cwdから解決する。独立実行に必要な条件を満たせなければ自己評価や構造審査へ切り替えず、`empirical evaluation skipped: independent execution unavailable`と表示して終了する。

## 2. baselineを実行する

各イテレーションで次を行う。

1. 対象プロンプトと必要な参照ファイルから、その回専用の読み取り専用snapshotを作る。
2. 標準・エッジの各シナリオへ一意なbranch、別Herdr worktree、別workspaceを作る。
3. 各workspaceへ固定した種別の新規Agentを起動し、チェックリストを伏せたタスクを全Agentへ送る。
4. 出力と成果物を親が直接検査し、チェック項目、不明瞭点、裁量補完、steps、duration、retriesを記録する。

実行、JSON検証、snapshot、失敗保持、cleanupは`references/herdr-execution.md`、採点と比較は`references/evaluation-protocol.md`に従う。

## 3. 1テーマだけ改善する

全baseline結果を横断し、新規不明瞭点または暗黙の裁量から影響が最大の1テーマを選ぶ。対象プロンプトだけを最小限修正し、要件チェックリストとシナリオは変えない。

要件変更、責務変更、構成刷新が必要なら修正せず停止する。修正後は新しいsnapshot、worktree、workspace、Agentで次のイテレーションを行う。

## 4. 収束または停止を判定する

全baselineシナリオについて、critical完全達成、新規不明瞭点0、前回との精度差3ポイント以下、steps差±10%以内を満たす安定回を連続2回要求する。baseline収束後にhold-outを1回だけ実行し、全critical達成かつ精度が直近baseline平均より15ポイント以上低くなければ合格とする。

次の場合は停止する。

- 3回以上連続して不明瞭点が減らない。
- Herdrの起動、送信、待機、回収、JSON検証が失敗する。
- 副作用をシナリオworktree内へ隔離できない。
- blocked、timeout、`herdr agent wait`違反になる。
- 最大イテレーションへ到達する。
- 最小修正の範囲を超える。

## 5. 結果を確定する

正常に回収・採点したworkspaceと今回作成したbranchだけを確認して削除する。失敗・未採点資源は診断用に保持する。各回の変更テーマ、採点、critical、不明瞭点、裁量補完、steps、duration、retries、収束・hold-out、最終変更、停止理由、保持資源を報告する。

実行Agentの報告だけで成功を判断せず、`herdr agent wait`の結果、回収出力、成果物、採点結果を親が確認して`converged`、`stopped`、`skipped`を確定する。
