---
name: start-implementation
description: >
  Use this when the user asks to start work on an Issue or implementation task,
  such as "Issue #123 を対応して", "この機能を実装して", or "開発を始めて".
  It orchestrates issue confirmation, branch creation, step breakdown, implementation,
  quality checks, commits, and handoff to PR creation by delegating to existing skills.
---

# 概要

実装着手時の標準フローをまとめて扱う上位スキル。Issue や作業指示の確認から、ブランチ作成、実装、品質確認、コミット、PR 作成準備までを一貫して進行管理する。

# このスキルを使用するタイミング

- ユーザーが Issue 番号付きで実装着手を依頼した時
- ユーザーが「対応して」「実装して」「着手して」と依頼した時
- 複数ステップの実装を開始し、進め方の分割と進行管理が必要な時
- 実装後にコミットや PR 作成までつなげる前提の時

# Agentが行うこと

1. Issue または作業指示を確認し、要求と完了条件を整理する。
2. Issue 化されていない設計依頼で設計合意が必要な場合は、プランをユーザーに提示して同意を得てから `github-issue-create-from-plan` へ委譲する。
3. 現在のブランチを確認し、`main` `master` `develop` への直接 push を避ける。
4. 実装作業が必要なら `git-branch-create` へ委譲して作業ブランチを用意する。
5. 実装内容を複数ステップに分割し、順に実装する。
6. 各ステップで利用可能な lint、test、formatter を実行して品質確認する。
7. 実装ステップの完了ごとに `git-commit-message` へ委譲してコミット内容をまとめる。
8. すべての実装完了後、結果と残課題を整理してユーザー確認を取る。
9. ユーザーが PR 作成を求めた場合は、変更概要と検証結果を整理して `github-pr-create` へ委譲する。

# 入力と出力

## 入力

- Issue 番号、Issue URL、または実装指示
- リポジトリ内の関連コード、設定、ドキュメント
- 必要に応じたユーザー確認

## 出力

- 着手に必要な作業ブランチ
- ステップ分割された実装
- 品質確認済みの変更
- コミット候補またはコミット済みの変更
- 作成済み PR への引き継ぎ情報

# ステップの詳細

## 1. 依頼内容を確認する

- Issue がある場合は本文、受け入れ条件、テスト観点を確認する。テスト観点が Issue に記載されていない場合は、スコープから推測した観点をユーザーへ提示して確認を取った上で続行する。
- Issue がない場合は会話から目的、対象範囲、完了条件を抽出する。不足している場合はユーザーへ確認する。
- 実装に先立って設計合意が必要と判断した場合は、プランをユーザーに提示して同意を得てから `github-issue-create-from-plan` へ委譲する。自動で Issue 化しない。**設計合意が必要な目安**: 受け入れ条件や完了条件が会話・Issue から特定できない場合。Issue や会話から完了条件が明確に読み取れる場合は、Issue 化せずそのまま実装へ進む。

## 2. ブランチ方針を確定する

- 現在のブランチを確認する。
- `main` `master` `develop` で直接作業しない。
- これらの保護対象ブランチへ直接 push しない。
- 実装を始める前に `git-branch-create` を使って作業ブランチを作成する。ブランチ名の提案と作成は `git-branch-create` が担う。完了後は `start-implementation` が制御を引き継いで実装へ進む。

## 3. 実装ステップを分割する

- 変更を 2 以上の独立したステップに分けられるか確認する。
- 分割できる場合は、各ステップが個別に検証可能な粒度にする。
- 小規模変更でも、実装前に確認事項と検証方法を短く整理する。

## 4. 実装と品質確認を進める

- 各ステップで必要なコードやドキュメントを更新する。
- プロジェクトに lint、test、formatter がある場合はそのステップ内で実行する。
- チェックが失敗したまま次のステップへ進まない。

## 5. コミットをまとめる

- 実装ステップの完了ごとに差分を見直し、そのステップの変更をひとつのコミット候補にまとめる。
- コミットメッセージは `git-commit-message` に委譲する。委譲先がメッセージを提案したら必ずユーザーへ提示して確認を取る。確認後にコミットを確定し、次ステップへ進む。
- 途中コミットが不要な小変更でも、最終コミット前に粒度を確認する。

## 6. 完了後の引き継ぎを行う

- 変更概要、実行した検証、未解決事項を整理してユーザーに共有する。
- PR 作成に必要な変更概要と検証結果を整理する。
- ユーザーが PR 作成まで求めた場合だけ `github-pr-create` に委譲する。

# 委譲先スキル

- `github-issue-create-from-plan`: 実装前に設計プランを Issue 化したい時。Issue 作成完了後は `start-implementation` が制御を引き継いでブランチ作成・実装へ進む。
- `git-branch-create`: 作業ブランチ名の提案とブランチ作成が必要な時。ブランチ名の命名は委譲先が行う。完了後は `start-implementation` が制御を引き継いで実装へ進む。
- `git-commit-message`: コミットメッセージを提案する時。委譲先の挙動に関わらず、提案内容を必ずユーザーへ提示して確認を取る。確認後は `start-implementation` が制御を引き継いで次ステップへ進む。
- `github-pr-create`: PR を GitHub に作成する時

# 制約

- `main` `master` `develop` では直接実装しない。
- `main` `master` `develop` への直接 push を行わない。
- Issue や指示にない変更を広げすぎない。
- 品質確認コマンドが存在する場合は、実行結果を確認してから完了扱いにする。

# 品質チェック

- [ ] 実装着手時に使う上位スキルだと説明だけで分かる
- [ ] Issue 確認から PR 作成準備までの流れが記述されている
- [ ] `github-issue-create-from-plan` `git-branch-create` `git-commit-message` `github-pr-create` への委譲が明記されている
- [ ] `main` `master` `develop` への直接 push 禁止が明記されている
- [ ] ステップ分割と段階的な品質確認の方針が含まれている
