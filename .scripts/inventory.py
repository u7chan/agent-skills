#!/usr/bin/env python3
"""Phase 1: 全スキルの棚卸し — 配布対象 + .claude/skills/ 保守専用スキルを走査し、
責務・参照関係・外部依存・本文量・重複候補を YAML として inventory/ に出力する。"""

import argparse
import hashlib
import os
import re
import sys
import yaml
from collections import OrderedDict
from pathlib import Path

from skill_validation.external import CANONICAL_DEPENDENCY_ALIASES, normalize_dependency_name

REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = REPO_ROOT / "inventory"
CANONICAL_CATEGORIES = REPO_ROOT / ".rules/skill-categories.yaml"
CANONICAL_RULES = REPO_ROOT / ".rules/skill-rules.yaml"

# ── スコープ定義 ──────────────────────────────────────────
EXCLUDE_DIRS = {".git", ".archive", ".codex", ".system", ".github", ".agents",
                "node_modules", "inventory", "__pycache__"}
MAINTENANCE_PREFIX = ".claude/skills"
SKILL_FILE_EXTS = {".md", ".py", ".sh", ".yaml", ".yml"}
SKILL_FILE_EXCLUDES = {"agents/openai.yaml"}  # agent設定は走査対象外

# ── 外部依存の種別 ────────────────────────────────────────
DEP_TYPES = ("required", "conditional", "optional", "fallback")

# ── 外部依存の別名正規化マップ（canonical → 別名集合） ───
DEP_ALIAS_MAP = {name: set(aliases) for name, aliases in CANONICAL_DEPENDENCY_ALIASES.items()}

# ── 明示的レイヤー定義 ────────────────────────────────────
# prefix → layer index。ここにない prefix は unclassified (index=-1)
LAYER_DEF = OrderedDict([
    # primitive layer (git, github, package managers, codex etc.)
    ("git", 0), ("github", 0),
    ("bun", 0), ("npm", 0), ("uv", 0),
    ("codex", 0), ("cagent", 0),
    # utility layer (self-maintenance, QA, text, UI, browser etc.)
    ("skill", 1), ("agent", 1),
    ("japanese", 1), ("qa", 1),
    ("tailwind", 1), ("apple", 1),
    ("html", 1), ("playwright", 1),
    ("image", 1), ("customize", 1),
    # orchestration layer (Herdr, design, grilling)
    ("herdr", 2), ("design", 2), ("grill", 2),
])

# ── 関連種別（スキル間参照） ──────────────────────────────
# depends_on : 呼び出し・委譲・参照など、実際に依存している関係
# routes_to  : 条件によって切り替え・選択される関係
# used_by    : 当該スキルが他から使われる旨の説明
# mention    : 比較・禁止・単なる言及
RELATION_TYPES = ("depends_on", "routes_to", "used_by", "mention")


# ====================================================================
# ヘルパー
# ====================================================================

def _find_line_number(lines: list[str], match_text: str) -> int:
    """match_text を含む最初の行番号 (1-indexed) を返す。見つからなければ 0。"""
    for i, line in enumerate(lines, 1):
        if match_text in line:
            return i
    return 0


def normalize_dep_name(name: str) -> str:
    """別名を正規形に変換。例: 'python 3' → 'python', 'node.js' → 'node'."""
    return normalize_dependency_name(name)


def normalize_dep_name_no_map(name: str) -> str:
    """簡単な正規化のみ（小文字化、バッククォート除去）。"""
    name = name.strip().lower()
    return re.sub(r"[`'\"]", "", name)


def classify_ref_relation(surrounding_text: str) -> str:
    """周辺文脈からスキル参照の関係種別を判定する。"""
    t = surrounding_text.lower()
    if re.search(r'(?:を使う|を利用|を呼|へ委譲|へ依頼|に従|を参照|を経由|に任せ|に送信|で配置|引き渡|に渡す|へ渡す|を開く|から読)', t):
        return "depends_on"
    if re.search(r'(?:を使い分け|へ切り替|を選ぶ|いずれか|の一方|または|どちら|選択)', t):
        return "routes_to"
    if re.search(r'(?:使われる|から使わ|から呼ば|から利用|が.*用意|が.*行う|が.*使う|が.*利用|が.*参照|が.*呼ぶ|used.by|から開か)', t):
        return "used_by"
    if re.search(r'(?:禁止|行わない|しない|使わない|異なる|ではない|しません|置き換)', t):
        return "mention"
    return "mention"


def get_layer(prefix: str) -> tuple[int, str]:
    """prefix からレイヤー (index, name) を返す。"""
    layer_names = {0: "primitive", 1: "utility", 2: "orchestration"}
    idx = LAYER_DEF.get(prefix, -1)
    name = layer_names.get(idx, "unclassified")
    return (idx, name)


# ====================================================================
# スキルファイル走査
# ====================================================================

def find_skill_files() -> list[Path]:
    """スコープ内の全 SKILL.md を返す。"""
    skills = []
    for root, dirs, files in os.walk(REPO_ROOT):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        if "SKILL.md" in files:
            rel = Path(root).relative_to(REPO_ROOT)
            if str(rel) != ".":
                skills.append(rel / "SKILL.md")
    public_roots = [path for path in REPO_ROOT.iterdir() if not path.name.startswith(".")]
    maintenance_root = REPO_ROOT / MAINTENANCE_PREFIX
    if maintenance_root.is_dir():
        public_roots.extend(maintenance_root.iterdir())
    for directory in public_roots:
        candidate = directory / "SKILL.md"
        relative = candidate.relative_to(REPO_ROOT)
        if directory.is_symlink() and candidate.is_file() and relative not in skills:
            skills.append(relative)
    return sorted(skills)


