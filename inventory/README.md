# Skill Inventory (Phase 1)

全スキルの現状棚卸し結果。配布対象スキル（33件）と `.claude/skills/` 保守専用スキル（1件）の計34件を対象とする。

## Files

| File | Description |
|------|-------------|
| `skills.yaml` | 全スキルのメタデータ一覧（責務、本文量、参照関係、外部依存、disposition） |
| `dependency-graph.yaml` | スキル間依存グラフ（edges, cycles, reverse dependencies, physical path refs） |
| `findings.yaml` | 自動検出 + 人手判断による所見（肥大化、重複候補、分割統合候補） |
| `summary.yaml` | 数値サマリ |

## Generation

```sh
python3 .scripts/inventory.py
```

**Prerequisites**: Python 3.9+ with PyYAML (`pip install pyyaml`).

再実行により同一リビジョンから同一結果が得られる（決定論的）。

## Scope

- **配布対象 (distributable)**: `SKILL.md` を持つトップレベルディレクトリ（`.archive`, `.system`, `.codex`, `.claude/skills` を除く）
- **保守専用 (maintenance)**: `.claude/skills/` 配下の `SKILL.md` を持つディレクトリ（リポジトリ保守専用、READMEのAvailable Skillsとスキル数バッジには含めない）

## How to Read

### skills.yaml

各スキルの基本情報と棚卸し結果。主要フィールド:

- `name`: スキル名（frontmatterの`name`値）
- `current_path`: リポジトリルートからの相対ディレクトリパス
- `classification`: `distributable` または `maintenance`
- `responsibility`: 1文に要約した責務（frontmatterの`description`先頭文）
- `line_count`: SKILL.mdの行数（180行制限の判定に使用）
- `has_references` / `has_scripts` / `has_tests`: サブディレクトリの有無
- `skill_references`: 本文中で言及される他スキル名の一覧
- `path_references`: 本文中の`../`相対パス参照
- `external_dependencies`: 外部依存とその種別（required/conditional/optional/fallback）、情報源（README/SKILL.md）
- `disposition`: 維持判断（Phase 2で決定。現時点では全件`keep`）
- `findings`: 当該スキルに関する所見

### dependency-graph.yaml

- `nodes`: スキル名、パス、分類、行数
- `edges`: スキル間の参照関係（`from` → `to`）
- `cycles`: 検出された循環参照
- `reverse_dependencies`: レイヤー逆方向依存候補
- `physical_path_refs`: 相対パス（`../`）による物理参照

### findings.yaml

- `auto_detected`: スクリプトが自動検出した所見（行数超過、近接など）
- `manual`: 人手判断で追加した所見（重複責務、分割統合候補、共通依存など）

## Key Findings Summary

### 循環参照 (2件)

1. `herdr-github-pr-orchestrate` → `herdr-worktree-create` → `herdr-github-pr-orchestrate`
2. `github-pr-create` → `github-pr-orchestrate` → `github-pr-create`

### 肥大化注意 (5件)

150行を超えるが180行制限内: bun-dependency-update(151), herdr-agent-delegate(173), herdr-github-pr-orchestrate(156), npm-dependency-update(153), uv-dependency-update(161)

### 重複候補 (4件)

- `git-worktree-create` / `herdr-worktree-create`
- `grilling` / `design-plan-grill`
- `github-pr-orchestrate` / `herdr-github-pr-orchestrate`
- `agent-skill-design` / `agent-skill-refine`（責務境界は明確、統合不要の判断）

### 逆方向依存 (16件)

主に Herdr（オーケストレーション層）から Git/GitHub（操作層）への依存。アーキテクチャ上は期待される方向であり、レイヤー定義の再考が必要。

### 物理パス参照 (22件)

`../skill-name/SKILL.md` 形式のスキル間参照。特に `herdr-github-pr-orchestrate`(8件) と `herdr-prompt-evaluate`(3件) が多い。Phase 2 でシンボリックリンク方式への移行時に解消候補。

## Limitations

- スキル参照の自動抽出は正規表現ベースであり、自然言語での間接的な参照や「上位移譲」のような概念的な依存は捉えられない
- 外部依存の抽出はREADMEテーブルを優先するが、`command -v`パターンやコードブロック内のimportのみ補完する。網羅的な動的依存解析ではない
- `disposition` はPhase 2で決定するため、現時点では全件 `keep`
