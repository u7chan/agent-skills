# Skill Inventory

全スキルの現状棚卸し結果。配布対象スキルと `.claude/skills/` 保守専用スキルを対象とする。

## Files

| File | Description |
|------|-------------|
| `skills.yaml` | 全スキルのメタデータ一覧（責務、本文量、参照関係、外部依存、disposition） |
| `dependency-graph.yaml` | スキル間依存グラフ（edges, cycles, reverse dependencies, physical path refs） |
| `findings.yaml` | 自動検出 + 人手判断による所見（肥大化、重複候補、分割統合候補） |
| `summary.yaml` | 数値サマリ |

4ファイルはいずれもトップレベルに`schema_version: 2`を持つ。`skills.yaml`はREADME/正本由来の直接依存と静的証拠を分離し、`dependency-graph.yaml`は正本の`depends_on`だけを`edges`へ入れる。

## Generation

```sh
python3 .scripts/inventory.py
```

**Prerequisites**: Python 3.9+ with PyYAML (`pip install pyyaml`).

再実行により同一リビジョンから同一結果が得られる（決定論的）。`bash .scripts/validate-skills.sh` は4ファイルを一時生成してchecked-in版と比較し、陳腐化を `V-INV-001` ERRORにする。

## Scope

- **配布対象 (distributable)**: `skills/` 配下のカテゴリディレクトリ内の `SKILL.md`（`.archive`, `.system`, `.codex`, `.claude/skills` を除く）
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
- `external_dependencies`: 外部依存とその種別（required/conditional/optional/fallback）、宣言元（配布SkillはREADME、保守Skillは正本）
- `external_dependency_evidence`: import・静的commandの確認証拠（宣言を自動上書きしない）
- `disposition`: 維持判断（`keep` または `archive`）
- `findings`: 当該スキルに関する所見

### dependency-graph.yaml

- `nodes`: スキル名、パス、分類、行数
- `edges`: スキル間の参照関係（`from` → `to`）
- `cycles`: 検出された循環参照
- `reverse_dependency_candidates`: レイヤー逆方向依存候補
- `physical_path_refs`: 相対パス（`../`）による物理参照

### findings.yaml

- `auto_detected`: スクリプトが自動検出した所見（行数超過、近接など）
- 人手判断で追加した所見（重複責務、分割統合候補、共通依存など）

## Key Findings Summary

### 循環参照 (0件)

`depends_on` エッジのみを対象としたTarjan SCCによる循環検出では、循環参照は検出されなかった。

### 肥大化注意 (4件)

150行を超えるが180行制限内: bun-dependency-update(151), herdr-github-pr-orchestrate(157), npm-dependency-update(153), uv-dependency-update(161)

### 重複候補 (4件)

- `git-worktree-create` / `herdr-worktree-create`
- `grilling` / `design-plan-grill`
- `github-pr-orchestrate` / `herdr-github-pr-orchestrate`
- `agent-skill-design` / `agent-skill-refine`（責務境界は明確、統合不要の判断）

### 逆方向依存候補 (0件)

正本の`depends_on`にはカテゴリ逆方向依存がない。

### 物理パス参照 (4件)

いずれも `.claude/skills` のsymlink targetまたはworktree出力先を示す`general`参照で、他Skill内部への物理参照はない。

## Limitations

- スキル参照の自動抽出は正規表現ベースであり、自然言語での間接的な参照や「上位移譲」のような概念的な依存は捉えられない
- 外部依存の証拠はPython AST、JS/TSの静的import/require、文書・shellの静的commandを対象とし、動的に組み立てられる依存は解析しない
- `disposition` は正本（skill-categories.yaml）の分類に従う
