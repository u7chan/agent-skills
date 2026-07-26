# agent-skills の発展と複雑化、そして移行

この文書は、個人用の小さなスキル集として始まったこのリポジトリが、単一Agentによる一貫自動化、複数Agentのオーケストレーション、厳密なガバナンスへ進み、最終的に必要最小限の構成へ移行するまでの記録です。勉強会やテックブログで再利用できるよう、出来事だけでなく、どこで費用対効果が変わったのかも残します。

対象期間は、最初の commit が作られた 2026年1月19日から、[global-agent-skills への移行を明記した PR #246](https://github.com/u7chan/old-agent-skills/pull/246) が merge された 2026年7月26日までです。

## この文書の読み方

この記録では、性質の異なる情報を分けて扱います。

- **履歴で確認できる事実**: Git の commit、GitHub の Issue / PR、当時のファイルから確認できるもの
- **運用者の回顧**: 日々使った本人の記憶。トークン消費量や認知負荷など、リポジトリだけでは観測できないもの
- **現在からの解釈**: 事実と回顧を並べた上での振り返り。唯一の因果説明ではない

以下の日付は、特記がない限り Git 履歴上の merge 日を基準にしています。

## ひとことで振り返る

```text
個人用の単機能スキル
  → 1体のAgentでIssueからPRまで完走
  → tmux / Herdrで複数Agentへ実装・レビューを委譲
  → 依存関係、契約、inventory、検証、CIで複雑さを統制
  → 統制機構自体の保守費と実行コストが便益を上回り、最小構成へ移行
```

このリポジトリは、機能を失って自然に衰退したわけではありません。自動化できる範囲は最後まで増えました。その一方で、安全かつ再現可能に動かすためのスキル、規則、検証、Agent間契約も増え続け、個人用ツールとしては全体を把握し、変更し、実行するコストが高くなりました。ここでいう「衰退」は、機能不足ではなく、保守可能性と費用対効果の低下です。

## 時系列

### 1. 小さな個人用スキル集（2026年1月〜2月）

最初は、文字列反転、Git のブランチ名・commit message 提案、ロールプレイなどを置く小さな実験場でした。[PR #1](https://github.com/u7chan/old-agent-skills/pull/1)、[PR #2](https://github.com/u7chan/old-agent-skills/pull/2)、[PR #3](https://github.com/u7chan/old-agent-skills/pull/3) に、その出発点が残っています。

[PR #11「feat: add comprehensive README documentation」](https://github.com/u7chan/old-agent-skills/pull/11) の時点でも、README に載っていた中心機能は commit message 関連の2スキルでした。セットアップも Claude Code のグローバルな skills ディレクトリから symlink する素朴なもので、個人用グローバルスキル管理という目的に対して構成は小さく、全体を目で追えました。

2月末には branch、commit、PR 本文・PR 作成を分割したスキルが揃い始めました。context 用と diff 用の派生を作った直後に統合し直した [PR #29](https://github.com/u7chan/old-agent-skills/pull/29)、[PR #30](https://github.com/u7chan/old-agent-skills/pull/30)、[PR #33](https://github.com/u7chan/old-agent-skills/pull/33) は、早い段階から責務の粒度を試行錯誤していたことを示しています。ただし、まだ各スキルは単機能で、呼び出す側が組み合わせを判断できる規模でした。

### 2. Claude Code / Codex 両対応とプリミティブの充実（2026年3月〜4月）

[PR #41「docs: add Codex skill setup instructions」](https://github.com/u7chan/old-agent-skills/pull/41) と [PR #46「feat: add claude-to-codex skills link skill」](https://github.com/u7chan/old-agent-skills/pull/46) により、Claude Code と Codex の両方から同じスキル群を使う形が整いました。

この時期は、Issue 作成、依存パッケージ更新、ブラウザ確認、PR コメント返信など、用途ごとのプリミティブを増やしながら、命名変更や重複統合を繰り返していました。[PR #57「Refactor skill naming conventions」](https://github.com/u7chan/old-agent-skills/pull/57) や [PR #77「refactor(github-pr-create): consolidate PR creation skills」](https://github.com/u7chan/old-agent-skills/pull/77) が代表例です。

運用者の回顧では、ここまではスキル数が増えても、Claude Code / Codex 両対応を含めて大きな問題はありませんでした。各スキルの入力、処理、出力が比較的局所的だったためです。

### 3. 単一Agentの一貫オーケストレーション（2026年5月）

大きな転換点は、[PR #83「Add github-implement-pr skill」](https://github.com/u7chan/old-agent-skills/pull/83) です。当時の `github-implement-pr` は、Issue の読み取り、branch 作成、実装、検証、commit、push、PR 作成までを1体のAgentが止まらずに進めるスキルでした。初版は他スキルへ委譲せず、1つの長いワークフローの中で完結する設計でした。

これは明確な価値を生みました。「Issue を渡せば PR まで進む」という高い操作性を、単一Agentのセッション内で実現したためです。一方で、Git、GitHub、実装、検証、失敗時の停止条件を1つの入口から扱うようになり、スキルは単なる手順書からワークフローエンジンに近づき始めました。

[PR #84「Add PR feedback address skill」](https://github.com/u7chan/old-agent-skills/pull/84) ではレビュー指摘対応が加わりました。さらに [Issue #114「SKILL.mdを原則180行以内に整理しCIで検証する」](https://github.com/u7chan/old-agent-skills/issues/114) と [PR #115「SKILL.mdを整理し検証CIを追加する」](https://github.com/u7chan/old-agent-skills/pull/115) により、スキル検証の CI が導入されました。自動化の対象だけでなく、自動化を壊さず保守する仕組みも必要になった時期です。

### 4. tmux による複数Agent化（2026年6月29日〜7月2日）

6月末、[PR #132「feat: add tmux Codex split skill」](https://github.com/u7chan/old-agent-skills/pull/132) を起点に、OpenCode / Claude の pane 起動、非同期 PR レビュー、Agent間メッセージングが短期間に追加されました。[PR #133「Add tmux split skills for OpenCode and Claude Code」](https://github.com/u7chan/old-agent-skills/pull/133)、[PR #134「feat: add asynchronous PR review handoff」](https://github.com/u7chan/old-agent-skills/pull/134)、[PR #137「feat: add tmux agent payload messaging」](https://github.com/u7chan/old-agent-skills/pull/137) です。#137 では JSON の通信形式、schema、timeout、trace、単体・tmux 結合テストまで導入されました。

しかし tmux 固有スキルは、わずか数日後の [PR #142「chore: archive tmux skills」](https://github.com/u7chan/old-agent-skills/pull/142) で archive されました。そして [Issue #143「herdrで複数Agentへの委譲を統合するスキルを追加する」](https://github.com/u7chan/old-agent-skills/issues/143) と [PR #144「feat: add Herdr agent delegation skill」](https://github.com/u7chan/old-agent-skills/pull/144) により、Herdr ベースへ置き換わりました。

ここで扱う状態は、一気に増えました。親子Agent、pane、tab、workspace、worktree、依頼送信、完了待機、出力回収、失敗時の資源保持などです。単一Agentの中だけで成立していた手順に、ターミナルマルチプレクサをまたぐ分散実行の契約が加わりました。

### 5. Herdr による実装・レビュー・FB ループ（2026年7月）

Herdr 導入の翌日には、[PR #148「feat: github-implement-pr に Herdr レビューループを追加」](https://github.com/u7chan/old-agent-skills/pull/148) と [PR #149「feat: github-implement-pr の実装工程を Herdr Agent へ委譲」](https://github.com/u7chan/old-agent-skills/pull/149) が入りました。その後 [PR #151](https://github.com/u7chan/old-agent-skills/pull/151) でスキル名にも Herdr が明示されました。

到達したワークフローは強力でした。親Agentが Issue と作業領域を解決し、実装を子Agentへ委譲し、PR を作成し、別Agentにレビューさせ、対応可能な指摘をさらに別Agentへ渡し、再チェックを繰り返せます。従来の単一Agent用スキルも下位工程として読み込まれました。

同時に、Herdr 周辺では pane 配置、入力 readiness、session 名、task exchange、timeout、長文 prompt などの修正が連続しました。[PR #153](https://github.com/u7chan/old-agent-skills/pull/153)、[PR #155](https://github.com/u7chan/old-agent-skills/pull/155)、[PR #157](https://github.com/u7chan/old-agent-skills/pull/157)、[PR #159](https://github.com/u7chan/old-agent-skills/pull/159)、[PR #165](https://github.com/u7chan/old-agent-skills/pull/165)、[PR #166](https://github.com/u7chan/old-agent-skills/pull/166)、[PR #168](https://github.com/u7chan/old-agent-skills/pull/168)、[PR #171](https://github.com/u7chan/old-agent-skills/pull/171)、[PR #173](https://github.com/u7chan/old-agent-skills/pull/173)、[PR #175](https://github.com/u7chan/old-agent-skills/pull/175)、[PR #179](https://github.com/u7chan/old-agent-skills/pull/179)、[PR #180](https://github.com/u7chan/old-agent-skills/pull/180) に、その安定化過程が残っています。

[PR #177](https://github.com/u7chan/old-agent-skills/pull/177) では、独立Agentを反復起動して prompt を実証評価する仕組みまで加わりました。自動化の対象が開発作業だけでなく、「Agent向け指示が再現可能に動くか」の評価へ広がった段階です。

### 6. Agent / Model / Effort の記録をめぐる修正（2026年6月〜7月）

PR 本文やレビューコメントへ、作業した Agent と Model を残す試みは [PR #59](https://github.com/u7chan/old-agent-skills/pull/59)、[PR #113](https://github.com/u7chan/old-agent-skills/pull/113)、[PR #129](https://github.com/u7chan/old-agent-skills/pull/129)、[PR #130](https://github.com/u7chan/old-agent-skills/pull/130) と段階的に進みました。Herdr 導入後は [PR #184](https://github.com/u7chan/old-agent-skills/pull/184) で PR の AI work metadata を追加し、[PR #188](https://github.com/u7chan/old-agent-skills/pull/188)、[PR #192](https://github.com/u7chan/old-agent-skills/pull/192)、[PR #201](https://github.com/u7chan/old-agent-skills/pull/201)、[PR #207](https://github.com/u7chan/old-agent-skills/pull/207) で取得元、優先順位、Effort、委譲先への伝播が修正されました。

履歴から確認できるのは、「実行時の Agent / Model / Effort を正しく表示する」という横断的な関心に対し、短期間に複数の修正が必要だったことです。「だんだん期待どおり動かなくなった」という評価は運用者の回顧ですが、表示値の出所が親Agent、子Agent、設定、runtime と複数にまたがり、契約が不安定になりやすかったことは変更の連続から読み取れます。

### 7. 複雑さを統制するための inventory・規則・検証（2026年7月19日〜24日）

7月後半には、責務分離後に短い「PRを作って」という依頼を完走できなくなった回帰を扱う [Issue #208「[github-pr-orchestrate] 未コミット変更からPR作成まで統括する」](https://github.com/u7chan/old-agent-skills/issues/208) が作られました。その対応である [PR #209「feat: add GitHub PR orchestration skills」](https://github.com/u7chan/old-agent-skills/pull/209) は、Herdr を使わない直接統括と Herdr 統括を分離しました。利用コンテキストごとに入口を分ける合理的な設計でしたが、共通の下位スキルを含む複数のオーケストレーション経路を維持することにもなりました。

続いて、[Issue #206「[Epic] スキル構成の大規模な棚卸しと再編」](https://github.com/u7chan/old-agent-skills/issues/206) の下で、次の整備が行われました。Issue 本文は、責務の重複、依存関係の複雑化、SKILL.md の肥大化、外部依存の把握困難を再編理由として明示しています。

- [PR #223「feat: add skill inventory scripts and data for Phase 1 (#214)」](https://github.com/u7chan/old-agent-skills/pull/223): skill inventory と依存関係データを追加
- [PR #224「Phase 2: スキル構成・依存ルールの確定」](https://github.com/u7chan/old-agent-skills/pull/224): カテゴリ、依存方向、責務、命名などの正本を定義
- [PR #226「feat(validation): add skill validation framework with 35 rule checks」](https://github.com/u7chan/old-agent-skills/pull/226): 35ルールの検証フレームワークを追加
- [PR #240「[Epic] スキル構成の棚卸し・再編・カテゴリ再配置」](https://github.com/u7chan/old-agent-skills/pull/240): カテゴリ別ディレクトリへの再配置とセットアップ処理を実施
- [PR #242「refactor: remove external dependency type annotations (R/C/O/F)」](https://github.com/u7chan/old-agent-skills/pull/242): 追加した外部依存種別をすぐに簡素化

これらは、既に存在する複雑さを可視化し、安全に整理するための対策でした。Phase 1 の初回棚卸しでは、34スキルに対して循環依存2件、逆方向依存の候補16件、物理パス参照22件が記録されています。ただし、対策によって `.rules/`、`inventory/`、生成スクリプト、検証コード、fixture、CI という新たな保守対象も生まれました。機能変更だけでなく、正本、生成物、README、依存グラフ、テストの同期が必要になり、整理のための仕組み自体が認知負荷へ加わりました。

### 8. 最小構成への移行（2026年7月25日〜26日）

[Issue #244「Herdrオーケストレーションスキルを別リポに切り出す」](https://github.com/u7chan/old-agent-skills/issues/244) では、「何でもこのリポジトリで管理すべきではない」という判断と、Herdr 関連をより小さな単位へ切り出す方針が記録されました。翌日の [PR #246「docs: global-agent-skillsへの移行経緯を記録する」](https://github.com/u7chan/old-agent-skills/pull/246) で、このリポジトリをメンテナンス対象から外し、新しい [global-agent-skills](https://github.com/u7chan/global-agent-skills) へ移行する方針が README に明記されました。README が移行先設計の正本として参照しているのは、[global-agent-skills Issue #8「[Epic] AI向けGitHub操作基盤 gh を構築する」](https://github.com/u7chan/global-agent-skills/issues/8) です。

運用者が新リポジトリで残そうとしている公開入口は、概ね次の3つです。

- `gh`: GitHub CLI の低レベル操作を集約するラッパー
- `herdr`: Agent オーケストレーションの低レベル操作を集約するラッパー
- `grilling`: 設計や意思決定を一問ずつ詰める対話スキル

狙いは、機能をすべて捨てることではありません。Agent が最初に読む description と公開スキル数を減らし、共通処理を CLI ラッパーへ寄せ、モデルが読み込むスキル同士の結合を減らすことです。

## 何が費用対効果を変えたのか

### 局所的には、どの追加も合理的だった

以下は、履歴と運用者の回顧をつないだ現在からの解釈です。各段階の追加には、それぞれ明確な理由がありました。

- PR 作成を自動化すると、その後のレビューも自動化したくなる
- レビューを別Agentにすると、pane、送信、待機、回収の共通化が必要になる
- 複数Agentを安全に動かすと、worktree、状態、timeout、失敗時資源の契約が必要になる
- 実行結果を追跡すると、Agent / Model / Effort の正確な記録が必要になる
- 密結合を整理すると、カテゴリ、依存方向、inventory、検証が必要になる

1つずつを見ると、前段階で実際に起きた問題への対策です。問題は、それらが積み重なったときの全体コストが、個別 PR のレビュー単位では見えにくかったことでした。

### オーケストレーションは、読み込みと状態の組み合わせを増やした

単一のプリミティブスキルでは、主に「入力、コマンド、出力」を考えれば済みます。Herdr 統括では、親Agentと複数の子Agent、GitHub、Git、pane、workspace、worktree、Agent CLI、モデル解決、レビュー状態が相互作用します。

現在の正本では、`herdr-github-pr-orchestrate` は branch、commit、PR 作成、レビュー、FB 対応、Herdr 委譲、worktree の7スキルに依存します。再利用によって重複実装は減りますが、実行時には複数の `SKILL.md` と `references/` を読み、境界条件を同時に守る必要があります。コードの関数呼び出しに似た依存関係を自然言語 prompt で構成したため、ロードする文脈と解釈の揺れが実行コストになりました。

### 品質保証が、個人用ツールの規模を越えた

移行決定時点のスナップショットは次のとおりです。行数はコメントや fixture を含む単純集計であり、品質や複雑さを直接測る指標ではありません。

| 対象 | 規模 |
| --- | ---: |
| commit | 262（うち147、約56%が2026年7月） |
| Git 管理ファイル | 204 |
| スキル | 配布対象33 + リポジトリ保守専用1 |
| orchestration カテゴリ | 7スキル |
| 正本に記録されたスキル依存 | 19本 |
| `.rules/` の2ファイル | 1,398行 |
| `inventory/` の4 YAML | 1,416行 |
| inventory 生成・検証コード | 3,069行 |
| Python テスト | 18ファイル、2,094行 |
| orchestration 配下の Markdown / Python | 3,025行 |

これは「テストや規則を作るべきではなかった」という意味ではありません。むしろ、自然言語で書かれた分散ワークフローを安定させようとすれば、契約テストや静的検証が必要になることを示しています。問題は、個人用スキル集の価値を得るために、専用フレームワークに近い保守を必要とする状態へ達したことです。

### トークンと Usage は、リポジトリの外側にある主要コストだった

Git 履歴だけから、実際のトークン数や Codex Usage は復元できません。以下は運用者の回顧です。

- 終盤のフローは Issue から実装、PR、レビュー、FB 対応、再チェックまで自動化できた
- その代わり、親子Agentが複数スキルと GitHub 情報を読み、成果を受け渡すため、トークン消費が大きくなった
- 複数タスクを並列実行すると、1日で Codex の Usage を使い切るほど費用対効果が悪化した
- 公開スキルの description が増えただけでも、毎セッションの初期ロードコストになった

このコストは CI のようにリポジトリ上へ自動記録されていませんでした。そのため、機能の増加は追跡できても、1タスクあたりのトークン、Agent起動数、待ち時間、成功までの再試行数は設計判断へ戻しにくい状態でした。

なお、[Issue #34「skillsのdescription英語化によるトークン使用量削減の検証」](https://github.com/u7chan/old-agent-skills/issues/34) のコメントには、LiteLLM Proxy を使った特定条件の測定で、日本語の description が英語より約105 prompt tokens 多かったという記録があります。一般化できる数値ではありませんが、description のロードコストを早い段階から意識していた例です。

## 得られた教訓

### 1. 自動化できる範囲と、持続可能な範囲は違う

Issue からレビュー FB ループまで自動化できたこと自体は成果です。ただし、「できる」ことと「毎日使って得をする」ことは別でした。自動化率だけでなく、1タスクのトークン、時間、失敗時の復旧負荷を含めて評価する必要があります。

### 2. 自然言語の依存関係にも API 設計が要る

スキル間参照が増えると、名前、責務、入力、出力、失敗状態、再試行、cleanup が API になります。契約が曖昧なら Agent が補完し、厳密にすれば指示と検証が増えます。公開する入口を少なくし、低レベルの定型処理を CLI へ寄せる方が、モデルへ渡す契約を小さくできます。

### 3. 「整理する仕組み」の予算を先に決める

カテゴリ、inventory、依存グラフ、検証ルールは複雑さの可視化に役立ちました。一方で、それぞれが同期対象です。機能コードだけでなく、ガバナンスコードの行数、変更頻度、修正時間にも上限や廃止条件を置くべきでした。

### 4. モデル実行時情報は、表示より先に出所を一意にする

Agent / Model / Effort の表示は便利ですが、親と子、設定値と実行値がある環境では、どの時点の値を正本にするかが先です。表示テンプレートから始めると、取得規則と伝播規則が後追いになり、横断修正が増えます。

### 5. 並列化は速度だけでなく、消費量も並列化する

複数Agentは待ち時間を短縮できますが、同じ背景説明、スキル読み込み、GitHub 情報取得、検証を複製します。並列数ではなく、「独立性が高く、受け渡しが小さい仕事だけを並列化する」という基準が必要です。

### 6. 移行は敗北ではなく、抽象化の置き場所を変える判断である

旧リポジトリで得た知見があるからこそ、新リポジトリでは `gh` と `herdr` のような薄いラッパーへ共通処理を寄せ、公開スキルを絞れます。このリポジトリは失敗作として消すより、どの抽象化が自然言語スキルに向き、どれが CLI に向くかを示す実験記録として残す価値があります。

## 勉強会・テックブログに展開できる問い

- 「Issue から PR まで全自動」の本当の運用コストをどう測るか
- Agent Skill を関数のように合成すると、どこでマイクロサービス的な複雑さが生まれるか
- prompt の契約テストはどこまで有効で、いつ専用フレームワーク化するか
- マルチAgentは何を並列化すると得で、何を並列化すると文脈の重複になるか
- Agent / Model / Effort の provenance を、親子Agent間でどう保持するか
- 個人用自動化に、組織向けガバナンスを持ち込む境界はどこか
- 「追加する PR」だけでなく「公開入口を減らす PR」をどう評価するか

## 終わりに

このリポジトリの歴史は、単純な「作りすぎて失敗した」話ではありません。小さな不便を解消するスキルが、実装を完走するワークフローになり、複数Agentの協調系になり、それを安定させるルールと検証基盤へ育った記録です。

その過程で、自動化の能力は上がりました。しかし個人が理解し、直し、日常的に安価に使えるという最初の価値は薄くなりました。次のリポジトリでは、ここで得た機能ではなく、境界の学びを持ち越します。