def classify_skill(rel_path: Path) -> str:
    """distributable か maintenance かを返す。"""
    if str(rel_path).startswith(MAINTENANCE_PREFIX):
        return "maintenance"
    return "distributable"


def scan_skill_files(skill_dir: Path) -> list[dict]:
    """スキル配下の全テキストファイルを走査し、ファイルパス・内容・行リストを返す。

    Returns:
        [{"rel_path": str, "content": str, "lines": [str]}, ...]
    """
    results = []
    # SKILL.md 本体
    skill_md = skill_dir / "SKILL.md"
    if skill_md.exists():
        content = skill_md.read_text()
        results.append({
            "rel_path": "SKILL.md",
            "content": content,
            "lines": content.splitlines(),
        })

    # references/, scripts/, agents/ サブディレクトリ
    for sub in ("references", "scripts", "agents"):
        sub_dir = skill_dir / sub
        if not sub_dir.is_dir():
            continue
        for f in sorted(sub_dir.iterdir()):
            if f.is_file():
                rel_in_skill = str(f.relative_to(skill_dir))
                # スキップするファイル
                if rel_in_skill in SKILL_FILE_EXCLUDES:
                    continue
                ext = f.suffix.lower()
                if ext not in SKILL_FILE_EXTS and not f.name.endswith(".md"):
                    continue
                try:
                    content = f.read_text()
                    results.append({
                        "rel_path": rel_in_skill,
                        "content": content,
                        "lines": content.splitlines(),
                    })
                except Exception:
                    pass

    return results


# ====================================================================
# フロントマター解析
# ====================================================================

def parse_frontmatter(content: str) -> dict:
    """YAML frontmatter を抜き出す。"""
    fm_match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    if not fm_match:
        return {}
    try:
        return yaml.safe_load(fm_match.group(1)) or {}
    except yaml.YAMLError:
        return {}


def extract_responsibility(skill_name: str, frontmatter: dict) -> str:
    """責務を1文で返す。description の先頭文を優先。"""
    desc = frontmatter.get("description", "")
    if desc:
        desc = desc.strip()
        first_sentence = re.split(r"。|(?<!\d)\.(?=\s|$)", desc.replace("\n", " "))[0].strip()
        if first_sentence:
            return first_sentence
    return f"unknown: {skill_name}"


def count_lines(filepath: Path) -> int:
    """ファイル行数。"""
    with open(filepath) as f:
        return sum(1 for _ in f)


def check_subdirs(skill_dir: Path) -> dict:
    """references/ scripts/ の有無を返す。"""
    result = {}
    for sub in ("references", "scripts", "tests", "evaluation-samples"):
        p = skill_dir / sub
        if p.is_dir():
            result[sub] = True
    return result


# ====================================================================
# スキル参照抽出（関係種別付き）
# ====================================================================

def _build_file_relpath(skill_relative: Path, file_rel_path: str) -> str:
    """スキル相対パスとファイル相対パスからリポジトリルート相対パスを生成。"""
    parent = skill_relative.parent if skill_relative.name == "SKILL.md" else skill_relative
    return str(parent / file_rel_path)


def extract_skill_references(file_contents: list[dict],
                             all_skill_names: set[str],
                             own_name: str) -> list[dict]:
    """本文中の他スキル参照を関係種別付きで抽出する。

    - バッククォート内のスキル名: 周辺文脈から関係種別を判定
    - ../skill-name/ 形式の相対パス参照: depends_on
    - 自然言語でのスキル名言及: 周辺文脈から関係種別を判定

    Returns:
        [{"name": str, "relation": str, "source_file": str, "source_line": int}, ...]
    """
    refs: dict[str, dict] = {}  # name → {relation, source_file, source_line}

    for file_info in file_contents:
        content = file_info["content"]
        lines = file_info["lines"]
        rel_path = file_info["rel_path"]

        # ── ../skill-name/ 形式のパス参照（最優先。常に depends_on） ──
        for m in re.finditer(r"\.\./?(?:[a-z]+-(?:[a-z]+-)*[a-z]+)", content):
            matched = m.group(0)
            clean = matched.lstrip("./")
            parts = clean.split("/")
            for part in parts:
                if part in all_skill_names and part != own_name:
                    line = _find_line_number(lines, matched)
                    # パス参照は常に depends_on、出典は最も早い行を優先
                    if part not in refs or refs[part]["source_line"] > line:
                        refs[part] = {
                            "name": part,
                            "relation": "depends_on",
                            "source_file": rel_path,
                            "source_line": line,
                        }

        # ── バッククォートで囲まれたスキル名 ──
        for m in re.finditer(r"`([a-z]+-[a-z]+-[a-z]+(?:-[a-z]+)*)`", content):
            name = m.group(1)
            if name == own_name:
                continue
            if name not in all_skill_names:
                continue
            line = _find_line_number(lines, m.group(0))
            context_start = max(0, line - 2)
            context_end = min(len(lines), line + 1)
            context = "\n".join(lines[context_start:context_end])
            relation = classify_ref_relation(context)
            # depends_on が最優先。既存の mention より優先。ただしパス参照で既に depends_on なら上書きしない
            if name not in refs:
                refs[name] = {"name": name, "relation": relation, "source_file": rel_path, "source_line": line}
            elif refs[name]["relation"] != "depends_on" and relation == "depends_on":
                refs[name] = {"name": name, "relation": relation, "source_file": rel_path, "source_line": line}

        # ── プレーンなスキル名言及（バッククォート外） ──
        for name in sorted(all_skill_names, key=len, reverse=True):
            if name == own_name or name in refs:
                continue
            pattern = r'(?<![a-z-])' + re.escape(name) + r'(?![a-z-])'
            for m in re.finditer(pattern, content):
                start = m.start()
                before_sub = content[max(0, start - 1):start]
                after_sub = content[m.end():m.end() + 1]
                if before_sub == "`" and after_sub == "`":
                    continue
                line = _find_line_number(lines, m.group(0))
                context_start = max(0, line - 2)
                context_end = min(len(lines), line + 1)
                context = "\n".join(lines[context_start:context_end])
                relation = classify_ref_relation(context)
                if name not in refs:
                    refs[name] = {"name": name, "relation": relation, "source_file": rel_path, "source_line": line}
                elif refs[name]["relation"] != "depends_on" and relation == "depends_on":
                    refs[name] = {"name": name, "relation": relation, "source_file": rel_path, "source_line": line}

    return sorted(refs.values(), key=lambda x: x["name"])


