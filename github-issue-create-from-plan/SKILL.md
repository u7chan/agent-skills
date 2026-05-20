---
name: github-issue-create-from-plan
description: >
  ユーザーから設計やプラン作成を求められ、その合意後にGitHub Issueを作成する時に使う。
  まずプランを作成して提示し、現在モードが plan の場合は切替案内を出し、edit または auto の場合はそのまま `gh issue create` を実行する。
  Issue作成後は人間向けHTMLも作成するか確認し、承諾された場合だけ `html-artifact-format` に従ってHTMLを生成する。
---

# 概要

設計を先に固め、その内容をGitHub Issueへ落とし込むためのスキル。現在モードに応じて、plan では実行前の切替案内を出し、edit または auto では余計な案内を挟まず Issue 作成まで進める。Issue 作成後は、人間がレビュー・共有しやすいHTMLも作るか確認する。

# 使用タイミング

- ユーザーが「まずプランを作って、その後 Issue にしたい」と依頼した時
- ユーザーがプラン合意後に `gh issue create` で起票する運用を求めた時
- ユーザーが現在モードに応じた Issue 作成フローを求めた時

# Agentが行うこと

1. リポジトリを探索し、要求に関係する実装と制約を把握する。
2. 不明点があればプランに影響する事項だけを確認する。
3. 決定完了なプランを `<proposed_plan>` ブロックで提示する。
4. 現在モードを判断し、plan の場合だけ Edit/Auto への切替案内を出す。
5. edit または auto の場合は、Issue の規模を判定し、`references/` 配下のテンプレートを **片方だけ** 読み込む。保持対象が多い、または設計判断を含む場合は Standard に切り替える。
6. edit または auto の場合は、確定済みプランの原文から、Issue に残すべき具体例を抽出する。
7. edit または auto の場合は、確定済みプランと抽出した具体例を基に Issue タイトルと本文を作る。
8. edit または auto の場合は、`gh issue create` を実行する。
9. 作成した Issue URL を返す。
10. Issue 作成後、人間向けHTMLも作成するか確認する。
11. 承諾された場合だけ、`html-artifact-format` に従ってHTMLを生成する。

# 入力 / 出力

## 入力

- ユーザーの設計依頼または仕様整理依頼
- リポジトリ内の関連コード、README、AGENTS.md、既存 Issue 文脈
- plan モード時のみ、ユーザーの `OK` 合図
- Issue 作成後のHTML確認に対するユーザーの承諾

## 出力

- `<proposed_plan>` ブロックを含む設計プラン
- plan モード時のみ、Edit/Auto モード切替と Issue 作成待ちを示す短い案内
- 作成済み GitHub Issue の URL
- Issue 作成後の人間向けHTML作成確認
- 承諾された場合のみ、人間向けHTML（`./output/{slug}.html`）

# ステップの詳細

## 1. プランを作る

- まず関連コード、設定、ドキュメントを読む。
- プランに影響する事実は探索で確定する。
- 影響の大きい仕様だけをユーザーに確認する。
- 実装担当者が追加判断なしで着手できる粒度までプランを固める。

## 2. プランを提示する

- `<proposed_plan>` ブロックで提示する。
- プランには少なくとも要約、主要変更点、テスト観点、前提を含める。
- 設計説明は箇条書きだけで終わらせず、フロー、データ構造、ロジック、DB関係などを最も伝わる具体表現で示す。
- 実装はまだ行わない。

## 3. プラン提示後の応答

- `<proposed_plan>` の直後に現在モードを見て分岐する。
- plan モードの場合は、`Edit または Auto モードに切り替えてください。切替後に OK と送ってください。` と明示し、ここでは `gh issue create` を実行しない。
- edit または auto モードの場合は、切替案内や `OK` 待ちを挟まず、Issue 作成へ進む。
- 現在モードを判定できない場合は安全側に倒し、plan モードと同じ案内を出す。

## 4. 待機条件

