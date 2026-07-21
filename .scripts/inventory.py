#!/usr/bin/env python3
"""Phase 1: 全スキルの棚卸し — 配布対象 + .claude/skills/ 保守専用スキルを走査し、
責務・参照関係・外部依存・本文量・重複候補を YAML として inventory/ に出力する。"""

import hashlib
import os
import re
import sys
import yaml
from collections import OrderedDict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = REPO_ROOT / "inventory"

# ── スコープ定義 ──────────────────────────────────────────
EXCLUDE_DIRS = {".git", ".archive", ".codex", ".system", ".github", ".agents",
                "node_modules", "inventory", "__pycache__"}
MAINTENANCE_PREFIX = ".claude/skills"
SKILL_FILE_EXTS = {".md", ".py", ".sh", ".yaml", ".yml"}
SKILL_FILE_EXCLUDES = {"agents/openai.yaml"}  # agent設定は走査対象外

# ── 外部依存の種別 ────────────────────────────────────────
DEP_TYPES = ("required", "conditional", "optional", "fallback")

# ── 外部依存の別名正規化マップ（canonical → 別名集合） ───
DEP_ALIAS_MAP = {
    "python": {"python", "python3", "python 3", "python3 -c", "command -v python3"},
    "node": {"node", "node.js", "nodejs"},
    "gh": {"gh", "github cli", "gh cli"},
    "npx": {"npx", "node.js / npx"},
    "tailwind": {"tailwind", "tailwind css", "tailwindcss"},
    "playwright": {"playwright", "playwright cli"},
    "librsvg": {"librsvg"},
    "inkscape": {"inkscape"},
    "browser": {"browser"},
    "herdr": {"herdr", "herdr cli"},
    "cagent": {"cagent"},
    "bun": {"bun"},
    "npm": {"npm"},
    "jq": {"jq"},
    "git": {"git"},
    "uv": {"uv"},
    "rg": {"rg", "ripgrep"},
    "posix shell": {"posix shell", "posix"},
    "github api": {"github api", "github"},
    "agent cli": {"agent cli", "agent", "selected agent cli", "selected agent"},
    "web access": {"web access"},
    "coreutils": {"coreutils"},
    "github": {"github"},  # GitHub platform, distinct from gh CLI
}

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
    name = name.strip().lower().rstrip(".")
    name = re.sub(r"[`'\"]", "", name)
    for canonical, aliases in DEP_ALIAS_MAP.items():
        if name in aliases:
            return canonical
    return name


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
        first_sentence = re.split(r"[.。]", desc.replace("\n", " "))[0].strip()
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

    / 区切りを個別依存へ分割、別名正規化、種別注記を解析する。
    """
    readme_path = REPO_ROOT / "README.md"
    if not readme_path.exists():
        return {}

    with open(readme_path) as f:
        content = f.read()

    deps: dict[str, list[dict]] = {}
    for m in re.finditer(
        r"\[([^\]]+)\]\(([^)]+/SKILL\.md)\)\s*\|[^|]*\|(.+?)\|",
        content
    ):
        name = m.group(1)
        dep_text = m.group(3).strip()

        if dep_text in ("—", "—", ""):
            continue

        dep_list = []
        # まずカンマで大分類し、各パート内の / 区切りも展開する
        # 例: "Node.js / npm, `rg`, POSIX shell" → Node.js, npm, rg, POSIX shell
        # 例: "librsvg / Inkscape / browser (one required)" → librsvg, Inkscape, browser
        if "," in dep_text:
            raw_parts = [p.strip() for p in dep_text.split(",")]
        else:
            raw_parts = [dep_text.strip()]

        parts = []
        for rp in raw_parts:
            if not rp or rp in ("—", "—"):
                continue
            # / 区切りを含むが、カンマを含まない場合のみ分割（ネストした / は分割しない）
            if "/" in rp and "," not in rp:
                parts.extend(_split_alternatives(rp))
            else:
                parts.append(rp)

        for part in parts:
            part = part.strip()
            if not part or part in ("—", "—"):
                continue

            dep_type = "required"
            # 種別注記を抽出: (conditional), (one required), (fallback)
            type_match = re.search(r'\(([^)]+)\)', part)
            if type_match:
                anno = type_match.group(1).strip().lower()
                if anno in DEP_TYPES:
                    dep_type = anno
                elif anno in ("one required", "any required", "required one"):
                    dep_type = "optional"  # 代替手段なので個々は optional
                elif anno in ("fallback",):
                    dep_type = "fallback"
                part = part[:type_match.start()].strip() + " " + part[type_match.end():].strip()

            # バッククォート除去、正規化
            part = re.sub(r"[`]", "", part).strip()
            if not part:
                continue

            dep_list.append({
                "name": part,
                "type": dep_type,
                "source": "README",
            })

        deps[name] = dep_list

    return deps


def _split_alternatives(text: str) -> list[str]:
    """/ 区切りの代替構文を個別要素へ分割する。

    例:
      "librsvg / Inkscape / browser (one required)" → ["librsvg", "Inkscape", "browser (one required)"]
      "Node.js / npm" → ["Node.js", "npm"]
    """
    # 種別注記がある場合は本体と種別を分離
    type_anno = ""
    anno_match = re.search(r'\(([^)]+)\)$', text.strip())
    if anno_match:
        type_anno = anno_match.group(0)
        text = text[:anno_match.start()].strip()

    # / で分割
    alternatives = [a.strip() for a in text.split("/") if a.strip()]

    if len(alternatives) <= 1:
        return [text + " " + type_anno] if type_anno else [text]

    # (one required) などの注記は全代替要素に付与（個々が optional 扱い）
    result = []
    for alt in alternatives:
        if type_anno:
            result.append(alt + " " + type_anno)
        else:
            result.append(alt)
    return result


def extract_external_deps(skill_name: str,
                          file_contents: list[dict],
                          readme_deps: dict[str, list[dict]]) -> list[dict]:
    """外部依存を抽出。README の External Dependencies 列を優先し、スキル配下ファイルから補完。
    別名正規化により重複を排除する。
    """
    deps: list[dict] = []
    seen_canonical: set[str] = set()

    def add_dep(name: str, dtype: str, source: str) -> None:
        canonical = normalize_dep_name(name)
        if canonical not in seen_canonical:
            deps.append({
                "name": canonical,
                "type": dtype,
                "source": source,
            })
            seen_canonical.add(canonical)

    # README からの依存（優先）
    if skill_name in readme_deps:
        for rd in readme_deps[skill_name]:
            add_dep(rd["name"], rd["type"], "README")

    # スキル配下ファイルから補完
    for file_info in file_contents:
        content = file_info["content"]
        rel_path = file_info["rel_path"]

        # `command -v <cmd>` パターン
        for cmd_match in re.finditer(r"`command -v (\w+)`", content):
            add_dep(cmd_match.group(1), "required", f"{rel_path} (command -v)")

        # `which <cmd>` パターン
        for which_match in re.finditer(r"`which (\w+)`", content):
            add_dep(which_match.group(1), "required", f"{rel_path} (which)")

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
                add_dep(mod, "required", f"{rel_path} (code-import)")
            # JS/TS: import { ... } from '...' / import ... from '...'
            for imp in re.finditer(r"(?:^|\n)\s*import\s+(?:\{[^}]*\}|\*\s+as\s+\w+|\w+)\s+from\s+['\"]([^'\"]+)['\"]", code):
                mod = imp.group(1)
                if mod.startswith(".") or mod.startswith("node:"):
                    continue
                pkg = mod.split("/")[0] if mod.startswith("@") else mod.split("/")[0]
                add_dep(pkg, "required", f"{rel_path} (code-import)")

        # 実ファイルの import 文（.py ファイルの直接解析）
        if rel_path.endswith(".py"):
            for imp in re.finditer(r"(?:^|\n)(?:from|import)\s+([a-zA-Z_]\w+)", content):
                mod = imp.group(1)
                if mod.lower() in ("os", "sys", "json", "re", "yaml", "pathlib",
                                   "subprocess", "shutil", "typing", "io", "time",
                                   "hashlib", "collections", "dataclasses", "importlib",
                                   "__future__", "argparse", "logging", "tempfile"):
                    continue
                add_dep(mod, "required", f"{rel_path} (import)")

        # .sh ファイルのコマンド参照
        if rel_path.endswith(".sh"):
            for cmd in re.finditer(r"(?:^|\s)([a-zA-Z_][a-zA-Z0-9_-]{2,})\s", content):
                c = cmd.group(1).lower()
                if c in ("set", "if", "then", "else", "elif", "fi", "for", "while",
                         "do", "done", "in", "esac", "case", "echo", "exit", "cd",
                         "dir", "ls", "test", "unset", "export", "local", "readonly",
                         "shift", "return", "source", "trap", "wait", "exec", "eval"):
                    continue
                add_dep(c, "required", f"{rel_path} (shell-cmd)")

    return deps


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


def build_dependency_graph(skills_meta: list[dict]) -> dict:
    """依存グラフを構築し、循環参照・逆方向依存・物理パス参照を検出する。"""
    graph: dict = {
        "nodes": [],
        "edges": [],
        "other_references": [],
        "cycles": [],
        "reverse_dependency_candidates": [],
        "physical_path_refs": [],
        "layer_definition": [{"layer": name, "index": idx, "prefixes": sorted(
            [p for p, i in LAYER_DEF.items() if i == idx]
        )} for name, idx in [("primitive", 0), ("utility", 1), ("orchestration", 2)]],
    }

    name_to_skill: dict[str, dict] = {}
    for s in skills_meta:
        name = s["name"]
        node = {
            "name": name,
            "current_path": s["current_path"],
            "classification": s["classification"],
            "line_count": s["line_count"],
        }
        graph["nodes"].append(node)
        name_to_skill[name] = s

    # depends_on エッジのみを有向依存グラフに含める
    dep_edges: list[dict] = []
    other_refs: list[dict] = []

    for s in skills_meta:
        from_name = s["name"]
        for ref in s["skill_references"]:
            ref_name = ref["name"]
            if ref_name not in name_to_skill:
                continue
            edge = {
                "from": from_name,
                "to": ref_name,
                "relation": ref["relation"],
                "source_file": ref["source_file"],
                "source_line": ref["source_line"],
            }
            if ref["relation"] == "depends_on":
                dep_edges.append(edge)
            else:
                other_refs.append(edge)

    graph["edges"] = dep_edges
    graph["other_references"] = other_refs

    # SCC による循環参照の検出（depends_on エッジのみ）
    adj: dict[str, set[str]] = {}
    for edge in dep_edges:
        adj.setdefault(edge["from"], set()).add(edge["to"])
        adj.setdefault(edge["to"], set())

    sccs = tarjan_scc(adj)
    for scc in sccs:
        if len(scc) > 1:
            # 循環パスを構築（SCC内のノードから最小限の辺を抽出）
            cycle_members: set[str] = set(scc)
            sub_adj: dict[str, set[str]] = {v: adj.get(v, set()) & cycle_members for v in scc}
            # 最初のノードからDFSでサイクルパスを構築
            cycle_path: list[str] = []
            visited_cycle: set[str] = set()

            def find_cycle_path(v: str, start: str, path: list[str]) -> list[str] | None:
                if v in visited_cycle:
                    return None
                visited_cycle.add(v)
                new_path = path + [v]
                for w in sorted(sub_adj.get(v, set())):
                    if w == start and len(new_path) > 1:
                        return new_path + [w]
                    if w not in visited_cycle:
                        result = find_cycle_path(w, start, new_path)
                        if result:
                            return result
                visited_cycle.discard(v)
                return None

            cycle_path = find_cycle_path(scc[0], scc[0], []) or scc
            if len(cycle_path) > 1:
                graph["cycles"].append({
                    "members": scc,
                    "example_path": cycle_path,
                })

    # 逆方向依存候補（明示的レイヤー定義に基づく）
    for edge in dep_edges:
        from_prefix = edge["from"].split("-")[0]
        to_prefix = edge["to"].split("-")[0]
        from_layer_idx, from_layer_name = get_layer(from_prefix)
        to_layer_idx, to_layer_name = get_layer(to_prefix)

        # 上位レイヤーから下位レイヤーへの参照は、アーキテクチャ上期待される方向
        # 下位→上位の depends_on は潜在的なレイヤー違反候補
        if from_layer_idx >= 0 and to_layer_idx >= 0 and from_layer_idx < to_layer_idx:
            graph["reverse_dependency_candidates"].append({
                "from": edge["from"],
                "to": edge["to"],
                "from_layer": from_layer_name,
                "to_layer": to_layer_name,
                "reason": f"{from_prefix}({from_layer_name}) → {to_prefix}({to_layer_name}): lower depends on higher layer",
                "source_file": edge["source_file"],
                "source_line": edge["source_line"],
            })

    # 物理パス参照の収集
    for s in skills_meta:
        for path_ref in s.get("path_references", []):
            graph["physical_path_refs"].append({
                "skill": s["name"],
                "path": path_ref["path"],
                "type": path_ref["type"],
                "source_file": path_ref["source_file"],
                "source_line": path_ref["source_line"],
            })

    return graph


# ====================================================================
# 所見分析
# ====================================================================

def analyze_findings(skills_meta: list[dict]) -> list[dict]:
    """自動検出可能な所見（肥大化・行数超過）を返す。"""
    findings = []
    fid = 0

    for s in skills_meta:
        if s["line_count"] > 180:
            fid += 1
            findings.append({
                "id": f"F{fid:03d}",
                "type": "oversize",
                "skill": s["name"],
                "line_count": s["line_count"],
                "reason": f"exceeds 180-line limit ({s['line_count']})",
                "recommendation": "split or shorten",
                "auto_detected": True,
            })
        elif s["line_count"] > 150:
            fid += 1
            findings.append({
                "id": f"F{fid:03d}",
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
    fid = auto_count

    def fid_next():
        nonlocal fid
        fid += 1
        return f"F{fid:03d}"

    # ── 重複責務候補 ──
    gwt = name_map.get("git-worktree-create")
    hwt = name_map.get("herdr-worktree-create")
    if gwt and hwt:
        findings.append({
            "id": fid_next(),
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
            "id": fid_next(),
            "type": "duplication_candidate",
            "skills": [gr["name"], dpg["name"]],
            "reason": "grilling は領域非依存の壁打ち、design-plan-grill は設計に特化した壁打ち。責務が重複しており、design-plan-grill は grilling の特殊化。grilling の SKILL.md 内でも design-plan-grill への委譲を指示している。",
            "auto_detected": False,
            "recommendation": "統合候補。design-plan-grill を grilling のサブモードとして統合するか、grilling を design-plan-grill に吸収。",
        })

    gpo = name_map.get("github-pr-orchestrate")
    hgo = name_map.get("herdr-github-pr-orchestrate")
    if gpo and hgo:
        findings.append({
            "id": fid_next(),
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
            "id": fid_next(),
            "type": "duplication_candidate",
            "skills": [asd["name"], asr["name"]],
            "reason": "agent-skill-design は新規作成・要件追加・全面再設計、agent-skill-refine は挙動を変えずに短文化・高密度化。責務は明確に分離されているが、密接に関連しており、参照関係も強い。",
            "auto_detected": False,
            "recommendation": "分割統合は不要。責務境界が明確で適切に分離されている。",
        })

    # ── 肥大化候補 ──
    had = name_map.get("herdr-agent-delegate")
    if had and had["line_count"] > 170:
        findings.append({
            "id": fid_next(),
            "type": "oversize_detail",
            "skill": had["name"],
            "line_count": had["line_count"],
            "reason": f"{had['line_count']}行。Agent委譲の全工程（プリフライト、宛先解決、pane配置、依頼送信、結果回収）を1ファイルに収めており、責務が大きい。references/ は既に存在するが、SKILL.md 自体の構造を再検討する余地がある。",
            "recommendation": "工程ごとに references/ へ分割し、SKILL.md はルーティングと主要ルールのみに絞る。",
            "auto_detected": False,
        })

    if hgo and hgo["line_count"] > 150:
        findings.append({
            "id": fid_next(),
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
            "id": fid_next(),
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
                "id": fid_next(),
                "type": "common_dependency",
                "dependency": dname,
                "type_class": dtype,
                "usage_count": count,
                "reason": f"全スキルの {count}/{len(skills_meta)} が依存。共通依存として暗黙的に扱うことを検討。",
                "auto_detected": False,
            })

    return (findings, fid)


# ====================================================================
# メイン
# ====================================================================

def main() -> None:
    print(f"Scanning {REPO_ROOT} ...")

    skill_files = find_skill_files()
    print(f"Found {len(skill_files)} SKILL.md files (distributable + maintenance)")

    readme_deps = parse_readme_deps()

    # 全スキル名を収集（依存抽出用）
    all_skill_names: set[str] = set()
    for sf in skill_files:
        with open(REPO_ROOT / sf) as f:
            content = f.read()
        fm = parse_frontmatter(content)
        name = fm.get("name", "")
        if name:
            all_skill_names.add(name)

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
        path_refs = extract_path_references(file_contents, all_skill_names)
        ext_deps = extract_external_deps(name, file_contents, readme_deps)

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
            "disposition": "keep",
            "findings": [],
        }
        skills_meta.append(meta)

    # 依存グラフ構築
    dep_graph = build_dependency_graph(skills_meta)

    # 所見の分析
    auto_findings = analyze_findings(skills_meta)
    auto_count = len(auto_findings)
    manual_findings, _ = add_manual_findings(skills_meta, auto_count)
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
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # スキルメタデータ出力
    skills_yaml = {
        "generated_by": ".scripts/inventory.py",
        "scope": "distributable + .claude/skills/ (maintenance-only)",
        "total_count": len(skills_meta),
        "distributable_count": sum(1 for s in skills_meta if s["classification"] == "distributable"),
        "maintenance_count": sum(1 for s in skills_meta if s["classification"] == "maintenance"),
        "skills": skills_meta,
    }

    with open(OUTPUT_DIR / "skills.yaml", "w") as f:
        yaml.dump(skills_yaml, f, allow_unicode=True, sort_keys=False, width=160)
    print(f"Wrote {OUTPUT_DIR / 'skills.yaml'}")

    # 依存グラフ出力
    with open(OUTPUT_DIR / "dependency-graph.yaml", "w") as f:
        yaml.dump(dep_graph, f, allow_unicode=True, sort_keys=False, width=160)
    print(f"Wrote {OUTPUT_DIR / 'dependency-graph.yaml'}")

    # 所見出力
    findings_yaml = {
        "generated_by": ".scripts/inventory.py",
        "total_findings": len(all_findings),
        "auto_detected": sum(1 for f in all_findings if f.get("auto_detected")),
        "manual": sum(1 for f in all_findings if not f.get("auto_detected")),
        "findings": all_findings,
    }
    with open(OUTPUT_DIR / "findings.yaml", "w") as f:
        yaml.dump(findings_yaml, f, allow_unicode=True, sort_keys=False, width=160)
    print(f"Wrote {OUTPUT_DIR / 'findings.yaml'}")

    # サマリ出力
    summary = {
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
    with open(OUTPUT_DIR / "summary.yaml", "w") as f:
        yaml.dump(summary, f, allow_unicode=True, sort_keys=False, width=160)
    print(f"Wrote {OUTPUT_DIR / 'summary.yaml'}")

    # MD5ハッシュ計算（再現性検証用）
    print("\n=== MD5 Checksums ===")
    for yaml_file in sorted(OUTPUT_DIR.glob("*.yaml")):
        with open(yaml_file, "rb") as f:
            h = hashlib.md5(f.read()).hexdigest()
        print(f"  {yaml_file.name}: {h}")

    print("\n=== Summary ===")
    for k, v in summary.items():
        if k != "generated_by" and k != "scope":
            print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