# ====================================================================
# 物理パス参照抽出（種別分類付き）
# ====================================================================

def extract_path_references(file_contents: list[dict],
                            all_skill_names: set[str]) -> list[dict]:
    """物理パス参照 (../) を種別付きで抽出する。

    Returns:
        [{"path": str, "type": "skill_internal"|"general", "source_file": str, "source_line": int}, ...]
    """
    refs: dict[str, dict] = {}  # path → {type, source_file, source_line}

    for file_info in file_contents:
        content = file_info["content"]
        lines = file_info["lines"]
        rel_path = file_info["rel_path"]

        for m in re.finditer(r"\.\./[^\s`)\]]+", content):
            matched = m.group(0)
            clean = matched.rstrip(".,;:")
            # スキル内部参照かどうかを判定
            # 最初のパス要素がスキル名に一致するか
            first_component = clean.lstrip("./").split("/")[0]
            ptype = "skill_internal" if first_component in all_skill_names else "general"
            line = _find_line_number(lines, matched)
            # 同じパスなら最初の発見を優先
            if clean not in refs:
                refs[clean] = {
                    "path": clean,
                    "type": ptype,
                    "source_file": rel_path,
                    "source_line": line,
                }

    return sorted(refs.values(), key=lambda x: x["path"])


# ====================================================================
# 外部依存抽出
# ====================================================================

def parse_readme_deps() -> dict[str, list[dict]]:
    """README.md の Available Skills テーブルから外部依存を取得する。

    README の External Dependencies 列を直接の正本として扱い、
    R/C/O/F grammar を解析する。実装中の import・command はここへ混ぜない。
    """
    readme_path = REPO_ROOT / "README.md"
    if not readme_path.exists():
        return {}

    with open(readme_path, encoding="utf-8") as f:
        content = f.read()

    deps: dict[str, list[dict]] = {}
    row = re.compile(r"^\|\s*\[([^]]+)\]\(([^)]+/SKILL\.md)\)\s*\|[^|]*\|\s*(.*?)\s*\|\s*$")
    type_by_symbol = {"R": "required", "C": "conditional", "O": "optional", "F": "fallback"}
    for line in content.splitlines():
        match = row.match(line)
        if not match:
            continue
        name, dep_text = match.group(1), match.group(3).strip()
        dep_list: list[dict] = []
        if dep_text not in ("—", ""):
            for part in _split_dependency_items(dep_text):
                annotation = re.search(r"\(\s*([RCOF])\s*\)\s*$", part, re.IGNORECASE)
                dep_type = type_by_symbol.get(annotation.group(1).upper(), "required") if annotation else "required"
                if annotation:
                    part = part[:annotation.start()].strip()
                part = part.replace("`", "").strip()
                if part and part != "—":
                    dep_list.append({"name": part, "type": dep_type, "source": "README"})
        deps[name] = dep_list

    return deps


def _split_dependency_items(text: str) -> list[str]:
    """カンマ区切りを基本に、旧来の ``A / B (O)`` も個別化する。"""
    items: list[str] = []
    for raw in text.split(","):
        raw = raw.strip()
        if not raw or raw == "—":
            continue
        annotation = re.search(r"(\(\s*[RCOF]\s*\))\s*$", raw, re.IGNORECASE)
        suffix = annotation.group(1) if annotation else ""
        body = raw[:annotation.start()].strip() if annotation else raw
        alternatives = [value.strip() for value in re.split(r"\s+/\s+", body) if value.strip()]
        items.extend(f"{alternative} {suffix}".strip() for alternative in alternatives)
    return items