- plan モードでは、ユーザーが `OK` と返すまでは Issue を作成しない。
- plan モードで `OK` を受け取った場合は、切替後の edit または auto モードとして Issue 作成へ進む。
- edit または auto モードでは、`OK` を待たずに Issue を作成する。
- plan モードで `OK` 以外の修正依頼が来たら、プラン更新を優先する。

## 5. テンプレートを選ぶ

Issue の規模に応じて、`references/` 配下のテンプレートを **どちらか片方だけ** 読み込む。両方を同時に読まない。Context を節約するため、判定前にテンプレ本文を投機的に読まない。

判定基準:

| 判定 | 参照ファイル | 適用例 |
| --- | --- | --- |
| Light / 軽量 | `references/issue-template-light.md` | typo、コメント修正、文言変更、命名のみのリファクタ、依存パッケージの軽微なバージョン更新、単一箇所で完結する明らかなバグ修正、ドキュメントの小さな追記 |
| Standard / 標準 | `references/issue-template-standard.md` | 機能追加、API 変更、DB スキーマ変更、設計判断を含む変更、複数ファイル横断の修正、パフォーマンス改善、セキュリティ修正 |

判断に迷う場合は Standard を選ぶ。Light で書き始めて設計説明や Out of Scope が必要だと判明したら、Standard に切り替えて読み直す。

## 6. Issue を作成する

- 直前に確定したプランと、選んだテンプレートだけを元に Issue を書く。
- Issue 本文を書き始める前に、直前に確定した `<proposed_plan>` 原文から次の保持対象を確認する。
  - サンプル例、具体的な入出力例
  - コードブロック、擬似コード、スキーマ、JSON、SQL
  - 表、Mermaid、状態遷移、シーケンス図
  - 実装判断やレビュー判断に必要な具体値、ファイル例、API 例
- 保持対象は要約で消さず、Issue 本文の適切なセクションに原文に近い形で移す。
- 保持対象が実装判断に必要か迷う場合は残す。
- Standard の場合は、保持対象を主に `Design Details / 設計詳細` に置く。補足的な例は `Notes / 補足` に置いてよい。
- Light の場合でも、保持対象があるなら `Examples / サンプル` セクションを追加して残す。保持対象が多い、または設計判断を含む場合は Standard に切り替える。
- Issue タイトルは内容が一目で分かる具体的な文にする。
- モノレポ運用で対象アプリやパッケージが明確な場合、Issue タイトルの先頭に Prefix を付ける。
- Prefix 形式は `[example-app] title example` のように `[scope] summary` を使う。
- 単一リポジトリ、または対象スコープが1つに定まらない場合は Prefix を付けない。
- Issue 作成時は、対象リポジトリで現在設定されている Label 一覧を確認する。
- Label は確認できた候補の中から、Issue 内容に最も合うものだけを選んで付与する。
- 適切な Label が存在しない場合は、存在しない Label 名を新規に仮定して付けない。
- ただし、既存 Label では運用上どうしても不足し、新規作成が妥当な場合は候補 Label 名と用途をユーザーに一度提案してから作成する。
- ユーザーが README や `AGENTS.md` の更新を要求している場合は、本文の `### Documentation / ドキュメント` セクションに明記する。
- `gh issue create` を使い、必要なら対象リポジトリを `--repo` で明示する。
- Label を付ける場合は、事前に確認した既存 Label 名だけを `--label` で明示する。
- 新規 Label が必要な場合は、ユーザー合意前に Label を作成しない。
- Issue 本文は必ず一時ファイルに書き、`--body-file` で渡す。Markdown を `--body "..."` や `$'...\n...'` へ直接埋め込まない。
- Issue 本文に Mermaid を含める場合は、GitHub の Mermaid プレビューで壊れやすい記法を避ける。
  - ノードラベルに `/`、`[`、`]`、`(`、`)`、`:`、`?`、`#`、`&`、`|` などを含める場合は必ず引用符付きラベルにする: `A["/path/to/resource"]`
  - `A[/path]` は平行四辺形ノード記法として解釈されるため、API path やファイルパス表記には使わない。
  - エッジラベルは `-- true -->` より `-- "true" -->` のように引用符付きにする。
  - Mermaid ブロックを作ったら、Issue 作成前にコードブロックだけを読み返し、括弧・角括弧・引用符が閉じていることを確認する。
