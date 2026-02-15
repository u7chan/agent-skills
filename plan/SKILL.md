---
name: plan
description: Skills related to plan files generated within the plans/ directory
---

## Workflow

### 1. Check Existing Plans
```bash
ls plans/ 2>/dev/null || echo "Directory does not exist"
ls plans/ | grep "{project-name}_{task-description}" | sort -V | tail -1
```

### 2. Generate Filename
**Format:** `plans/{YYYY-MM-DD}_{project-name}_{task-description}_v{version}.md`

**Components:**
- `YYYY-MM-DD`: Current date (ISO 8601)
- `project-name`: Directory name under `apps/` or `packages/` in kebab-case
- `task-description`: 3-5 words summarizing the task in kebab-case
- `version`: Integer starting from v1, increment for updates

### 3. Naming Rules
- **Flat structure**: All files directly under `plans/`, no subdirectories
- **No spaces**: Use hyphens `-` for word separation
- **Version increment**: Always increment version when updating, keep history

### 4. Special Cases

**Cross-project tasks:**
- Primary project first: `2024-01-15_web-shop_cross-mobile-sync_v1.md`
- Or use `cross`: `2024-01-15_cross_auth-system-unification_v2.md`

**Infrastructure/Tooling:**
- Use `infra-` or `repo-` prefix: `2024-01-15_infra-terraform_eks-migration_v1.md`

**Research/Investigation:**
- Include `research`: `2024-01-15_api-gateway_research-grpc-migration_v1.md`

### 5. File Content Template

```yaml
---
created: YYYY-MM-DD
project: {project-name}
version: v{n}
previous_version: {filename or null}
status: draft | ready | archived
---
```

### 6. Output Format

When generating a plan file, output:

```
## Plan File

**Path:** `plans/YYYY-MM-DD_project-name_task-description_v1.md`

**Content:**
```yaml
---
created: YYYY-MM-DD
project: {project-name}
version: v1
previous_version: null
status: draft
---

[Plan content here]
```
```

### 7. Search Patterns

```bash
# Specific project plans
ls plans | grep "_web-shop_"

# Date range
ls plans | grep "^2024-01-15"

# Latest versions only
ls plans | awk -F'_v' '{print $1}' | sort | uniq
```