def extract_external_dependency_evidence(file_contents: list[dict]) -> list[dict]:
    """import・command の静的証拠を確認材料として収集する。

    これは README の直接依存へ自動追加しない。宣言との差分判定は
    Phase 3 validator に委ね、inventory には証拠としてのみ保存する。
    """
    evidence: list[dict] = []
    seen: set[tuple[str, str, str]] = set()

    def add_evidence(name: str, evidence_type: str, source: str) -> None:
        canonical = normalize_dep_name(name)
        key = (canonical, evidence_type, source)
        if canonical and key not in seen:
            seen.add(key)
            evidence.append({"name": canonical, "evidence_type": evidence_type, "source": source})

    for file_info in file_contents:
        content = file_info["content"]
        rel_path = file_info["rel_path"]

        # `command -v <cmd>` パターン
        for cmd_match in re.finditer(r"`command -v (\w+)`", content):
            add_evidence(cmd_match.group(1), "command-v", rel_path)

        # `which <cmd>` パターン
        for which_match in re.finditer(r"`which (\w+)`", content):
            add_evidence(which_match.group(1), "which", rel_path)

        # 全コードブロックから import 文を抽出（Python / JS / TS）
        for code in re.findall(r"```[^\n]*\n(.*?)```", content, re.DOTALL):
            # Python: from/import
            for imp in re.finditer(r"(?:^|\n)(?:from|import)\s+([a-zA-Z_]\w+)", code):
                mod = imp.group(1)
                if mod.lower() in ("os", "sys", "json", "re", "yaml", "pathlib",
                                    "subprocess", "shutil", "typing", "io", "time",
                                    "hashlib", "collections", "dataclasses", "importlib",
                                    "__future__", "argparse", "logging", "tempfile"):
                    continue
                add_evidence(mod, "python-import", rel_path)
            # JS/TS: import { ... } from '...' / import ... from '...'
            for imp in re.finditer(r"(?:^|\n)\s*import\s+(?:\{[^}]*\}|\*\s+as\s+\w+|\w+)\s+from\s+['\"]([^'\"]+)['\"]", code):
                mod = imp.group(1)
                if mod.startswith(".") or mod.startswith("node:"):
                    continue
                pkg = mod.split("/")[0] if mod.startswith("@") else mod.split("/")[0]
                add_evidence(pkg, "module-import", rel_path)

        # 実ファイルの import 文（.py ファイルの直接解析）
        if rel_path.endswith(".py"):
            for imp in re.finditer(r"(?:^|\n)(?:from|import)\s+([a-zA-Z_]\w+)", content):
                mod = imp.group(1)
                if mod.lower() in ("os", "sys", "json", "re", "yaml", "pathlib",
                                   "subprocess", "shutil", "typing", "io", "time",
                                   "hashlib", "collections", "dataclasses", "importlib",
                                   "__future__", "argparse", "logging", "tempfile"):
                    continue
                add_evidence(mod, "python-import", rel_path)

        # .sh ファイルのコマンド参照
        if rel_path.endswith(".sh"):
            for cmd in re.finditer(r"(?:^|\s)([a-zA-Z_][a-zA-Z0-9_-]{2,})\s", content):
                c = cmd.group(1).lower()
                if c in ("set", "if", "then", "else", "elif", "fi", "for", "while",
                         "do", "done", "in", "esac", "case", "echo", "exit", "cd",
                         "dir", "ls", "test", "unset", "export", "local", "readonly",
                         "shift", "return", "source", "trap", "wait", "exec", "eval"):
                    continue
                add_evidence(c, "shell-command", rel_path)

    return sorted(evidence, key=lambda item: (item["name"], item["evidence_type"], item["source"]))


def extract_external_deps(skill_name: str,
                          file_contents: list[dict],
                          readme_deps: dict[str, list[dict]]) -> list[dict]:
    """READMEの直接宣言だけをinventory形式へ変換する互換ヘルパー。"""
    del file_contents
    return [
        {"name": normalize_dep_name(dependency["name"]), "type": dependency["type"], "source": "README"}
        for dependency in readme_deps.get(skill_name, [])
    ]


# ====================================================================
# 依存グラフ構築（SCCベース循環検出、明示的レイヤー、関係種別利用）
# ====================================================================

def tarjan_scc(adj: dict[str, set[str]]) -> list[list[str]]:
    """Tarjan の SCC アルゴリズムで決定的に強連結成分を列挙する。
    各 SCC 内のノード、SCC 間の順序はソートされる。
    """
    index_counter = 0
    stack: list[str] = []
    on_stack: set[str] = set()
    indices: dict[str, int] = {}
    lowlinks: dict[str, int] = {}
    sccs: list[list[str]] = []

    def strongconnect(v: str) -> None:
        nonlocal index_counter
        indices[v] = index_counter
        lowlinks[v] = index_counter
        index_counter += 1
        stack.append(v)
        on_stack.add(v)

        for w in sorted(adj.get(v, set())):
            if w not in indices:
                strongconnect(w)
                lowlinks[v] = min(lowlinks[v], lowlinks[w])
            elif w in on_stack:
                lowlinks[v] = min(lowlinks[v], indices[w])

        if lowlinks[v] == indices[v]:
            scc: list[str] = []
            while True:
                w = stack.pop()
                on_stack.discard(w)
                scc.append(w)
                if w == v:
                    break
            scc.sort()
            sccs.append(scc)

    for v in sorted(adj.keys()):
        if v not in indices:
            strongconnect(v)

    # SCC をソート（サイズ降順、内容で安定ソート）
    sccs.sort(key=lambda s: (-len(s), s[0] if s else ""))
    return sccs


def load_yaml_document(path: Path) -> dict:
    """正本YAMLを読み込む。壊れた正本でも棚卸しの他項目は出力する。"""
    try:
        with open(path, encoding="utf-8") as handle:
            document = yaml.safe_load(handle) or {}
    except (OSError, yaml.YAMLError):
        return {}
    return document if isinstance(document, dict) else {}


