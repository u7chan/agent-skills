---
name: tailwind-ui-compose
description: >
  Composition-first UI design and Tailwind implementation guidance for screens,
  pages, and app surfaces that need clear hierarchy, restrained decoration, and
  responsive structure. Use when Codex is asked to design a new UI, restyle an
  existing screen, propose layout direction, or generate JSX/TSX with Tailwind
  while avoiding card-heavy, shadow-heavy, component-first output.
---

# Design UI Compose

## 概要

画面設計をコンポーネント配置から始めず、構成、情報階層、主役の定義から始める。
Tailwind 実装まで一貫して扱い、カード過多、装飾過多、狭すぎるレイアウトを避ける。

## 基本動作

1. 最初に `references/design-rules.md` を読む。
2. 画面の目的、主要タスク、最重要情報を特定する。
3. セクションを分割し、各セクションに目的を1つだけ割り当てる。
4. 各セクションの主役を1つだけ決める。
5. タイポグラフィ、余白、色、面の使い方を画面全体で統一する。
6. 構造を先に決めてから、必要最小限のコンポーネントを置く。
7. Tailwind で実装する時はテーマの尺度を優先し、 arbitrary value と装飾を増やしすぎない。
8. 狭い画面での優先順位崩れ、情報密度過多、横並びの破綻を確認する。

## 実行フロー

### 1. 構成を定義する

- セクション一覧を作る。
- 各セクションの役割を `inform` `compare` `input` `guide` `act` から選ぶ。
- 画面全体の主導線を決める。

### 2. 画面の世界観を固定する

- 余白の基準、タイポグラフィ階層、基調色、アクセント戦略を先に決める。
- セクションごとに別ルールを増やさない。
- 背景表現は弱く保ち、可読性を優先する。

### 3. 構造で整理する

- まず `section` `grid` `flex` `gap` `divider` で整理する。
- カードは明確な囲いが必要な時だけ使う。
- 影よりも境界線、面差、余白で階層を作る。

### 4. Tailwind に落とし込む

- `px-*` `py-*` `gap-*` `max-w-*` `grid-cols-*` など、テーマ準拠のユーティリティを優先する。
- ネストを浅く保つ。
- `shadow-lg` `shadow-xl` や大量の `rounded-*` を常用しない。
- モバイルでは横並びを無理に維持せず、縦積みへ再構成する。

### 5. 仕上げを検証する

- セクションごとに主役が1つか確認する。
- 強い装飾が複数箇所で競合していないか確認する。
- 小さな UI 要素が密集していないか確認する。
- 画面全体が同じ世界観でつながっているか確認する。

## 出力ルール

- 設計案だけを返す場合も、最初にセクション構成と優先順位を示す。
- JSX / TSX を書く場合は、意味のあるセクション分けと浅いラッパー構造を保つ。
- 既存デザインシステムがある場合は、その語彙を優先しつつ、本スキルの構成原則を守る。
- 派手さよりも、明快さ、一貫性、広がり、読みやすさを優先する。

## 参照資料

- 詳細ルール: `references/design-rules.md`
