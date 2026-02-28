---
name: plan-creator
description: plans/ディレクトリ内に生成されるプラン関連のスキル
---

## ワークフロー

### 1. 既存のプランを確認

```bash
ls plans/ 2>/dev/null || echo "Directory does not exist"
ls plans/ | grep "{project-name}_{task-description}" | sort -V | tail -1
```

### 2. ファイル名を生成

**形式:** `plans/{YYYY-MM-DD}_{project-name}_{task-description}_v{version}.md`

**構成要素:**
- `YYYY-MM-DD`: 現在の日付（ISO 8601形式）
- `project-name`: `apps/` または `packages/` 配下のディレクトリ名をkebab-caseで
- `task-description`: タスクを要約した3〜5語をkebab-caseで
- `version`: v1から始まる整数、更新時にインクリメント

### 3. 命名ルール

- **フラット構造**: すべてのファイルを `plans/` 直下に配置、サブディレクトリなし
- **スペースなし**: 単語区切りにはハイフン `-` を使用
- **バージョンインクリメント**: 更新時は必ずバージョンをインクリメントし、履歴を保持

### 4. 特別なケース

**クロスプロジェクトタスク:**
- 主要プロジェクトを先に: `2024-01-15_web-shop_cross-mobile-sync_v1.md`
- または `cross` を使用: `2024-01-15_cross_auth-system-unification_v2.md`

**インフラストラクチャ/ツール:**
- `infra-` または `repo-` プレフィックスを使用: `2024-01-15_infra-terraform_eks-migration_v1.md`

**調査/リサーチ:**
- `research` を含める: `2024-01-15_api-gateway_research-grpc-migration_v1.md`

### 5. ファイル内容のテンプレート

```yaml
---
created: YYYY-MM-DD
project: {project-name}
version: v{n}
previous_version: {filename or null}
status: draft | ready | archived
---
```

### 6. 出力形式

プランを生成する際は以下を出力:

```
## プラン

**パス:** `plans/YYYY-MM-DD_project-name_task-description_v1.md`

**内容:**
```yaml
---
created: YYYY-MM-DD
project: {project-name}
version: v1
previous_version: null
status: draft
---

[プラン内容をここに記述]
```
```

### 7. 検索パターン

```bash
# 特定のプロジェクトのプラン
ls plans | grep "_web-shop_"

# 日付範囲
ls plans | grep "^2024-01-15"

# 最新バージョンのみ
ls plans | awk -F'_v' '{print $1}' | sort | uniq
```