def canonical_line(path: Path, name: str) -> int:
    """正本内のSkill宣言行を返す。"""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return 0
    return _find_line_number(lines, f"- name: {name}")


def canonical_relations(document: dict, active_names: set[str]) -> dict[str, dict]:
    """skill-categories.yaml の依存・経路関係を正規化する。"""
    result: dict[str, dict] = {}
    for entry in document.get("skills", []):
        if not isinstance(entry, dict) or entry.get("name") not in active_names:
            continue
        name = entry["name"]
        depends = entry.get("depends_on", [])
        routes = entry.get("routes_to", [])
        conditions = entry.get("depends_on_edge_condition", {})
        result[name] = {
            "depends_on": sorted({value for value in depends if isinstance(value, str)} if isinstance(depends, list) else set()),
            "routes_to": sorted({value for value in routes if isinstance(value, str)} if isinstance(routes, list) else set()),
            "depends_on_edge_condition": conditions if isinstance(conditions, dict) else {},
            "category": entry.get("category"),
        }

    notes = document.get("dependency_notes", {})
    routes_notes = notes.get("routes_to_not_depends", {}) if isinstance(notes, dict) else {}
    for item in routes_notes.get("items", []) if isinstance(routes_notes, dict) else []:
        if not isinstance(item, dict) or item.get("from") not in active_names:
            continue
        source = item["from"]
        targets = item.get("to", [])
        if not isinstance(targets, list):
            targets = [targets]
        relation = item.get("relation", "mention")
        result.setdefault(source, {"depends_on": [], "routes_to": [], "depends_on_edge_condition": {}, "category": None})
        if relation == "routes_to":
            result[source]["routes_to"].extend(value for value in targets if isinstance(value, str))
    for relation in result.values():
        relation["routes_to"] = sorted(set(relation["routes_to"]))
    return result


def build_dependency_graph(skills_meta: list[dict], categories_document: dict, rules_document: dict) -> dict:
    """正本のdepends_onだけでグラフを構築する。自然言語抽出は循環判定に使わない。"""
    name_to_skill = {skill["name"]: skill for skill in skills_meta}
    active_names = set(name_to_skill)
    relations = canonical_relations(categories_document, active_names)
    canonical_skills = {entry.get("name"): entry for entry in categories_document.get("skills", []) if isinstance(entry, dict)}
    category_defs = {entry.get("id"): entry for entry in rules_document.get("categories", []) if isinstance(entry, dict)}

    graph: dict = {
        "schema_version": 2,
        "nodes": [],
        "edges": [],
        "other_references": [],
        "cycles": [],
        "reverse_dependency_candidates": [],
        "physical_path_refs": [],
        "canonical_source": ".rules/skill-categories.yaml",
        "layer_definition": [
            {"layer": category, "index": definition.get("order"), "skills": sorted(
                name for name, relation in relations.items() if relation.get("category") == category
            )}
            for category, definition in sorted(category_defs.items(), key=lambda item: (item[1].get("order", 999), item[0]))
        ],
    }

    for skill in skills_meta:
        graph["nodes"].append({
            "name": skill["name"],
            "current_path": skill["current_path"],
            "classification": skill["classification"],
            "line_count": skill["line_count"],
        })

    dep_edges: list[dict] = []
    for source in sorted(relations):
        relation = relations[source]
        for target in relation["depends_on"]:
            if target not in active_names:
                continue
            condition = relation["depends_on_edge_condition"].get(target, "unconditional")
            dep_edges.append({
                "from": source,
                "to": target,
                "relation": "depends_on",
                "edge_condition": condition,
                "source_file": ".rules/skill-categories.yaml",
                "source_line": canonical_line(CANONICAL_CATEGORIES, source),
            })
    graph["edges"] = dep_edges

    other_refs: dict[tuple[str, str, str], dict] = {}
    for source in sorted(relations):
        for target in relations[source]["routes_to"]:
            if target in active_names:
                other_refs[(source, target, "routes_to")] = {
                    "from": source, "to": target, "relation": "routes_to",
                    "source_file": ".rules/skill-categories.yaml",
                    "source_line": canonical_line(CANONICAL_CATEGORIES, source),
                }
    # 自動抽出は観測用。depends_on辺には昇格させない。
    for skill in skills_meta:
        for reference in skill.get("skill_references", []):
            target = reference["name"]
            if target not in active_names or reference["relation"] == "depends_on":
                continue
            key = (skill["name"], target, reference["relation"])
            other_refs.setdefault(key, {
                "from": skill["name"],
                "to": target,
                "relation": reference["relation"],
                "source_file": reference["source_file"],
                "source_line": reference["source_line"],
            })
    graph["other_references"] = sorted(other_refs.values(), key=lambda item: (item["from"], item["to"], item["relation"]))

    adj: dict[str, set[str]] = {name: set() for name in active_names}
    for edge in dep_edges:
        adj[edge["from"]].add(edge["to"])
    for component in tarjan_scc(adj):
        cyclic = len(component) > 1 or component[0] in adj.get(component[0], set())
        if not cyclic:
            continue
        members = set(component)
        start = component[0]
        path = [start]
        current = start
        seen = {start}
        while True:
            target = next((value for value in sorted(adj[current]) if value in members), None)
            if target is None:
                break
            path.append(target)
            if target == start:
                break
            if target in seen:
                break
            seen.add(target)
            current = target
        graph["cycles"].append({"members": component, "example_path": path})

    # category order を正本から読み、下位カテゴリから上位カテゴリへの辺だけを候補化する。
    for edge in dep_edges:
        source_category = category_defs.get(canonical_skills.get(edge["from"], {}).get("category"), {})
        target_category = category_defs.get(canonical_skills.get(edge["to"], {}).get("category"), {})
        source_order = source_category.get("order")
        target_order = target_category.get("order")
        if isinstance(source_order, int) and isinstance(target_order, int) and source_order > target_order:
            graph["reverse_dependency_candidates"].append({
                "from": edge["from"], "to": edge["to"],
                "from_layer": source_category.get("id"), "to_layer": target_category.get("id"),
                "reason": f"{source_category.get('id')} → {target_category.get('id')}: lower depends on higher category",
                "source_file": edge["source_file"], "source_line": edge["source_line"],
            })

    for skill in skills_meta:
        for path_ref in skill.get("path_references", []):
            graph["physical_path_refs"].append({
                "skill": skill["name"],
                "path": path_ref["path"],
                "type": path_ref["type"],
                "source_file": path_ref["source_file"],
                "source_line": path_ref["source_line"],
            })
    graph["physical_path_refs"].sort(key=lambda item: (item["skill"], item["path"], item["source_file"], item["source_line"]))
    return graph