- Issue 作成前に、`<proposed_plan>` 原文にあった保持対象が Issue 本文から落ちていないか読み返す。
- `gh issue create` は次の形を優先して使う。

    FILE=$(mktemp)
    trap 'rm -f "$FILE"' EXIT
    cat > "$FILE" << 'EOF'
    ## Overview / 概要
    ...
    EOF

    gh issue create \
      --repo owner/repo \
      --title "Issue title" \
      --body-file "$FILE"

- タイトルと本文をコマンド内で明示し、対話入力モードには入らない。
- GitHub コネクタは使わず、`gh` の認証で作成する。コネクタと `gh` は認証主体や権限が異なるため、書き込み操作で 403 になることがある。

## 7. Issue 作成後のHTML確認

- Issue URL を返した直後に、`人間向けHTMLも作成しますか？` と確認する。
- 確認文は Issue 作成後にだけ出し、Issue 作成前の plan モード待機中には出さない。
- 承諾された場合は、`html-artifact-format` を使用する。
- HTML生成時は、確定済み `<proposed_plan>` と作成済み Issue 本文/URL を素材にする。
- Issue 本文は実装者向けMarkdownとして残し、HTML側は人間のレビュー・共有用に要約、比較、論点、次アクションを前面に出して再構成する。
- HTMLテンプレートは `html-artifact-format` の規模判定に従い、`single-screen-brief`、`scroll-report`、`tabbed-workspace` のどれか1つを選ぶ。
- HTML生成のトリガーは、直前の確認に対する `OK`、`お願いします`、`作って`、`yes` などの明確な承諾だけにする。
- HTML確認への承諾がない場合、承諾が曖昧な場合、または修正依頼が来た場合はHTMLを生成しない。

## 8. 完了報告

- Issue URL を返す。
- タイトルと含めた主要論点を1文か2文で要約する。
- Issue 作成直後は、人間向けHTMLも作成するか確認する。
- HTMLも生成した場合は、保存先と選択テンプレートも返す。

# 品質チェック

- [ ] スキルの説明だけで、プラン作成後に Issue 作成へ進む用途だと分かる
- [ ] plan モードでは `OK` が来る前に `gh issue create` を実行しない
- [ ] edit または auto モードでは切替案内や `OK` 待ちを挟まず `gh issue create` を実行する
- [ ] プランは `<proposed_plan>` ブロックで提示する
- [ ] Issue 規模を判定し、`references/issue-template-light.md` または `references/issue-template-standard.md` のどちらか片方だけを読み込む
- [ ] モノレポ時の Issue タイトル Prefix ルールが明記されている
- [ ] Issue 作成時に既存 Label から選んで付与するルールが明記されている
- [ ] 新規 Label が必要な場合にユーザー提案と合意を先に取るルールが明記されている
- [ ] ユーザー要求があれば README と `AGENTS.md` 更新が Issue に含まれる
- [ ] 現在モードを判定できない場合は plan モード相当の安全な案内になる
- [ ] `<proposed_plan>` 原文のサンプル例、コードブロック、表、Mermaid、具体的な入出力例が Issue 本文に保持されている
- [ ] Issue 本文は `--body-file` で渡し、Markdown をシェル引数へ直接埋め込まない
- [ ] Mermaid を含める場合は、特殊文字を含むノード/エッジラベルを引用符付きにしてプレビュー崩れを防ぐ
- [ ] Issue URL を返した直後に、人間向けHTMLも作成するか確認している
- [ ] Issue 作成前や plan モード待機中にHTML作成確認を出していない
- [ ] HTML確認に対する明確な承諾がある場合だけ `html-artifact-format` に従ってHTMLを生成している
