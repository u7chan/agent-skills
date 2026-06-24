---
name: ai-identity-resolve
description: >
  Resolve AI agent identity metadata for review comments and PR replies. Use
  when composing AI review helper metadata or when another skill needs the
  current agent name and model name without guessing.
---

# 概要

AIレビュー補助コメントに入れるエージェント名とモデル名を、実行中の環境から取得する。
取得できない値は推測せず、省略する。

# 実行ルール

- エージェント名とモデル名は、実行中の環境から取得できた値をそのまま使う。
- スキルファイルの文中に登場する他のエージェント名や、対話相手のツール名を混同しない。
- 古い固定モデル名、プレースホルダー、例示用の値を投稿本文へ入れない。

# 手順

1. 自身のシステムプロンプトを参照する。
2. `You are <name>` に続く自己紹介文からエージェント名を抽出する。
3. モデル名は、実行環境が提供する明示的なモデル情報から抽出する。
4. モデル名が明示されていない場合は、モデル名を推測しない。
5. 取得できた識別情報を ` / ` で結合する。

# 取得例

- opencode の場合、システムプロンプトに `You are opencode` と記載されていれば、エージェント名は `opencode` とする。
- システムプロンプトに `You are powered by the model named <model>` のような記載があれば、モデル名は `<model>` とする。
- エージェント名だけ取得できた場合は、識別子を `（<agent>）` とする。
- エージェント名とモデル名の両方を取得できた場合は、識別子を `（<agent> / <model>）` とする。
- どちらも取得できない場合は、識別子を空文字列にする。

# 品質チェック

- [ ] `You are powered by` をエージェント名として扱っていない
- [ ] モデル名を推測で補っていない
- [ ] スキル本文に出てくる例示名を現在の実行者として扱っていない