# ====================================================================
# 所見分析
# ====================================================================

def analyze_findings(skills_meta: list[dict]) -> list[dict]:
    """自動検出可能な所見（肥大化・行数超過）を返す。"""
    findings = []
    stable_ids = {
        "bun-dependency-update": "F001",
        "herdr-agent-delegate": "F002",
        "herdr-github-pr-orchestrate": "F003",
        "npm-dependency-update": "F004",
        "uv-dependency-update": "F005",
    }

    for s in skills_meta:
        if s["line_count"] > 180:
            findings.append({
                "id": stable_ids.get(s["name"], f"F-LINE-{s['name']}"),
                "type": "oversize",
                "skill": s["name"],
                "line_count": s["line_count"],
                "reason": f"exceeds 180-line limit ({s['line_count']})",
                "recommendation": "split or shorten",
                "auto_detected": True,
            })
        elif s["line_count"] > 150:
            findings.append({
                "id": stable_ids.get(s["name"], f"F-LINE-{s['name']}"),
                "type": "near_limit",
                "skill": s["name"],
                "line_count": s["line_count"],
                "reason": f"approaches 180-line limit ({s['line_count']})",
                "recommendation": "monitor, consider reducing",
                "auto_detected": True,
            })

    return findings


def add_manual_findings(skills_meta: list[dict], auto_count: int) -> list[dict]:
    """人手判断による所見を追加する。"""
    name_map = {s["name"]: s for s in skills_meta}
    findings = []
    del auto_count

    # ── 重複責務候補 ──
    gwt = name_map.get("git-worktree-create")
    hwt = name_map.get("herdr-worktree-create")
    if gwt and hwt:
        findings.append({
            "id": "F006",
            "type": "duplication_candidate",
            "skills": [gwt["name"], hwt["name"]],
            "reason": "両者とも独立したworktree作成が責務。git-worktree-create は純粋なgit操作、herdr-worktree-create はHerdrコマンドによる作成。責務が重複しているが、利用コンテキストが異なるため統合には慎重な判断が必要。",
            "auto_detected": False,
            "recommendation": "統合候補。共通のworktree作成ロジックを抽出し、ラッパーとしてgit/herdr版を提供する構成を検討。",
        })

    gr = name_map.get("grilling")
    dpg = name_map.get("design-plan-grill")
    if gr and dpg:
        findings.append({
            "id": "F007",
            "type": "duplication_candidate",
            "skills": [gr["name"], dpg["name"]],
            "reason": "grilling は領域非依存の壁打ち、design-plan-grill は設計に特化した壁打ち。design-plan-grill は grilling の特殊化であり、grilling の SKILL.md で routes_to による条件付き委譲を指示。",
            "auto_detected": False,
            "recommendation": "Phase 4 で境界確認済み。grilling（領域非依存）と design-plan-grill（設計特化・docs-backed モード）の責務分離は適切。統合不要。",
        })

    gpo = name_map.get("github-pr-orchestrate")
    hgo = name_map.get("herdr-github-pr-orchestrate")
    if gpo and hgo:
        findings.append({
            "id": "F008",
            "type": "duplication_candidate",
            "skills": [gpo["name"], hgo["name"]],
            "reason": "両者ともPR作成の統括フロー。github-pr-orchestrate は非Herdr環境、herdr-github-pr-orchestrate はHerdr環境向け。herdr版はgithub版の共通スキルを参照している。",
            "auto_detected": False,
            "recommendation": "統合候補。共通フローを抽出し、Herdr/非Herdrの差異だけを切り替え可能にする。",
        })

    asd = name_map.get("agent-skill-design")
    asr = name_map.get("agent-skill-refine")
    if asd and asr:
        findings.append({
            "id": "F009",
            "type": "duplication_candidate",
            "skills": [asd["name"], asr["name"]],
            "reason": "agent-skill-design は新規作成・要件追加・全面再設計（挙動を変える）、agent-skill-refine は挙動を変えずに短文化・高密度化（表現を変える）。責務は明確に分離されている。",
            "auto_detected": False,
            "recommendation": "Phase 4 で境界確認済み。design は挙動変更、refine は意味保存改善で責務分離は適切。分割統合不要。",
        })

    # ── 肥大化候補 ──
    had = name_map.get("herdr-agent-delegate")
    if had and had["line_count"] > 170:
        findings.append({
            "id": "F010",
            "type": "oversize_detail",
            "skill": had["name"],
            "line_count": had["line_count"],
            "reason": f"{had['line_count']}行。Agent委譲の全工程（プリフライト、宛先解決、pane配置、依頼送信、結果回収）を1ファイルに収めており、責務が大きい。references/ は既に存在するが、SKILL.md 自体の構造を再検討する余地がある。",
            "recommendation": "工程ごとに references/ へ分割し、SKILL.md はルーティングと主要ルールのみに絞る。",
            "auto_detected": False,
        })

    if hgo and hgo["line_count"] > 150:
        findings.append({
            "id": "F011",
            "type": "near_limit_detail",
            "skill": hgo["name"],
            "line_count": hgo["line_count"],
            "reason": f"{hgo['line_count']}行。実装委譲からPR作成、レビュー、FB対応までの全工程をカバーしており、工程ごとの分岐条件も多い。references/ に実装委譲とレビューループの詳細は分離済み。",
            "recommendation": "モニタリング。180行を超える前に工程分岐の一部を references/ に移すことを検討。",
            "auto_detected": False,
        })

    car = name_map.get("cagent-agent-command-resolve")
    if car and car.get("has_scripts"):
        findings.append({
            "id": "F012",
            "type": "complexity",
            "skill": car["name"],
            "reason": "cagent の解決ロジックと Agent Command の生成を1スキルで扱っている。scripts/ に実装があり、SKILL.md はそれらの使い方を説明する構成。責務は明確だが、cagent 自体のバージョンアップに追従が必要。",
            "recommendation": "現状維持。scripts/ への分離は適切に行われている。",
            "auto_detected": False,
        })

    # ── 共通依存 ──
    deps_summary: dict[tuple[str, str], int] = {}
    for s in skills_meta:
        for dep in s.get("external_dependencies", []):
            key = (dep["name"], dep["type"])
            deps_summary[key] = deps_summary.get(key, 0) + 1

    for (dname, dtype), count in sorted(deps_summary.items(), key=lambda x: -x[1]):
        if count >= len(skills_meta) * 0.5:
            findings.append({
                "id": f"F-COMMON-{normalize_dep_name(dname).replace(' ', '-').upper()}",
                "type": "common_dependency",
                "dependency": dname,
                "type_class": dtype,
                "usage_count": count,
                "reason": f"全スキルの {count}/{len(skills_meta)} が依存。共通依存として暗黙的に扱うことを検討。",
                "auto_detected": False,
            })

    return findings


# ====================================================================
# メイン
# ====================================================================

def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Generate deterministic skill inventory YAML.")
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    args = parser.parse_args(argv)
    output_dir = args.output_dir if args.output_dir.is_absolute() else REPO_ROOT / args.output_dir
    print(f"Scanning {REPO_ROOT} ...")

    skill_files = find_skill_files()
    print(f"Found {len(skill_files)} SKILL.md files (distributable + maintenance)")

    readme_deps = parse_readme_deps()
    categories_document = load_yaml_document(CANONICAL_CATEGORIES)
    rules_document = load_yaml_document(CANONICAL_RULES)

    # 全スキル名を収集（依存抽出用）
    all_skill_names: set[str] = set()
    for sf in skill_files:
        with open(REPO_ROOT / sf) as f:
            content = f.read()
        fm = parse_frontmatter(content)
        name = fm.get("name", "")
        if name:
            all_skill_names.add(name)

    # 正本の依存関係を取得（自然言語ヒューリスティックの上書き用）
    canonical_rels = canonical_relations(categories_document, all_skill_names)
    # (source_name, target_name) → canonical_relation の上書きマップ
    relation_overrides: dict[tuple[str, str], str] = {}
    for src_name, rel in canonical_rels.items():
        for target in rel.get("depends_on", []):
            relation_overrides[(src_name, target)] = "depends_on"
        for target in rel.get("routes_to", []):
            if (src_name, target) in relation_overrides:
                continue  # depends_on が優先
            relation_overrides[(src_name, target)] = "routes_to"

    # 各スキルのメタデータを収集
    skills_meta: list[dict] = []
    for sf in skill_files:
        full_path = REPO_ROOT / sf
        skill_dir = full_path.parent

        # スキル配下の全ファイルを走査
        file_contents = scan_skill_files(skill_dir)

        # SKILL.md の内容
        skill_md = skill_dir / "SKILL.md"
        with open(skill_md) as f:
            skill_content = f.read()

        fm = parse_frontmatter(skill_content)
        name = fm.get("name", "")
        if not name:
            name = skill_dir.name

        classification = classify_skill(sf)
        responsibility = extract_responsibility(name, fm)
        line_count = count_lines(skill_md)
        subdirs = check_subdirs(skill_dir)
        skill_refs = extract_skill_references(file_contents, all_skill_names, name)
        # 正本の依存関係で自然言語ヒューリスティックの結果を上書き
        for ref in skill_refs:
            key = (name, ref["name"])
            if key in relation_overrides and ref["relation"] != relation_overrides[key]:
                ref["relation"] = relation_overrides[key]
        path_refs = extract_path_references(file_contents, all_skill_names)
        # 外部依存の直接宣言は README のみ。実装証拠は別フィールドに保存する。
        ext_deps = extract_external_deps(name, file_contents, readme_deps)
        ext_evidence = extract_external_dependency_evidence(file_contents)

        meta = {
            "name": name,
            "current_path": str(skill_dir.relative_to(REPO_ROOT)),
            "classification": classification,
            "responsibility": responsibility,
            "description": fm.get("description", ""),
            "line_count": line_count,
            "has_references": subdirs.get("references", False),
            "has_scripts": subdirs.get("scripts", False),
            "has_tests": subdirs.get("tests", False),
            "has_evaluation_samples": subdirs.get("evaluation-samples", False),
            "skill_references": skill_refs,
            "path_references": path_refs,
            "external_dependencies": ext_deps,
            "external_dependency_evidence": ext_evidence,
            "disposition": "keep",
            "findings": [],
        }
        skills_meta.append(meta)

    # 依存グラフ構築
    dep_graph = build_dependency_graph(skills_meta, categories_document, rules_document)

    # 所見の分析
    auto_findings = analyze_findings(skills_meta)
    auto_count = len(auto_findings)
    manual_findings = add_manual_findings(skills_meta, auto_count)
    all_findings = auto_findings + manual_findings

    # 各スキルの findings に該当する finding ID を設定
    finding_by_skill: dict[str, list[str]] = {}
    for finding in all_findings:
        if "skill" in finding:
            finding_by_skill.setdefault(finding["skill"], []).append(finding["id"])
        if "skills" in finding:
            for sname in finding["skills"]:
                finding_by_skill.setdefault(sname, []).append(finding["id"])

    for s in skills_meta:
        s["findings"] = sorted(finding_by_skill.get(s["name"], []))

    # 出力ディレクトリ作成
    output_dir.mkdir(parents=True, exist_ok=True)

    # スキルメタデータ出力
    skills_yaml = {
        "schema_version": 2,
        "generated_by": ".scripts/inventory.py",
        "scope": "distributable + .claude/skills/ (maintenance-only)",
        "total_count": len(skills_meta),
        "distributable_count": sum(1 for s in skills_meta if s["classification"] == "distributable"),
        "maintenance_count": sum(1 for s in skills_meta if s["classification"] == "maintenance"),
        "skills": skills_meta,
    }

    with open(output_dir / "skills.yaml", "w", encoding="utf-8") as f:
        yaml.dump(skills_yaml, f, allow_unicode=True, sort_keys=False, width=160)
    print(f"Wrote {output_dir / 'skills.yaml'}")

    # 依存グラフ出力
    with open(output_dir / "dependency-graph.yaml", "w", encoding="utf-8") as f:
        yaml.dump(dep_graph, f, allow_unicode=True, sort_keys=False, width=160)
    print(f"Wrote {output_dir / 'dependency-graph.yaml'}")

    # 所見出力
    findings_yaml = {
        "schema_version": 2,
        "generated_by": ".scripts/inventory.py",
        "total_findings": len(all_findings),
        "auto_detected": sum(1 for f in all_findings if f.get("auto_detected")),
        "manual": sum(1 for f in all_findings if not f.get("auto_detected")),
        "findings": all_findings,
    }
    with open(output_dir / "findings.yaml", "w", encoding="utf-8") as f:
        yaml.dump(findings_yaml, f, allow_unicode=True, sort_keys=False, width=160)
    print(f"Wrote {output_dir / 'findings.yaml'}")

    # サマリ出力
    summary = {
        "schema_version": 2,
        "generated_by": ".scripts/inventory.py",
        "scope": "distributable + .claude/skills/ (maintenance-only)",
        "total_skills": len(skills_meta),
        "distributable": sum(1 for s in skills_meta if s["classification"] == "distributable"),
        "maintenance": sum(1 for s in skills_meta if s["classification"] == "maintenance"),
        "total_dependency_edges": len(dep_graph["edges"]),
        "total_other_references": len(dep_graph["other_references"]),
        "cycles_found": len(dep_graph["cycles"]),
        "reverse_dependency_candidates": len(dep_graph["reverse_dependency_candidates"]),
        "physical_path_refs_found": len(dep_graph["physical_path_refs"]),
        "total_findings": len(all_findings),
        "oversize_skills": sum(1 for f in all_findings if f.get("type") == "oversize"),
        "near_limit_skills": sum(1 for f in all_findings if f.get("type") == "near_limit"),
        "duplication_candidates": sum(1 for f in all_findings if f.get("type") == "duplication_candidate"),
    }
    with open(output_dir / "summary.yaml", "w", encoding="utf-8") as f:
        yaml.dump(summary, f, allow_unicode=True, sort_keys=False, width=160)
    print(f"Wrote {output_dir / 'summary.yaml'}")

    # MD5ハッシュ計算（再現性検証用）
    print("\n=== MD5 Checksums ===")
    for yaml_file in sorted(output_dir.glob("*.yaml")):
        with open(yaml_file, "rb") as f:
            h = hashlib.md5(f.read()).hexdigest()
        print(f"  {yaml_file.name}: {h}")

    print("\n=== Summary ===")
    for k, v in summary.items():
        if k != "generated_by" and k != "scope":
            print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
